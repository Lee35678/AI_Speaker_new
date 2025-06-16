"""
fall_module.py
───────────────────────────────────────────────────────────────
TensorFlow-Lite MoveNet 기반 낙상 감지
 - 입력 dtype 자동 처리, 출력 shape 안전 변환
 - 카메라 버퍼 1프레임 제한, 추론 프레임 간격(INFER_EVERY)
 - 낙상 감지 후 쿨다운 + 모든 예외 캐치 → 루프 계속 유지
Author : Gizmo 2025-05-13
───────────────────────────────────────────────────────────────
"""
import cv2, time, numpy as np, tensorflow as tf
from collections import deque
from fcm_module import send_fcm_alert

# ────────────────────────────────
#  파라미터
# ────────────────────────────────
HIST_LEN        = 10          # dy·angle 이동 평균 창
THR_NOSE_DROP   = 0.08        # 낙폭(정규화 y) 임계
THR_ANGLE       = 35          # 상체 각도 임계
MIN_SCORE       = 0.3         # 평균 신뢰도 임계
ALERT_INTERVAL  = 5           # 알림 최소 간격(초)
INFER_EVERY     = 2           # N 프레임마다 추론

# 개선된 낙상 판단을 위한 추가 파라미터
CONFIRM_FRAMES  = 4           # 낙상 의심 후 확인할 프레임 수
THR_HORIZONTAL  = 40          # 상체가 수평에 가까운지 판단할 각도

# ────────────────────────────────
#  MoveNet 로드
# ────────────────────────────────
interpreter = tf.lite.Interpreter(model_path="movenet_lightning.tflite")
interpreter.allocate_tensors()
in_det  = interpreter.get_input_details()
out_det = interpreter.get_output_details()
in_dtype = in_det[0]["dtype"]

NOSE, L_SH, R_SH, L_HIP, R_HIP = 0, 5, 6, 11, 12

def angle(p1, p2):
    return abs(np.degrees(np.arctan2(p2[1]-p1[1], p2[0]-p1[0])))

# ────────────────────────────────
#  메인 실행 함수
# ────────────────────────────────
def run():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise IOError("카메라를 열 수 없습니다.")
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    hist = deque(maxlen=HIST_LEN)
    last_alert = 0.0
    frame_idx  = 0
    suspect_frames = 0

    print("=== 낙상 감지 모듈 시작 (Esc: 종료) ===")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            h, w = frame.shape[:2]

            if frame_idx % INFER_EVERY == 0:
                # ── 전처리
                img = cv2.resize(frame, (192, 192))
                if in_dtype == np.float32:
                    inp = (img.astype(np.float32) / 255.0)[None]
                else:
                    inp = img.astype(np.uint8)[None]

                # ── 추론
                interpreter.set_tensor(in_det[0]["index"], inp)
                interpreter.invoke()
                kpts = interpreter.get_tensor(out_det[0]["index"]).reshape(-1, 3)
                mean_sc = kpts[:, 2].mean()

                # ── 지표 계산
                nose_y = kpts[NOSE][0]
                torso_a = (angle(kpts[L_SH], kpts[L_HIP]) +
                           angle(kpts[R_SH], kpts[R_HIP])) / 2
                hist.append((nose_y, torso_a))

                dy = da = 0
                if len(hist) > 1:
                    dy = hist[-2][0] - hist[-1][0]
                    da = abs(hist[-1][1] - hist[-2][1])

                    hip_y = (kpts[L_HIP][0] + kpts[R_HIP][0]) / 2
                    horizontal = min(torso_a, 180 - torso_a) < THR_HORIZONTAL

                    if suspect_frames > 0:
                        suspect_frames -= 1
                        if (horizontal and nose_y > hip_y and
                            time.time() - last_alert > ALERT_INTERVAL):
                            print(f"!!! 낙상 감지 dy={dy:.3f} da={da:.1f}")
                            try:
                                send_fcm_alert("낙상 감지",
                                               "쓰러짐이 감지되었습니다!")
                            except Exception as e:
                                print(f"[경고] FCM 전송 실패: {e}")
                            last_alert = time.time()
                            suspect_frames = 0
                    else:
                        if (mean_sc > MIN_SCORE and
                            dy > THR_NOSE_DROP and
                            da > THR_ANGLE):
                            suspect_frames = CONFIRM_FRAMES

                # ── 스켈레톤 & 오버레이
                for y_norm, x_norm, sc in kpts:
                    if sc > 0.2:
                        cv2.circle(frame,
                                   (int(x_norm * w), int(y_norm * h)),
                                   3, (0, 255, 0), -1)
                cv2.putText(frame, f"dy={dy:.3f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(frame, f"a={torso_a:.1f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            frame_idx += 1
            # ── 화면 표시
            cv2.imshow("Fall Detection", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except Exception as e:
        print(f"[오류] 낙상 모듈 예외: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("낙상 감지 모듈 종료")

# 모듈 단독 실행 시
if __name__ == "__main__":
    run()
