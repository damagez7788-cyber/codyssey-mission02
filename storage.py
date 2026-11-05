"""state.json을 읽고 임시 파일을 거쳐 안전하게 저장합니다."""
import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile

from defaults import default_quizzes
from quiz import Quiz


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        self.writable = True

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("quizzes"), list):
                raise ValueError("quizzes 목록이 없습니다.")
            quizzes = [Quiz.from_dict(item) for item in data["quizzes"]]
            score = data["best_score"]
            played = data.get("played", score > 0)
            result = data.get("best_result")
            if type(score) is not int or not 0 <= score <= 100 or type(played) is not bool:
                raise ValueError("점수 또는 풀이 여부 형식이 잘못됐습니다.")
            if result is not None:
                if not isinstance(result, dict):
                    raise ValueError("최고 기록 형식이 잘못됐습니다.")
                correct, total = result.get("correct"), result.get("total")
                if type(correct) is not int or type(total) is not int or not 0 <= correct <= total or total < 1:
                    raise ValueError("최고 기록의 정답 수가 잘못됐습니다.")
                if round(correct * 100 / total) != score:
                    raise ValueError("최고 점수와 정답 수가 맞지 않습니다.")
            print(f"저장된 퀴즈 {len(quizzes)}개와 최고 점수 {score}점을 불러왔습니다.")
            return quizzes, score, played, result
        except FileNotFoundError:
            print("첫 실행입니다. 기본 퀴즈 6개로 시작합니다.")
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            print(f"데이터 손상: {error}")
            backup = self.path.with_name("state.corrupt-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".json")
            try:
                shutil.copy2(self.path, backup)
                print(f"원본을 {backup.name}에 보관하고 기본 데이터로 복구합니다.")
            except OSError as backup_error:
                self.writable = False
                print(f"원본 보관 실패: {backup_error}. 원본 보호를 위해 이번 실행은 저장하지 않습니다.")
        except OSError as error:
            self.writable = False
            print(f"파일 읽기 실패: {error}. 기본 퀴즈로 실행하며 원본을 덮어쓰지 않습니다.")
        return default_quizzes(), 0, False, None

    def save(self, quizzes, best_score, played, best_result):
        if not self.writable:
            print("이번 실행의 저장은 제한되어 있습니다. 폴더 접근 권한을 확인해 주세요.")
            return False
        temporary = None
        try:
            data = {"quizzes": [quiz.to_dict() for quiz in quizzes], "best_score": best_score,
                    "played": played, "best_result": best_result}
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=".state-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, self.path)
            return True
        except OSError as error:
            print(f"저장 실패: {error}. 현재 내용은 메모리에만 있습니다. 종료 전에 저장 경로를 확인해 주세요.")
            return False
        finally:
            if temporary is not None and temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass
