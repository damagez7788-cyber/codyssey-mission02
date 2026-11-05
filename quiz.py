"""문제 하나의 데이터와 동작을 묶습니다."""


class Quiz:
    def __init__(self, question, choices, answer):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 비어 있지 않은 글이어야 합니다.")
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError("선택지는 정확히 4개여야 합니다.")
        if any(not isinstance(item, str) or not item.strip() for item in choices):
            raise ValueError("선택지는 비어 있지 않은 글이어야 합니다.")
        if type(answer) is not int or not 1 <= answer <= 4:
            raise ValueError("정답 번호는 1~4의 정수여야 합니다.")
        self.question = question.strip()
        self.choices = [item.strip() for item in choices]
        self.answer = answer

    def display(self):
        print(self.question)
        for number, choice in enumerate(self.choices, start=1):
            print(f"  {number}. {choice}")

    def is_correct(self, answer):
        return answer == self.answer

    def to_dict(self):
        return {"question": self.question, "choices": self.choices, "answer": self.answer}

    @classmethod
    def from_dict(cls, item):
        if not isinstance(item, dict):
            raise ValueError("퀴즈 데이터는 객체여야 합니다.")
        return cls(item["question"], item["choices"], item["answer"])
