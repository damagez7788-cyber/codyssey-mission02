"""제출 보완 근거를 실제 실행으로 만듭니다. 개인 state.json은 건드리지 않습니다."""
import argparse
import contextlib
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from defaults import default_quizzes
from quiz import Quiz
from storage import StateStore

CORE = ("main.py", "game.py", "quiz.py", "input_utils.py", "defaults.py", "storage.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def run(command, cwd, input_text=None, timeout=90):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    result = subprocess.run(command, cwd=cwd, input=input_text, text=True,
                            encoding="utf-8", capture_output=True, env=env, timeout=timeout)
    return {"command": [str(x) for x in command], "stdin": input_text,
            "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}


def save_log(path, record):
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def integration():
    with tempfile.TemporaryDirectory(prefix="mission02-cli-") as folder:
        folder = Path(folder)
        for filename in CORE:
            shutil.copy2(ROOT / filename, folder / filename)
        # 빈 메뉴/문자/범위 오류, 빈 문제/선택지, 잘못된 정답 번호도 재입력합니다.
        lines = ["", "hello", "0", "2", "", "검증용 추가 문제", "", "가", "나", "다", "라", "5", "1", "3", "1"]
        lines += [str(q.answer) for q in default_quizzes()] + ["1", "4", "5"]
        first = run([sys.executable, "main.py"], folder, "\n".join(lines) + "\n")
        assert first["exit_code"] == 0, first
        for marker in ("사이의 숫자를 입력해 주세요.", "범위 오류:", "빈 내용은 등록할 수 없습니다."):
            assert marker in first["stdout"], marker
        state = json.loads((folder / "state.json").read_text(encoding="utf-8"))
        assert len(state["quizzes"]) == 7 and state["best_score"] == 100
        assert state["best_result"] == {"correct": 7, "total": 7}
        restart = run([sys.executable, "main.py"], folder, "3\n4\n5\n")
        assert restart["exit_code"] == 0
        assert "저장된 퀴즈 7개와 최고 점수 100점" in restart["stdout"]
        assert "검증용 추가 문제" in restart["stdout"]
        eof = run([sys.executable, "main.py"], folder, "")
        assert eof["exit_code"] == 0 and "입력이 중단되었습니다." in eof["stdout"]
        (folder / "state.json").write_text("{ 손상된 JSON", encoding="utf-8")
        corrupt = run([sys.executable, "main.py"], folder, "5\n")
        backups = list(folder.glob("state.corrupt-*.json"))
        assert corrupt["exit_code"] == 0 and len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "{ 손상된 JSON"
        assert len(json.loads((folder / "state.json").read_text(encoding="utf-8"))["quizzes"]) == 6
        return {"passed": True, "add_play": first, "restart": restart, "eof": eof,
                "corrupt_recovery": corrupt, "verified": "7문제·100점 재실행 유지, EOF, 손상 원문 보관 및 6문제 복구"}


def benchmark(count):
    with tempfile.TemporaryDirectory(prefix="mission02-scale-") as folder:
        path = Path(folder) / "state.json"
        quizzes = [Quiz(f"합성 퀴즈 {i:06d}: 저장과 검색을 확인하는 문제입니다.",
                        ["첫 번째 선택지", "두 번째 선택지", "세 번째 선택지", "네 번째 선택지"], i % 4 + 1)
                   for i in range(count)]
        quizzes[0] = Quiz('한글·따옴표 "퀴즈"·줄바꿈\n이모지 🐍도 보존되나요?',
                          ['예 "가능"', "아니요", "줄바꿈\n선택지", "이모지 ✅"], 1)
        expected = [q.to_dict() for q in quizzes]
        store = StateStore(path)

        def save():
            assert store.save(quizzes, 100, True, {"correct": count, "total": count})

        def load():
            with contextlib.redirect_stdout(io.StringIO()):
                return store.load()

        # 시간 측정과 메모리 추적은 분리합니다. 첫 1회는 준비 실행입니다.
        save()
        assert len(load()[0]) == count
        saves, loads, hits, misses = [], [], [], []
        for _ in range(3):
            start = time.perf_counter()
            save()
            saves.append((time.perf_counter() - start) * 1000)
            start = time.perf_counter()
            restored, score, played, best = load()
            loads.append((time.perf_counter() - start) * 1000)
            assert [q.to_dict() for q in restored] == expected
            assert (score, played, best) == (100, True, {"correct": count, "total": count})
            for title, times, exists in ((quizzes[-1].question, hits, True), ("존재하지 않는 제목", misses, False)):
                start = time.perf_counter()
                for _ in range(100):
                    found = next((q for q in restored if q.question == title), None)
                    assert (found is not None) == exists
                times.append((time.perf_counter() - start) * 1000 / 100)

        peaks = {}
        for label, operation in (("save", save), ("load", load)):
            tracemalloc.start()
            result = operation()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peaks[label + "_python_peak_bytes"] = peak
            del result
        return {"quiz_count": count, "json_bytes": path.stat().st_size,
                "trials": 3, "warmup": 1, "searches_per_trial": 100,
                "save_ms": saves, "load_ms": loads, "linear_last_hit_ms": hits, "linear_miss_ms": misses,
                "median_save_ms": statistics.median(saves), "median_load_ms": statistics.median(loads),
                "median_linear_last_hit_ms": statistics.median(hits), "median_linear_miss_ms": statistics.median(misses),
                **peaks, "roundtrip_all_fields_equal": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "precheck_20261114")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    before = {name: digest(ROOT / name) for name in CORE + ("state.json",)}
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    environment = {"checked_at_kst": now.isoformat(), "python": sys.version,
                   "executable": sys.executable, "os": platform.platform(), "machine": platform.machine(),
                   "benchmark_scope": "합성 4지선다; 시간은 추적 없이 3회 중앙값; 메모리는 별도 1회 tracemalloc Python 할당 피크(RSS 아님)"}
    tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT)
    save_log(args.output / "01_tests.txt", {"environment": environment, **tests})
    assert tests["exit_code"] == 0, tests
    cli = integration()
    save_log(args.output / "02_cli.txt", {"environment": environment, **cli})
    metrics = [benchmark(1000), benchmark(10000)]
    save_log(args.output / "03_benchmark.json", {"environment": environment, "results": metrics})
    # 이 저장소만 명령 단위로 허용하며 전역 Git 설정은 바꾸지 않습니다.
    git = ["git", "-c", "safe.directory=" + ROOT.as_posix()]
    git_records = {"count": run(git + ["rev-list", "--count", "HEAD"], ROOT),
                   "head": run(git + ["rev-parse", "HEAD"], ROOT),
                   "commits": run(git + ["log", "--format=%h %s", "HEAD"], ROOT),
                   "branches": run(git + ["branch", "--list"], ROOT),
                   "status": run(git + ["status", "--short"], ROOT)}
    assert all(record["exit_code"] == 0 for record in git_records.values())
    save_log(args.output / "04_git_history.txt", {"environment": environment, **git_records})
    after = {name: digest(ROOT / name) for name in before}
    assert before == after, "실제 데이터 또는 코어 파일이 검증 중 변경됐습니다."
    save_log(args.output / "verification.json", {"environment": environment, "tests_exit_code": tests["exit_code"],
             "integration_passed": cli["passed"], "benchmark_passed": True,
             "tracked_commit_count": int(git_records["count"]["stdout"].strip()),
             "core_and_personal_state_unchanged": before == after, "sha256": before,
             "platform_reevaluation": "플랫폼 재평가 미실시", "github_update": "미실시"})
    print(json.dumps({"output": str(args.output), "environment": environment, "results": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
