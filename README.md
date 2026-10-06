# AI\_Speaker 프로젝트

음성 인공지능 스피커와 **웹캠 기반 낙상 감지** 기능을 한 자리에서 시험해 볼 수 있는 파이썬 데모입니다.

* **voice\_module.py**  : Google Cloud STT/TTS·Gemini·Programmable Search Engine를 이용한 한국어 음성 어시스턴트 (웨이크 워드 "실비야")
* **fall\_module.py**   : TensorFlow‑Lite MoveNet Lightning 모델로 **웹캠 영상**을 실시간 분석하여 낙상을 탐지, FCM(푸시) 알림 전송
* **fcm\_module.py**    : Firebase Cloud Messaging 헬퍼 (`fallAlerts` 토픽으로 알림 전송)
* **main.py**          : 음성 어시스턴트(백그라운드 스레드)와 낙상 감지(메인 스레드)를 **동시에** 실행하는 런처 (각 모듈을 따로 실행해도 무방)
* **android\_app/**     : FCM 낙상 알림을 받는 안드로이드 클라이언트 예시 코드 안내 ([android_app/README.md](android_app/README.md))

> 웹캠(노트북 내장 카메라 등)만 연결되어 있으면 바로 낙상 감지를 시도할 수 있습니다.

##  

## 1. 빠른 시작

```bash
# 저장소 클론 & 가상환경
$ git clone https://github.com/Lee35678/AI_Speaker_new.git
$ cd AI_Speaker_new
$ python -m venv .venv && .venv\Scripts\activate   # Windows 예시

# 필수 패키지 설치
(.venv)$ pip install -r requirements.txt

# MoveNet TFLite 모델은 저장소에 movenet_lightning.tflite로 포함되어 있습니다.
# 다시 받아야 할 때만 아래 명령 사용
(.venv)$ curl -L -o movenet_lightning.tflite \
  https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4?lite-format=tflite

# 서비스 계정 키 등 환경 변수 설정 (아래 2‑B ~ 2‑E 참고)

# 음성 어시스턴트 + 낙상 감지 동시 실행
(.venv)$ python main.py

# 또는 따로 실행
(.venv)$ python voice_module.py   # AI 스피커
(.venv)$ python fall_module.py    # 낙상 감지 (웹캠 필요)
```

##  

## 2. 사전 준비

### 2‑A. 파이썬 의존성

`requirements.txt`에 들어 있는 패키지:

```
google-cloud-speech==2.32.0
google-cloud-texttospeech>=2.20.0
google-generativeai>=0.5.3
opencv-python>=4.9.0.80
numpy>=1.26
tensorflow==2.16.1      # TFLite Interpreter 포함. 라즈베리 파이 등에서는 tflite-runtime 사용
pygame>=2.3.0
requests>=2.31.0
pyaudio>=0.2.14
```

코드에서 선택적으로 쓰는 패키지(설치되어 있으면 자동 사용, `requirements.txt`에는 없음):

```
gTTS          # Cloud TTS 오류·미설정 시 폴백
webrtcvad     # 음성 구간 감지(VAD). 없으면 RMS 음량 기준으로 감지
pvporcupine   # 오프라인 웨이크워드 감지 훅 (USE_KWS)
```

> **Windows** 에서 PyAudio는 미리 wheel 파일을 받아 두면 설치가 수월합니다.

### 2‑B. Google Cloud STT/TTS

1. **서비스 계정** → 역할에 *Cloud Speech Client*, *Cloud Text‑to‑Speech Client* 부여
2. JSON 키를 내려받아 예) `C:\Keys\gcloud-ai-speaker.json`
3. 환경 변수 지정

   ```powershell
   setx GOOGLE_APPLICATION_CREDENTIALS C:\Keys\gcloud-ai-speaker.json
   ```

### 2‑C. Gemini API (Generative AI)

1. [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 에서 **API Key** 발급
2. 환경 변수

   ```powershell
   setx GOOGLE_API_KEY_PALM <YOUR_GEMINI_KEY>
   ```

### 2‑D. Programmable Search Engine(CSE)

1. [https://programmablesearchengine.google.com](https://programmablesearchengine.google.com) → *Create Search engine* → **Search the entire web**
2. API Key 발급 ([https://developers.google.com/custom-search/v1/overview](https://developers.google.com/custom-search/v1/overview))
3. 환경 변수

   ```powershell
   setx GOOGLE_API_KEY_SEARCH <YOUR_CSE_API_KEY>
   setx GOOGLE_SEARCH_ENGINE_ID <YOUR_CSE_ID>
   ```

### 2‑E. Firebase Cloud Messaging(선택)

1. Firebase Console → 새 프로젝트 → Cloud Messaging 탭
2. **서버 Key**(Legacy Server Key) 저장 → `FCM_SERVER_KEY` 환경 변수
3. 알림은 개별 기기 토큰이 아니라 `fallAlerts` **토픽**으로 전송됩니다. 받는 앱이 이 토픽을 구독해야 합니다 ([android_app/README.md](android_app/README.md) 참고).

##  

## 3. 음성 어시스턴트 상세

| 기능     | 설명                                                 |
| ------ | -------------------------------------------------- |
| 웨이크 워드 | "실비야", "헤이 실비" (인식 오차를 고려해 "실비아", "실비", "비아"도 허용) – 호출 시 삐링 효과음 후 명령 대기 |
| STT    | Google Cloud Speech‑to‑Text (`command_and_search` 모델, 웨이크 워드 문구 가중치 적용, webrtc‑VAD or RMS 감지) |
| TTS    | 기본 Cloud TTS, 오류·오프라인 시 gTTS 폴백                    |
| RAG    | 질문 → Google CSE 검색(상위 5개) → Gemini(`gemini-2.5-pro-preview-05-06`)로 종합 답변 |
| 특수 명령  | "현재 시간", "종료" 등 로컬 처리                              |

##  

## 4. 낙상 감지 모듈(fall\_module.py)

| 항목    | 값                                               |
| ----- | ----------------------------------------------- |
| 모델    | **MoveNet Lightning TFLite** (단일 사람, 192×192)   |
| 추론 간격 | `INFER_EVERY=2` → 약 15 FPS 웹캠에서 7‑8 FPS 추론      |
| 1단계: 의심 | 평균 신뢰도 > `MIN_SCORE`(0.3) 이고, 코 y 낙폭 `dy` > 0.08, 어깨‑엉덩이 각도 변화 `da` > 35° 이면 낙상 의심 |
| 2단계: 확인 | 의심 후 `CONFIRM_FRAMES`(4) 추론 프레임 안에 상체가 수평에 가깝고(`THR_HORIZONTAL`=40°) 코가 엉덩이보다 아래에 있으면 낙상 확정 |
| 알림    | `send_fcm_alert(title, body)` 호출로 FCM 푸시, `ALERT_INTERVAL`(5초) 안에는 중복 알림 안 함 |
| 종료    | 영상 창에서 `Esc`                                   |

##  

## 5. 폴더 구조

```
AI_Speaker_new/
├── main.py                    # 음성 + 낙상 감지 동시 실행 런처
├── voice_module.py            # 음성 어시스턴트 (Cloud STT/TTS, CSE + Gemini RAG)
├── fall_module.py             # MoveNet 낙상 감지
├── fcm_module.py              # FCM 알림 전송
├── movenet_lightning.tflite   # MoveNet Lightning 모델 (약 4.7MB)
├── Pling Sound.wav            # 웨이크 워드 효과음
├── requirements.txt
└── android_app/README.md      # 안드로이드 FCM 수신 앱 예시
```

##  

## 6. 참고 (코드상 한계)

* `fcm_module.py`는 FCM **레거시 HTTP API**(`fcm.googleapis.com/fcm/send`, 서버 키 방식)를 씁니다. Google이 레거시 API 지원을 종료했으므로, 지금 알림을 보내려면 HTTP v1 API(서비스 계정 OAuth)로 바꿔야 합니다.
* Cloud STT 인증(`GOOGLE_APPLICATION_CREDENTIALS`)이 없으면 음성 인식이 빈 문자열을 반환해 음성 어시스턴트가 반응하지 않습니다. STT는 폴백이 없습니다.
* 웨이크 워드를 부른 뒤 **다음 한 문장**만 명령으로 처리하고 다시 대기합니다.
* `MODEL_NAME`이 프리뷰 모델(`gemini-2.5-pro-preview-05-06`)이라 더 이상 제공되지 않으면 바꿔야 합니다.
* `fall_module.py`는 카메라를 `cv2.CAP_DSHOW`(Windows DirectShow)로 엽니다. 다른 OS에서는 이 인자를 빼야 할 수 있습니다.
* 낙상 판단은 MoveNet 키포인트에 대한 규칙(임계값) 기반이며, 단일 인물만 추적합니다.

##  

## 7. 라이선스

MIT License – 자유롭게 사용/수정하시고, 개선점을 공유해 주세요.

---

**문의·기여** : Pull Request나 Issue로 편하게 남겨 주세요. 🙌
