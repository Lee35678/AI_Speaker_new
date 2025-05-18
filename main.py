import threading
import voice_module   # voice_module.main() 내부에 while-loop 존재
import fall_module    # fall_module.run() 함수 (카메라 창 표시)

def start_voice():
    voice_module.main()    # 블로킹 루프

if __name__ == "__main__":
    # 1) 음성 챗봇을 백그라운드 스레드로 실행
    t_voice = threading.Thread(target=start_voice, daemon=True, name="VoiceThread")
    t_voice.start()

    print("시스템 시작: 음성 챗봇(스레드) + 낙상 감지(메인) 동시 실행 중 …")
    print("Ctrl+C 를 누르면 전체 프로그램이 종료됩니다.")

    try:
        # 2) 낙상 감지 루프는 메인 스레드에서 실행
        fall_module.run()
    except KeyboardInterrupt:
        print("\n사용자 종료 요청 – 프로그램을 종료합니다.")