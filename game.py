"""게임 전체의 메뉴와 데이터 흐름을 관리합니다."""
from pathlib import Path

from input_utils import read_number, read_text
from quiz import Quiz
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

    def add_quiz(self):
        print("\n새 퀴즈를 등록합니다. 입력을 모두 끝내면 저장합니다.")
        question = read_text("문제: ")
        choices = [read_text(f"선택지 {number}: ") for number in range(1, 5)]
        answer = read_number("정답 번호 (1~4): ", 1, 4)
        self.quizzes.append(Quiz(question, choices, answer))
        if self.save():
            print("퀴즈를 추가하고 파일에 저장했습니다.")
        else:
            print("퀴즈는 현재 실행에만 추가됐습니다. 파일 저장은 실패했습니다.")

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

    def show_score(self):
        if not self.played:
            print("아직 퀴즈를 풀지 않았습니다. 메뉴 1에서 도전해 보세요.")
            return
        print(f"최고 점수: {self.best_score}점")
        if self.best_result is not None:
            print(f"최고 기록 당시 {self.best_result['total']}문제 중 {self.best_result['correct']}문제 정답")

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
            elif choice == 2:
                self.add_quiz()
            elif choice == 3:
                self.show_list()
            elif choice == 4:
                self.show_score()
