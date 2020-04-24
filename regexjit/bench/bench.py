import pyperf

runner = pyperf.Runner()

regular_expressions = [
    r">.+<",
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
    r"^[a-z0-9_-]{3,16}$",
    r"^#?([a-f0-9]{6}|[a-f0-9]{3})$"
]

init_jit_stmt = """
if not jitbuilder.initialize_jit():
    exit()
"""

shutdown_jit_stmt = """
jitbuilder.shutdown_jit()
"""

setup = """
import jitbuilder
import re
from pathlib import Path
from regexjit.program{import_suffix} import compile_regex

path = Path("{file}").parent / "./data/blogs.xml"

with open(
    path.absolute(), "rb"
) as data_file:
    data = data_file.read()
{preprocess_data}
regex = "{regex}"

{init_jit}

p = {compile_stmt}
"""

stmt_find_first = """
p.{find_fn}
"""

for regex in regular_expressions:
    runner.timeit(
        f"python_stdlib-({regex})",
        stmt=stmt_find_first.format(find_fn="findall(data)"),
        setup=setup.format(
            import_suffix="",
            regex=regex,
            init_jit="",
            compile_stmt="re.compile(regex)",
            file=__file__,
            preprocess_data="data = data.decode('utf-8')",
        ),
    )
    runner.timeit(
        f"python_jitbuilder-({regex})",
        stmt=stmt_find_first.format(find_fn="find_all(data, 1)"),
        setup=setup.format(
            import_suffix="compiled",
            regex=regex,
            init_jit=init_jit_stmt,
            compile_stmt="compile_regex(regex)",
            file=__file__,
            preprocess_data="",
        ),
        teardown=shutdown_jit_stmt,
    )
    # runner.timeit(
    #     f"python-({regex})",
    #     stmt=stmt_find_first.format(find_fn="find_first(data, 1)"),
    #     setup=setup.format(
    #         import_suffix="",
    #         regex=regex,
    #         init_jit="",
    #         compile_stmt="compile_regex(regex)",
    #         file=__file__,
    #         preprocess_data="",
    #     ),
    # )

stmt_find_all = """
"""

