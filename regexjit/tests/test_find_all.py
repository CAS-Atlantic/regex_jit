import pytest
import csv
import sys, os

p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p + "/../")

from program import compile_regex
import jitbuilder


def get_regex_test_objects():
    with open(
        "/Users/daytonjallen/regex-jit/regexjit/tests/data/find_all_tests.csv"
    ) as csv_file:
        return list(csv.reader(csv_file, delimiter=","))


regex_test_objects = get_regex_test_objects()

@pytest.mark.parametrize("regex, expected", regex_test_objects)
def test_search_nfa(regex, expected, benchmark):
    with open(
        "/Users/daytonjallen/regex-jit/regexjit/tests/data/sherlock.txt", "rb"
    ) as data_file:
        text = data_file.read()
    if not jitbuilder.initialize_jit():
        exit()
    p = compile_regex(regex)
    res = benchmark(p.find_all, text, 1)
    jitbuilder.shutdown_jit()
    assert res == int(expected)

