import pyperf

runner = pyperf.Runner()

regular_expressions = [
    "sc(ored|ared|oring)",
    "a(.*)a",
    "Gutenberg",
    "(?i)Gutenberg",
    "Gutenberg|Good",
    r"\bzero matches\b",
    "and",
    ".*",
    "(?s).*",
    "[a-zA-Z]+ly",
    r"^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,5})$",
    r"^(([0-9]{1})*[- .(]*([0-9]{3})[- .)]*[0-9]{3}[- .]*[0-9]{4})+$",
    r"Afghanistan|Albania|Algeria|Andorra|Angola|Antigua & Barbuda|Argentina|Armenia|Australia|Austria|Azerbaijan|Bahamas|Bahrain|Bangladesh|Barbados|Belarus|Belgium|Belize|Benin|Bhutan|Bolivia|Bosnia Herzegovina|Botswana|Brazil|Brunei|Bulgaria|Burkina|Burundi|Cambodia|Cameroon|Canada|Cape Verde|Central African Rep|Chad|Chile|China|Colombia|Comoros|Congo|Congo|Costa Rica|Croatia|Cuba|Cyprus|Czech Republic|Denmark|Djibouti|Dominica|Dominican Republic|East Timor|Ecuador|Egypt|El Salvador|Equatorial Guinea|Eritrea|Estonia|Ethiopia|Fiji|Finland|France|Gabon|Gambia|Georgia|Germany|Ghana|Greece|Grenada|Guatemala|Guinea|Guinea-Bissau|Guyana|Haiti|Honduras|Hungary|Iceland|India|Indonesia|Iran|Iraq|Ireland|Israel|Italy|Ivory Coast|Jamaica|Japan|Jordan|Kazakhstan|Kenya|Kiribati|North Korea|South Korea|Kosovo|Kuwait|Kyrgyzstan|Laos|Latvia|Lebanon|Lesotho|Liberia|Libya|Liechtenstein|Lithuania|Luxembourg|Macedonia|Madagascar|Malawi|Malaysia|Maldives|Mali|Malta|Marshall Islands|Mauritania|Mauritius|Mexico|Micronesia|Moldova|Monaco|Mongolia|Montenegro|Morocco|Mozambique|Myanmar|Namibia|Nauru|Nepal|Netherlands|New Zealand|Nicaragua|Niger|Nigeria|Norway|Oman|Pakistan|Palau|Panama|Papua New Guinea|Paraguay|Peru|Philippines|Poland|Portugal|Qatar|Romania|Russian Federation|Rwanda|St Kitts & Nevis|St Lucia|Saint Vincent & the Grenadines|Samoa|San Marino|Sao Tome & Principe|Saudi Arabia|Senegal|Serbia|Seychelles|Sierra Leone|Singapore|Slovakia|Slovenia|Solomon Islands|Somalia|South Africa|South Sudan|Spain|Sri Lanka|Sudan|Suriname|Swaziland|Sweden|Switzerland|Syria|Taiwan|Tajikistan|Tanzania|Thailand|Togo|Tonga|Trinidad & Tobago|Tunisia|Turkey|Turkmenistan|Tuvalu|Uganda|Ukraine|United Arab Emirates|United Kingdom|United States|Uruguay|Uzbekistan|Vanuatu|Vatican City|Venezuela|Vietnam|Yemen|Zambia|Zimbabwe",
    r"Project\w+" r"\w+Project\w+",
]

backtracking_killer = b"aaaaaaaaaaaaaaa"

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

path = Path("{file}").parent / "../data/merged.txt"

with open(
    path.absolute(), "rb"
) as data_file:
    data = data_file.read()
{preprocess_data}
regex = "{regex}"

{init_jit}

p = {compile_stmt}
"""

stmt_find_all = """
p.{find_fn}
"""

for regex in regular_expressions:
    runner.timeit(
        f"python-stdlib ({regex})",
        stmt=stmt_find_all.format(find_fn="findall(data)"),
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
        f"python-jitbuilder ({regex})",
        stmt=stmt_find_all.format(find_fn="find_all(data, 1)"),
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

runner.timeit(
    f"python-stdlib ((a*)*c)",
    stmt=stmt_find_all.format(find_fn=f"findall({backtracking_killer})"),
    setup=setup.format(
        import_suffix="",
        regex="(a*)*c",
        init_jit="",
        compile_stmt="re.compile(regex)",
        file=__file__,
        preprocess_data="data = data.decode('utf-8')",
    ),
)
runner.timeit(
    f"python-jitbuilder ((a*)*c)",
    stmt=stmt_find_all.format(find_fn=f"find_all({backtracking_killer}, 1)"),
    setup=setup.format(
        import_suffix="compiled",
        regex="(a*)*c",
        init_jit=init_jit_stmt,
        compile_stmt="compile_regex(regex)",
        file=__file__,
        preprocess_data="",
    ),
    teardown=shutdown_jit_stmt,
)

for regex in regular_expressions:
    runner.timeit(
        f"python ({regex})",
        stmt=stmt_find_all.format(find_fn="find_all(data, 1)"),
        setup=setup.format(
            import_suffix="",
            regex=regex,
            init_jit="",
            compile_stmt="compile_regex(regex)",
            file=__file__,
            preprocess_data="",
        ),
    )

runner.timeit(
        f"python ((a*)*c)",
        stmt=stmt_find_all.format(find_fn=f"find_all({backtracking_killer}, 1)"),
        setup=setup.format(
            import_suffix="",
            regex="(a*)*c",
            init_jit="",
            compile_stmt="compile_regex(regex)",
            file=__file__,
            preprocess_data="",
        ),
    )

