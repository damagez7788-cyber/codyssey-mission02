"""개발 기초 퀴즈의 시작 파일입니다."""
from input_utils import read_number


def main():
    while True:
        print("\n개발 기초 퀴즈\n1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
        choice = read_number("선택: ", 1, 5)
        if choice == 5:
            print("퀴즈를 종료합니다.")
            break
        print("선택한 기능을 개발 중입니다.")


if __name__ == "__main__":
    main()
