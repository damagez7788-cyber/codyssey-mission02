"""개발 도구와 파이썬 기초를 복습하는 기본 문제입니다."""
from quiz import Quiz


def default_quizzes():
    data = [
        ("Ubuntu에서 현재 폴더의 위치를 확인하는 명령은?", ["pwd", "mkdir", "chmod", "cp"], 1),
        ("Dockerfile을 읽어 실행 준비물인 이미지를 만드는 작업은?", ["pull", "build", "stop", "logs"], 2),
        ("Git에서 내 컴퓨터에 변경 이력을 기록하는 명령은?", ["clone", "pull", "commit", "push"], 3),
        ("Python에서 여러 값을 순서대로 담는 자료형은?", ["bool", "int", "str", "list"], 4),
        ("이름표와 값을 짝으로 저장하는 Python 자료형은?", ["dict", "int", "bool", "str"], 1),
        ("JSON 파일에 데이터를 저장하는 이유는?", ["터미널 색을 바꾸려고", "프로그램을 꺼도 데이터를 남기려고", "비밀번호를 공개하려고", "이미지를 빌드하려고"], 2),
    ]
    return [Quiz(question, choices, answer) for question, choices, answer in data]
