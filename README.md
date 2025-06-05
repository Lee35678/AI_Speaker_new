# AI\_Speaker 프로젝트

음성 인공지능 스피커와 **웹캠 기반 낙상 감지** 기능을 한 자리에서 시험해 볼 수 있는 파이썬 데모입니다.

* **voice\_module.py**  : Google Cloud STT/TTS·Gemini·Programmable Search Engine를 이용한 한국어 음성 어시스턴트 (웨이크 워드 "실비야")
* **fall\_module.py**   : TensorFlow‑Lite MoveNet Lightning 모델로 **웹캠 영상**을 실시간 분석하여 낙상을 탐지, FCM(푸시) 알림 전송
* **fcm\_module.py**    : Firebase Cloud Messaging 헬퍼
* **main.py**          : 두 모듈을 한 프로그램에서 선택 실행할 수 있는 런처 (원한다면 따로 실행해도 무방)

> ⓘ 초경량 운영을 위해 현재 버전은 **LD500 LiDAR** 센서를 사용하지 않습니다.
> 웹캠(노트북 내장 카메라 등)만 연결되어 있으면 바로 낙상 감지를 시도할 수 있습니다.

##  

## 1. 빠른 시작

```bash
# 저장소 클론 & 가상환경
$ git clone https://github.com/your-id/AI_Speaker.git
$ cd AI_Speaker
$ python -m venv .venv && .venv\Scripts\activate   # Windows 예시

# 필수 패키지 설치
(.venv)$ pip install -r requirements.txt

# MoveNet TFLite 모델 다운로드 (1회)
(.venv)$ curl -L -o movenet_lightning.tflite \
  https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4?lite-format=tflite

# 서비스 계정 키 등 환경 변수 설정 (아래 2‑B, 2‑C 참고)

# AI 스피커 실행
(.venv)$ python voice_module.py

# 낙상 감지 실행 (웹캠 필요)
(.venv)$ python fall_module.py
```

##  

## 2. 사전 준비

### 2‑A. 파이썬 의존성

`requirements.txt` 예시(버전은 변경 가능)

```
pygame
pyaudio
opencv-python
numpy
tensorflow==2.15.0   # TFLite Interpreter 포함
webrtcvad            # (선택) 음성 Activity Detection
requests
google-generativeai
google-cloud-speech
google-cloud-texttospeech
PyFCM                # FCM 알림 전송용
gTTS                 # Cloud TTS 오류 시 폴백
```

> **Windows** 에서 PyAudio는 미리 wheel 파일을 받아 두면 설치가 수월합니다.

### 2‑B. Google Cloud STT/TTS

1. **서비스 계정** → 역할에 *Cloud Speech Client*, *Cloud Text‑to‑Speech Client* 부여
2. JSON 키를 내려받아 예) `C:\Keys\gcloud-ai-speaker.json`
3. 환경 변수 지정

   ```powershell
   setx GOOGLE_APPLICATION_CREDENTIALS C:\Keys\gcloud-ai-speaker.json
   ```

### 2‑C. Gemini API (Generative AI)

1. [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 에서 **API Key** 발급
2. 환경 변수

   ```powershell
   setx GOOGLE_API_KEY_PALM <YOUR_GEMINI_KEY>
   ```

### 2‑D. Programmable Search Engine(CSE)

1. [https://programmablesearchengine.google.com](https://programmablesearchengine.google.com) → *Create Search engine* → **Search the entire web**
2. API Key 발급 ([https://developers.google.com/custom-search/v1/overview](https://developers.google.com/custom-search/v1/overview))
3. 환경 변수

   ```powershell
   setx GOOGLE_API_KEY_SEARCH <YOUR_CSE_API_KEY>
   setx GOOGLE_SEARCH_ENGINE_ID <YOUR_CSE_ID>
   ```

### 2‑E. Firebase Cloud Messaging(선택)

1. Firebase Console → 새 프로젝트 → Cloud Messaging 탭
2. **서버 Key**(또는 Legacy Server Key) 저장 → `FCM_SERVER_KEY` 환경 변수
3. 안드로이드/iOS 앱 토큰을 `fcm_module.py` 또는 DB에 등록

##  

## 3. 음성 어시스턴트 상세

| 기능     | 설명                                                 |
| ------ | -------------------------------------------------- |
| 웨이크 워드 | "실비야", "헤이 실비" – 호출 시 삐링 효과음 후 명령 대기             |
| STT    | Google Cloud Speech‑to‑Text (webrtc‑VAD or RMS 감지) |
| TTS    | 기본 Cloud TTS, 오류·오프라인 시 gTTS 폴백                    |
| RAG    | 질문 → Google CSE 검색(상위 5개) → Gemini로 종합 답변          |
| 특수 명령  | "현재 시간", "종료" 등 로컬 처리                              |

##  

## 4. 낙상 감지 모듈(fall\_module.py)

| 항목    | 값                                               |
| ----- | ----------------------------------------------- |
| 모델    | **MoveNet Lightning TFLite** (단일 사람, 192×192)   |
| 추론 간격 | `INFER_EVERY=2` → 약 15 FPS 웹캠에서 7‑8 FPS 추론      |
| 판단 로직 | 코 y 낙폭 `dy` + 어깨‑엉덩이 각도 `da` 이동 평균이 임계치를 넘으면 낙상 |
| 알림    | `send_fcm_alert(title, body)` 호출로 FCM 푸시        |


##  

## 5. 라이선스

MIT License – 자유롭게 사용/수정하시고, 개선점을 공유해 주세요.

---

**문의·기여** : Pull Request나 Issue로 편하게 남겨 주세요. 🙌
