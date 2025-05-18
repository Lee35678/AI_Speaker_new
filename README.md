# AI\_Speaker 프로젝트

파이썬으로 구현한 **음성 기반 AI 스피커 & 낙상 감지 데모**입니다. Google Cloud STT/TTS, Gemini(Generative AI), Programmable Search Engine를 활용해 자연어 질의에 답하고, LiDAR LD500 데이터를 바탕으로 낙상 여부를 식별합니다.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue"/>
  <img src="https://img.shields.io/badge/license-MIT-green"/>
</p>

---

## 디렉터리 구조

```text
AI_Speaker/
├─ main.py              # 데모 진입점 (스피커 + 낙상 모드 스위치)
├─ voice_module.py      # 웨이크 워드 기반 AI 스피커
├─ fall_module.py       # LD500 LiDAR 실시간 낙상 감지
├─ fcm_module.py        # Firebase Cloud Messaging 경보 전송
├─ requirements.txt     # 의존성 목록
├─ Pling Sound.wav      # 웨이크‑워드 확인 효과음
└─ README.md            # 사용 설명서
```

---

## 설치 방법

### 1) 클론 & 가상환경

```bash
$ git clone https://github.com/YourName/AI_Speaker.git
$ cd AI_Speaker
$ python -m venv .venv
$ source .venv/bin/activate  # Windows → .venv\Scripts\activate
```

### 2) 필수 라이브러리

```bash
(.venv) $ pip install -r requirements.txt
```

> **선택** : 더 정확한 음성 활성화를 원한다면 → `pip install webrtcvad`

#### requirements.txt (발췌)

```text
google-cloud-speech>=2.25.0
google-cloud-texttospeech>=2.15.0
google-generativeai>=0.4.0
pygame>=2.6.0
pyaudio>=0.2.14
requests>=2.31
```

---

## 환경 변수 설정 (필수)

| 변수                               | 설명                                | 예시                        |
| -------------------------------- | --------------------------------- | ------------------------- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Cloud STT/TTS용 서비스 계정 JSON 경로     | `C:\Keys\ai-speaker.json` |
| `GOOGLE_API_KEY_SEARCH`          | Custom Search JSON API Key        | `AIza...`                 |
| `GOOGLE_SEARCH_ENGINE_ID`        | Programmable Search Engine ID(CX) | `83c22d5ab755e4657`       |
| `GOOGLE_API_KEY_PALM`            | Gemini (PaLM 2) API Key           | `AIza...`                 |

Windows PowerShell 예시:

```powershell
$Env:GOOGLE_APPLICATION_CREDENTIALS="C:\Keys\ai-speaker.json"
$Env:GOOGLE_API_KEY_SEARCH="AIza..."
$Env:GOOGLE_SEARCH_ENGINE_ID="83c22d5ab755e4657"
$Env:GOOGLE_API_KEY_PALM="AIza..."
```

---

## Google Cloud & API 설정 가이드

1. **Google Cloud Project 생성** 후 ‘Speech‑to‑Text’, ‘Text‑to‑Speech’ API 활성화
2. **IAM & 관리 → 서비스 계정** → 새 계정 생성 → 키 (JSON) 다운로드
3. **Programmable Search Engine** ([https://programmablesearchengine.google.com](https://programmablesearchengine.google.com))

   * *Search entire web* 활성화 → 배포 탭에서 **Search engine ID(CX)** 복사
4. **Custom Search JSON API** 활성화 → API Key 발급
5. **Google AI Studio** ([https://aistudio.google.com](https://aistudio.google.com)) → API Key 발급 (Gemini Pro 모델)
6. 위 네 값과 JSON 파일 경로를 모두 환경 변수에 등록

---

## 실행

### 1) AI 스피커만 실행

```bash
(.venv) $ python voice_module.py
```

* **웨이크 워드** : "스피커야", "헤이 스피커"
* 예) “스피커야, 오늘 서울 날씨 알려 줘.”

### 2) 낙상 감지

```bash
(.venv) $ python fall_module.py
```

* LD500 LiDAR 센서를 USB(UART)로 연결해야 함
* 실시간 상태(서 / 보행 / 좌 / 전 / 후 낙상)를 콘솔에 출력하며, `fcm_module.py`를 통해 FCM 푸시를 전송

### 3) 통합 시나리오

```bash
(.venv) $ python main.py
```

`main.py`는 프로젝트별로 원하는 흐름(스피커 ↔ 낙상 모드 전환 등)을 조합하는 예시 코드입니다.

---

## 주요 파일 설명

| 파일                   | 역할                                            |
| -------------------- | --------------------------------------------- |
| **voice\_module.py** | 웨이크 워드 + Google STT/TTS + Gemini RAG로 Q\&A 수행 |
| **fall\_module.py**  | LD500 LiDAR를 읽어 낙상 여부를 분류 (PySerial 필요)       |
| **fcm\_module.py**   | Firebase Cloud Messaging 전송 래퍼                |
| **main.py**          | 두 기능을 하나로 묶는 데모 엔트리 포인트                       |

---

## 커스터마이징 포인트

* **웨이크 워드** : `WAKE_WORDS` 리스트 수정
* **음성 감지 민감도** : `AUDIO_THRESH`, `webrtcvad.Vad(level)` 조정
* **타임존** : `LOCAL_TZ = ZoneInfo("Asia/Seoul")` 변경
* **LD500 임계값** : `fall_module.py` 내부 `THRESH_*` 상수 조정

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

Happy Hacking! 🎙️🤖
