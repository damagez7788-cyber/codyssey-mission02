"""게임 전체의 메뉴와 데이터 흐름을 관리합니다."""
from pathlib import Path

from input_utils import read_number
from storage import StateStore


class QuizGame:
    def __init__(self, state_path=None):
        path = state_path if state_path is not None else Path(__file__).resolve().parent / "state.json"
        self.store = StateStore(path)
        self.quizzes, self.best_score, self.played, self.best_result = self.store.load()

    def save(self):
        return self.store.save(self.quizzes, self.best_score, self.played, self.best_result)

    def show_list(self):
        print(f"\n등록된 퀴즈: {len(self.quizzes)}개")
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다. 메뉴 2에서 추가해 주세요.")
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"[{number}] {quiz.question}")

    def play(self):
        if not self.quizzes:
            print("풀 퀴즈가 없습니다. 메뉴 2에서 먼저 추가해 주세요.")
            return
        correct = 0
        total = len(self.quizzes)
        print(f"\n퀴즈를 시작합니다. 총 {total}문제입니다.")
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"\n[문제 {number}/{total}]")
            quiz.display()
            answer = read_number("정답 번호 (1~4): ", 1, 4)
            if quiz.is_correct(answer):
                correct += 1
                print("정답입니다!")
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다.")
        score = round(correct * 100 / total)
        print(f"결과: {total}문제 중 {correct}문제 정답! ({score}점)")
        if not self.played or score > self.best_score:
            self.best_score = score
            self.best_result = {"correct": correct, "total": total}
            print("새로운 최고 점수입니다!")
        self.played = True
        self.save()

    def run(self):
        while True:
            print("\n개발 기초 퀴즈\n1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
            choice = read_number("선택: ", 1, 5)
            if choice == 5:
                self.save()
                print("퀴즈를 종료합니다.")
                return
            if choice == 1:
                self.play()
            elif choice == 3:
                self.show_list()
            else:
                print("선택한 기능을 개발 중입니다.")
