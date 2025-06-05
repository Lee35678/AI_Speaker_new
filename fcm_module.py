# fcm_module.py
import requests
import time
import os

# Firebase 콘솔 > 프로젝트 설정 > 클라우드 메시징 > 서버 키(legacy)는
# 환경 변수 `FCM_SERVER_KEY` 에서 읽어옵니다. 설정되지 않으면 빈 문자열을 사용합니다.
SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")

FCM_URL = "https://fcm.googleapis.com/fcm/send"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"key={SERVER_KEY}"
}

def send_fcm_alert(title: str, body: str):
    payload = {
        "to": "/topics/fallAlerts",
        "notification": {
            "title": title,
            "body": body
        },
        "data": {
            "event": "fall",
            "timestamp": time.time()
        }
    }
    try:
        res = requests.post(FCM_URL, json=payload, headers=headers)
        print(f"FCM 전송 상태: {res.status_code}, 응답: {res.text}")
    except Exception as e:
        print(f"FCM 전송 실패: {e}")
