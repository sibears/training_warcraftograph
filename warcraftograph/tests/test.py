import random
import string
import sys
import tempfile
from os import path

# Hack import paths.
sys.path.append(path.dirname(path.realpath(__file__)))
import warcraftograph


def test_smoke(msg: str):
    with tempfile.TemporaryDirectory() as temp:
        f = path.join(temp, "test.jpg")

        warcraftograph.encode(msg, f)
        got = warcraftograph.decode(f)
        if got != msg:
            raise RuntimeError(f"want {msg} but got {got}")


def random_word(n):
    letters = string.printable
    return "".join(random.choice(letters) for _ in range(n))


# Pytest is for weak ones B].
if __name__ == "__main__":
    cases = [
        "a",
        "a" * 4,
        "a" * 36,
        "Hello, world!",
        "Привет, мир!",
        random_word(4),
        random_word(40),
        random_word(1336),
    ]

    failed = 0
    for i, case in enumerate(cases):
        print(f"Test case #{i}", end="")
        try:
            test_smoke(case)
            print("\t[OK]")
        except Exception as e:
            failed += 1
            print("\t[ERR]")
            print(f"\t\t{e}")

    if failed:
        print(f"Failed {failed} test cases")
        exit(128)
