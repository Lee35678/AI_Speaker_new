# fcm_module.py
import requests
import time

# Firebase 콘솔 > 프로젝트 설정 > 클라우드 메시징 > 서버 키(legacy) 복사해서 붙여넣으세요
SERVER_KEY = ""

FCM_URL = "https://fcm.googleapis.com/fcm/send"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"key={SERVER_KEY}"
}

def send_fcm_alert():
    payload = {
        "to": "/topics/fallAlerts",
        "notification": {
            "title": "낙상 감지 경고",
            "body": "독거노인 사용자께서 넘어짐이 감지되었습니다!"
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
