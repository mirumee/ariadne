import sys
from pathlib import Path

from conf import RESULTS_DIR, RESULTS_LIMIT


def main():
    if len(sys.argv) != 2:
        raise Exception(
            "'rotate_results.py' should be called with single "
            "arg: a substr for name with benchmarks dir to rotate"
        )

    result_substr = str(sys.argv[1])

    for sub_results_dir in Path(RESULTS_DIR).glob("**"):
        if sub_results_dir.is_dir() and result_substr in sub_results_dir.name:
            rotate_results(sub_results_dir)


def rotate_results(results_dir: Path):
    json_files = []
    for json_file in results_dir.glob("*.json"):
        if json_file.is_file():
            json_files.append(json_file.name)

    json_files = sorted(json_files, reverse=True)
    if len(json_files) > RESULTS_LIMIT:
        for file_to_delete in json_files[RESULTS_LIMIT:]:
            file_path = results_dir / file_to_delete
            file_path.unlink()


if __name__ == "__main__":
    main()
