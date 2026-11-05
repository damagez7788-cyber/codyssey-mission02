"""입력을 검사하고 잘못된 값이면 같은 질문으로 돌아갑니다."""


def read_number(prompt, minimum, maximum):
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print(f"{minimum}~{maximum} 사이의 숫자를 입력해 주세요.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"범위 오류: {minimum}~{maximum} 사이에서 골라 주세요.")


def read_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("빈 내용은 등록할 수 없습니다. 다시 입력해 주세요.")
