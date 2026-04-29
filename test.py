# 파일명: test.py
import sys

# Windows 기본 콘솔(cp1252)에서 이모지·한글 print 시 UnicodeEncodeError 방지
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import matlab.engine
except ModuleNotFoundError:
    sys.stderr.write(
        "matlab.engine 을 불러올 수 없습니다. MATLAB Engine API for Python 이 필요합니다.\n"
        "이 프로젝트에서는 가상환경으로 실행해 보세요:\n"
        '  .\\venv\\Scripts\\python.exe test.py\n'
    )
    raise SystemExit(1)

def main():
    print("⏳ MATLAB 엔진을 켜는 중입니다... (초기 실행 시 10~20초 정도 소요될 수 있습니다)")
    
    # MATLAB 백그라운드 프로세스 시작
    eng = matlab.engine.start_matlab()
    print("✅ MATLAB 엔진 부팅 완료!\n")

    try:
        print("▶️ 파이썬에서 test_prach.m 함수를 호출합니다...")
        
        # 파라미터 준비 (MATLAB으로 넘길 숫자는 float 형식을 권장합니다)
        format_type = 'B2'
        scs_value = 15.0 
        
        # 중요: nargout=2 는 MATLAB 함수가 리턴할 '결과값의 개수'를 의미합니다.
        config_idx, message = eng.test_prach(format_type, scs_value, nargout=2)
        
        print("\n--- 🎯 파이썬 터미널로 무사히 리턴된 결과 ---")
        print(f"👉 도출된 Config Index : {config_idx}")
        print(f"👉 MATLAB의 메시지     : {message}")
        print("----------------------------------------------")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

    finally:
        # 작업이 끝나면 메모리 반환을 위해 엔진을 종료합니다.
        eng.quit()
        print("\n🛑 MATLAB 엔진이 안전하게 종료되었습니다.")

if __name__ == "__main__":
    main()