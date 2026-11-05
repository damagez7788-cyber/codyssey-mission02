"""개발 기초 퀴즈의 시작 파일입니다."""
from game import QuizGame


def main():
    game = QuizGame()
    try:
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n입력이 중단되었습니다. 완료된 내용까지 저장하고 종료합니다.")
        game.finish()


if __name__ == "__main__":
    main()
