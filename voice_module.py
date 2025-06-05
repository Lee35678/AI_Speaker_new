"""
voice_module.py – RAG 기반 AI 스피커 + Wake-Word + optional webrtc-VAD
Rev: 2025-05-26  (wake-word 인식률 개선)
"""

from __future__ import annotations
import logging, math, os, re, struct, tempfile, threading, time, wave
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import pygame, pyaudio, requests
from google.auth.exceptions import DefaultCredentialsError

# ────────────────────────────────────────────────────────────
#  환경 변수
# ────────────────────────────────────────────────────────────
CSE_API_KEY = os.getenv("GOOGLE_API_KEY_SEARCH") or "YOUR-CUSTOM-SEARCH-KEY"
CSE_ID      = os.getenv("GOOGLE_SEARCH_ENGINE_ID") or "YOUR-SEARCH-ENGINE-CX"
CSE_CX      = CSE_ID
PALM_KEY    = os.getenv("GOOGLE_API_KEY_PALM")    or "YOUR-GEMINI-KEY"
MODEL_NAME  = "gemini-2.5-pro-preview-05-06"

LOCAL_TZ    = ZoneInfo("Asia/Seoul")

# 웨이크 워드 --------------------------------------------
WAKE_WORDS  = [
    r"실비야", r"실비[아야]?",          # “실비야”, “실비아”, “실비” 허용    ★ 수정
    r"헤이\s*실비", r"비아"            # 많이 틀리는 “비아”도 허용          ★ 수정
]
WAKE_PAT    = re.compile("|".join(WAKE_WORDS), re.I)

# (선택) 오프라인 키워드 스팟터 훅 ------------------------  ★ 추가
USE_KWS = False
try:
    import pvporcupine       # pip install pvporcupine
    PORCUPINE = pvporcupine.create(keywords=["shee-bee-ya"])  # 커스텀 모델 사용 시
    USE_KWS = True
except Exception:
    PORCUPINE = None

# STT 녹음 기본값 ---------------------------------------
RATE = 16_000
CHUNK = 1024                # RMS 방식 기본값 (64 ms)
CHANNELS = 1
PA_FMT = pyaudio.paInt16
AUDIO_THRESH = 300
MAX_PHRASE = 10             # 최대 발화 길이(초)

# ────────────────────────────────
#  로깅
# ────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("voice_module")

# ────────────────────────────────
#  외부 API 초기화
# ────────────────────────────────
GEMINI_OK = False
try:
    import google.generativeai as genai
    genai.configure(api_key=PALM_KEY)
    GEMINI_OK = True
    logger.info("Gemini 초기화 성공")
except Exception as e:
    logger.warning(f"Gemini 초기화 실패: {e}")

USE_CLOUD_TTS = USE_CLOUD_STT = False
try:
    from google.cloud import texttospeech, speech_v1p1beta1 as speech
    TTS_CLIENT = texttospeech.TextToSpeechClient()
    STT_CLIENT = speech.SpeechClient()
    USE_CLOUD_TTS = USE_CLOUD_STT = True
    logger.info("Google Cloud STT/TTS 클라이언트 초기화 성공")
except DefaultCredentialsError as e:
    logger.warning(f"ADC 미설정 → Cloud STT/TTS 비활성화: {e}")

# optional webrtc-VAD -----------------------------------
try:
    import webrtcvad
    VAD = webrtcvad.Vad(1)          # aggressiveness 0~3
    CHUNK = 480                     # 30 ms (480 samples @ 16 kHz)
    logger.info("webrtc-VAD 사용, CHUNK=480")
except ImportError:
    VAD = None
    logger.info("webrtc-VAD 미설치 → RMS 방식, CHUNK=1024")

# Pygame mixer
try:
    pygame.mixer.init()
    logger.info("Pygame mixer 초기화 완료")
except pygame.error as e:
    logger.error(f"Pygame mixer 초기화 실패: {e}")

# 웨이크 워드 효과음
PLING_PATH = os.path.join(os.path.dirname(__file__), "Pling Sound.wav")
if not os.path.exists(PLING_PATH):
    PLING_PATH = None

# ────────────────────────────────
#  TTS
# ────────────────────────────────
_is_speaking = False
_stop_flag   = threading.Event()

def _generate_gtts(text: str, mp3_path: str):
    try:
        from gtts import gTTS
        gTTS(text=text, lang="ko").save(mp3_path)
        logger.info("gTTS 음성 생성")
    except Exception as e:
        logger.error(f"gTTS 실패: {e}")

