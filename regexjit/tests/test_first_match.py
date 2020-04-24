import pytest
import csv
import sys, os

p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p + "/../")

from programcompiled import compile_regex
import jitbuilder


def get_regex_test_objects():
    with open(
        "/Users/daytonjallen/regex-jit/regexjit/tests/data/match_tests.csv"
    ) as csv_file:
        return list(csv.reader(csv_file, delimiter=","))


regex_test_objects = get_regex_test_objects()


@pytest.mark.parametrize("text, regex, expected", regex_test_objects)
def test_search_nfa(text, regex, expected, benchmark):
    if not jitbuilder.initialize_jit():
        exit()
    p = compile_regex(regex)
    res = (
        True if benchmark(p.find_first, text.encode("utf-8"), 1) is not None else False
    )
    jitbuilder.shutdown_jit()
    assert res == int(expected)

