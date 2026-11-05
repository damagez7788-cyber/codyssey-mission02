import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defaults import default_quizzes
from game import QuizGame
from input_utils import read_number, read_text
import main
from quiz import Quiz
from storage import StateStore


class QuizTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "state.json"
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def test_quiz_validates_and_round_trips(self):
        quiz = Quiz(" 문제 ", ["a", "b", "c", "d"], 2)
        self.assertTrue(Quiz.from_dict(quiz.to_dict()).is_correct(2))
        self.assertFalse(quiz.is_correct(1))
        for answer in (0, 5, True, "1"):
            with self.assertRaises(ValueError):
                Quiz("문제", ["a", "b", "c", "d"], answer)

    def test_bad_question_choices(self):
        for question, choices in (("", ["a"] * 4), ("문제", ["a"] * 3), ("문제", ["", "b", "c", "d"])):
            with self.assertRaises(ValueError):
                Quiz(question, choices, 1)

    def test_number_retries_blank_text_and_range(self):
        with patch("builtins.input", side_effect=["", "abc", "9", "0", " 2 "]):
            self.assertEqual(read_number("선택", 1, 5), 2)

    def test_text_retries_blank(self):
        with patch("builtins.input", side_effect=[" ", " 테스트 "]):
            self.assertEqual(read_text("문제"), "테스트")

    def test_first_run_defaults_and_score(self):
        game = QuizGame(self.path)
        self.assertGreaterEqual(len(game.quizzes), 5)
        self.assertFalse(game.played)
        game.show_score()
        self.assertIn("아직 퀴즈를 풀지", self.output.getvalue())

    def test_add_and_restart_preserves_korean(self):
        game = QuizGame(self.path)
        with patch("builtins.input", side_effect=["한글 새 문제?", "가", "나", "다", "라", " 2 "]):
            game.add_quiz()
        loaded = QuizGame(self.path)
        self.assertEqual(len(loaded.quizzes), 7)
        self.assertEqual(loaded.quizzes[-1].answer, 2)
        self.assertIn("한글 새 문제", self.path.read_text(encoding="utf-8"))

    def test_play_score_persists_and_never_decreases(self):
        game = QuizGame(self.path)
        with patch("builtins.input", side_effect=[str(quiz.answer) for quiz in game.quizzes]):
            game.play()
        self.assertEqual(QuizGame(self.path).best_score, 100)
        with patch("builtins.input", side_effect=[str(quiz.answer % 4 + 1) for quiz in game.quizzes]):
            game.play()
        self.assertEqual(QuizGame(self.path).best_score, 100)
        self.assertEqual(game.best_result, {"correct": 6, "total": 6})

    def test_zero_score_is_distinct_from_never_played(self):
        game = QuizGame(self.path)
        with patch("builtins.input", side_effect=[str(quiz.answer % 4 + 1) for quiz in game.quizzes]):
            game.play()
        loaded = QuizGame(self.path)
        self.assertTrue(loaded.played)
        loaded.show_score()
        self.assertIn("최고 점수: 0점", self.output.getvalue())

    def test_empty_quiz_list(self):
        self.path.write_text('{"quizzes": [], "best_score": 0, "played": false}', encoding="utf-8")
        game = QuizGame(self.path)
        game.show_list()
        game.play()
        self.assertIn("풀 퀴즈가 없습니다", self.output.getvalue())

    def test_corrupt_json_backup(self):
        original = "깨진 데이터 {"
        self.path.write_text(original, encoding="utf-8")
        game = QuizGame(self.path)
        self.assertEqual(len(game.quizzes), 6)
        backup = next(self.path.parent.glob("state.corrupt-*.json"))
        self.assertEqual(backup.read_text(encoding="utf-8"), original)
        self.assertTrue(game.save())
        self.assertEqual(len(json.loads(self.path.read_text(encoding="utf-8"))["quizzes"]), 6)

    def test_bad_schema_is_recovered(self):
        for data in ({}, {"quizzes": {}, "best_score": 0}, {"quizzes": [], "best_score": -1},
                     {"quizzes": [], "best_score": True}, {"quizzes": [{"question": "bad"}], "best_score": 0}):
            self.path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(len(QuizGame(self.path).quizzes), 6)

    def test_read_failure_does_not_overwrite_original(self):
        self.path.write_text("original", encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=PermissionError("read denied")):
            game = QuizGame(self.path)
        self.assertFalse(game.save())
        self.assertEqual(self.path.read_text(), "original")

    def test_failed_backup_blocks_overwrite(self):
        self.path.write_text("bad", encoding="utf-8")
        with patch("storage.shutil.copy2", side_effect=PermissionError("backup denied")):
            game = QuizGame(self.path)
        self.assertFalse(game.save())
        self.assertEqual(self.path.read_text(), "bad")

    def test_write_failure_is_reported(self):
        store = StateStore(self.path.parent / "missing" / "state.json")
        self.assertFalse(store.save(default_quizzes(), 0, False, None))
        self.assertIn("저장 실패", self.output.getvalue())

    def test_atomic_replace_failure_preserves_file(self):
        self.path.write_text("original", encoding="utf-8")
        with patch("storage.os.replace", side_effect=OSError("replace denied")):
            self.assertFalse(StateStore(self.path).save(default_quizzes(), 0, False, None))
        self.assertEqual(self.path.read_text(), "original")
        self.assertEqual(list(self.path.parent.glob(".state-*.tmp")), [])

    def test_ctrl_c_and_eof_save_completed_state(self):
        for error in (KeyboardInterrupt, EOFError):
            game = QuizGame(self.path)
            with patch("main.QuizGame", return_value=game), patch("builtins.input", side_effect=error):
                main.main()
            self.assertTrue(self.path.exists())

    def test_menu_routes_and_normal_exit(self):
        game = QuizGame(self.path)
        with patch("builtins.input", side_effect=["3", "4", "5"]):
            game.run()
        self.assertIn("등록된 퀴즈: 6개", self.output.getvalue())
        self.assertIn("퀴즈를 종료", self.output.getvalue())

    def test_partial_registration_is_not_added(self):
        game = QuizGame(self.path)
        with patch("builtins.input", side_effect=["unfinished", EOFError]):
            with self.assertRaises(EOFError):
                game.add_quiz()
        self.assertEqual(len(game.quizzes), 6)


if __name__ == "__main__":
    unittest.main()