def speak_text(text: str, interruptible: bool = True):
    global _is_speaking
    if not text:
        return
    _is_speaking = True
    mp3_path = os.path.join(tempfile.gettempdir(), "tts_output.mp3")

    if USE_CLOUD_TTS:
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )
            audio_conf = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            audio = TTS_CLIENT.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_conf
            )
            with open(mp3_path, "wb") as f:
                f.write(audio.audio_content)
            logger.info("Cloud TTS 생성")
        except Exception as e:
            logger.error(f"Cloud TTS 오류 → gTTS 대체: {e}")
            _generate_gtts(text, mp3_path)
    else:
        _generate_gtts(text, mp3_path)

    threading.Thread(
        target=_playback, args=(mp3_path, interruptible), daemon=True
    ).start()

def _playback(path: str, interruptible: bool):
    global _is_speaking
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if interruptible and _stop_flag.is_set():
                pygame.mixer.music.stop()
                logger.info("재생 중단")
                break
            time.sleep(0.05)
        pygame.mixer.music.unload()
    except Exception as e:
        logger.error(f"오디오 재생 오류: {e}")
    finally:
        _is_speaking = False
        _stop_flag.clear()
        try:
            os.remove(path)
        except:
            pass

# ────────────────────────────────
#  STT 녹음
# ────────────────────────────────
def _rms(data: bytes) -> float:
    cnt = len(data) // 2
    if not cnt:
        return 0.0
    samples = struct.unpack("<" + "h" * cnt, data)
    return math.sqrt(sum(s * s for s in samples) / cnt)

def _is_speech_vad(frame: bytes) -> bool:
    if not VAD:
        return _rms(frame) > AUDIO_THRESH
    return VAD.is_speech(frame, RATE)

def record_audio(timeout: int = 5) -> Optional[bytes]:
    """마이크 입력을 녹음하고 WAV bytes 반환. 타임아웃(초) 내 말소리 없으면 None."""
    p = pyaudio.PyAudio()
    stream = p.open(
        format=PA_FMT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    frames: List[bytes] = []
    recording = False
    end_time = time.time() + timeout

    logger.info("듣고 있습니다…")
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)

        # 오프라인 KWS 사용 시 즉시 체크 --------------------  ★ 추가
        if USE_KWS and not recording:
            pcm = struct.unpack_from("h" * (len(data) // 2), data)
            if PORCUPINE.process(pcm) >= 0:
                logger.info("Porcupine 키워드 탐지!")
                recording = True      # 이후 STT용으로 이어서 녹음

        speech_flag = _is_speech_vad(data)

        if not recording:
            if speech_flag:
                recording = True
                frames.append(data)
                logger.info("음성 감지!")
            elif time.time() > end_time:
                logger.info("입력 타임아웃")
                break
        else:
            frames.append(data)
            dur = len(frames) * CHUNK / RATE
            if dur >= MAX_PHRASE or (not speech_flag and dur > 0.5):
                break

    stream.stop_stream()
    stream.close()
    p.terminate()

    if not recording:
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        wav_path = tmp.name

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(PA_FMT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    with open(wav_path, "rb") as f:
        wav_bytes = f.read()
    os.remove(wav_path)
    return wav_bytes

# SpeechContext 문구 및 boost ---------------------------  ★ 추가
SPEECH_CONTEXT_PHRASES = ["실비야", "헤이 실비", "실비아", "실비", "비아"]

def speech_to_text(wav_bytes: bytes) -> str:
    if not USE_CLOUD_STT:
        return ""
    try:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="ko-KR",
            enable_automatic_punctuation=True,
            model="command_and_search",                  # ★ 수정
            speech_contexts=[
                speech.SpeechContext(
                    phrases=SPEECH_CONTEXT_PHRASES,
                    boost=20.0                           # ★ 큰 가중치
                )
            ],
            max_alternatives=3                           # 후보 더 받기
        )
        audio = speech.RecognitionAudio(content=wav_bytes)
        resp = STT_CLIENT.recognize(config=config, audio=audio)
        return resp.results[0].alternatives[0].transcript if resp.results else ""
    except Exception as e:
        logger.error(f"STT 오류: {e}")
        return ""

# ────────────────────────────────
#  Google Custom Search (safe extract)
# ────────────────────────────────
def google_search(query: str, num: int = 5, _retry=True) -> List[Dict]:
    params = {
        "key": CSE_API_KEY,
        "cx": CSE_CX,
        "q": query,
        "num": num,
        "hl": "ko",
        "gl": "kr",
    }
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1", params=params, timeout=10
        )
        items = r.json().get("items", [])
        if not items and _retry:
            params.pop("hl", None)
            params.pop("gl", None)
            return google_search(query, num, _retry=False)
        return [
            {
                "title": it.get("title", ""),
                "snippet": it.get("snippet") or it.get("htmlSnippet", ""),
                "link": it.get("link", ""),
            }
            for it in items
        ]
    except Exception as e:
        logger.error(f"검색 실패: {e}")
        return []

# ────────────────────────────────
#  RAG 답변
# ────────────────────────────────
def rag_answer(question: str) -> str:
    if not GEMINI_OK:
        return "죄송합니다, 현재 지식 검색 기능을 사용할 수 없습니다."
    docs = google_search(question, 5)
    if not docs:
        prompt = (
            "인터넷 자료를 찾지 못했습니다. 당신의 지식과 추론으로 "
            f"다음 질문에 답해 주세요.\n\n### 질문:\n{question}\n\n### 답변:"
        )
        try:
            m = genai.GenerativeModel(MODEL_NAME)
            return m.generate_content(prompt).text.strip()
        except Exception as e:
            logger.error(f"Gemini 오류: {e}")
            return "답변을 생성하지 못했습니다."

    context = "\n\n".join(
        f"[문서{i+1}] 제목:{d['title']}\n요약:{d['snippet']}\n링크:{d['link']}"
        for i, d in enumerate(docs)
    )
    prompt = (
        "당신은 한국어 AI 어시스턴트입니다. 아래 검색 결과를 종합해 "
        "정확하고 간결하게 답하세요(필요시 링크를 괄호로 표시). 답변은 사람에게 말로 설명하듯이 자연스러운 말투로 작성할것. 답변에 링크주소나 특수문자 기호같은것들은 넣지말고 작성해. \n\n"
        f"### 질문:\n{question}\n\n### 검색 결과:\n{context}\n\n### 답변:"
    )
    try:
        m = genai.GenerativeModel(MODEL_NAME)
        return (
            m.generate_content(prompt, generation_config={"temperature": 0.3})
            .text.strip()
        )
    except Exception as e:
        logger.error(f"Gemini 오류: {e}")
        return "답변을 생성하지 못했습니다."

# ────────────────────────────────
#  현재 시각
# ────────────────────────────────
TIME_PAT = re.compile(r"(지금|현재)\s*(몇\s*시|시간)", re.I)

def get_now_time() -> str:
    now = datetime.now(LOCAL_TZ)
    return f"지금 시간은 {now.strftime('%p %I시 %M분')}입니다."

# ────────────────────────────────
#  명령 파싱
# ────────────────────────────────
EXIT_PAT = re.compile(r"(종료|그만|멈춰|꺼져)")

def parse_command(text: str) -> str:
    if not text:
        return ""
    if EXIT_PAT.search(text):
        return "__EXIT__"
    if TIME_PAT.search(text):
        return get_now_time()
    return rag_answer(text)

# ────────────────────────────────
#  메인 루프
# ────────────────────────────────
def main():
    logger.info("AI 스피커 시작")
    speak_text("AI 스피커를 시작합니다. '실비야' 하고 불러 주세요.", interruptible=False)

    listening_for_command = False
    try:
        while True:
            wav = record_audio(timeout=5)
            query = speech_to_text(wav) if wav else ""
            if not query:
                continue
            logger.info(f"STT: {query}")

            if not listening_for_command:
                if WAKE_PAT.search(query):
                    listening_for_command = True
                    if PLING_PATH:
                        pygame.mixer.Sound(PLING_PATH).play()
                    else:
                        speak_text("네, 말씀하세요.", interruptible=False)
                    continue
                else:
                    logger.info("웨이크 워드 없음 → 무시")
                    continue
            else:
                listening_for_command = False
                response = parse_command(query)
                if response == "__EXIT__":      # 종료 명령
                    speak_text("안녕히 계세요. 종료합니다.")
                    break
                if response:
                    logger.info(f"AI: {response}")
                    speak_text(response)

    except KeyboardInterrupt:
        logger.info("종료 신호 수신")
    finally:
        pygame.mixer.quit()
        logger.info("프로그램 종료")

if __name__ == "__main__":
    main()
