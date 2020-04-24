use criterion::BenchmarkId;
use criterion::Criterion;
use criterion::{black_box, criterion_group, criterion_main};
use regex::bytes::Regex;
use regex::internal::ExecBuilder;
use std::fs;

fn find_all(c: &mut Criterion) {
    let data = fs::read_to_string("/Users/daytonjallen/regex-jit/bench/data/merged.txt").unwrap();
    let regular_expressions = [
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
        r"Project\w+",
        r"\w+Project\w+",
    ];
    let lot_of_alternations = r"Afghanistan|Albania|Algeria|Andorra|Angola|Antigua & Barbuda|Argentina|Armenia|Australia|Austria|Azerbaijan|Bahamas|Bahrain|Bangladesh|Barbados|Belarus|Belgium|Belize|Benin|Bhutan|Bolivia|Bosnia Herzegovina|Botswana|Brazil|Brunei|Bulgaria|Burkina|Burundi|Cambodia|Cameroon|Canada|Cape Verde|Central African Rep|Chad|Chile|China|Colombia|Comoros|Congo|Congo|Costa Rica|Croatia|Cuba|Cyprus|Czech Republic|Denmark|Djibouti|Dominica|Dominican Republic|East Timor|Ecuador|Egypt|El Salvador|Equatorial Guinea|Eritrea|Estonia|Ethiopia|Fiji|Finland|France|Gabon|Gambia|Georgia|Germany|Ghana|Greece|Grenada|Guatemala|Guinea|Guinea-Bissau|Guyana|Haiti|Honduras|Hungary|Iceland|India|Indonesia|Iran|Iraq|Ireland|Israel|Italy|Ivory Coast|Jamaica|Japan|Jordan|Kazakhstan|Kenya|Kiribati|North Korea|South Korea|Kosovo|Kuwait|Kyrgyzstan|Laos|Latvia|Lebanon|Lesotho|Liberia|Libya|Liechtenstein|Lithuania|Luxembourg|Macedonia|Madagascar|Malawi|Malaysia|Maldives|Mali|Malta|Marshall Islands|Mauritania|Mauritius|Mexico|Micronesia|Moldova|Monaco|Mongolia|Montenegro|Morocco|Mozambique|Myanmar|Namibia|Nauru|Nepal|Netherlands|New Zealand|Nicaragua|Niger|Nigeria|Norway|Oman|Pakistan|Palau|Panama|Papua New Guinea|Paraguay|Peru|Philippines|Poland|Portugal|Qatar|Romania|Russian Federation|Rwanda|St Kitts & Nevis|St Lucia|Saint Vincent & the Grenadines|Samoa|San Marino|Sao Tome & Principe|Saudi Arabia|Senegal|Serbia|Seychelles|Sierra Leone|Singapore|Slovakia|Slovenia|Solomon Islands|Somalia|South Africa|South Sudan|Spain|Sri Lanka|Sudan|Suriname|Swaziland|Sweden|Switzerland|Syria|Taiwan|Tajikistan|Tanzania|Thailand|Togo|Tonga|Trinidad & Tobago|Tunisia|Turkey|Turkmenistan|Tuvalu|Uganda|Ukraine|United Arab Emirates|United Kingdom|United States|Uruguay|Uzbekistan|Vanuatu|Vatican City|Venezuela|Vietnam|Yemen|Zambia|Zimbabwe";
    
    let mut group = c.benchmark_group("find_all");
    for regex in regular_expressions.iter() {
        let re = Regex::new(regex).unwrap();
        let re_nfa = ExecBuilder::new(regex)
            .nfa()
            .build()
            .map(|e| e.into_byte_regex())
            .unwrap();
        group.bench_with_input(
            BenchmarkId::from_parameter(format!("normal-{}", regex)),
            regex,
            |b, &regex| {
                b.iter(|| re.find_iter(&data.as_bytes()).count());
            },
        );

        group.bench_with_input(
            BenchmarkId::from_parameter(format!("nfa-{}", regex)),
            regex,
            |b, &regex| {
                b.iter(|| re_nfa.find_iter(&data.as_bytes()).count());
            },
        );
    }

    group.bench_with_input(
        BenchmarkId::from_parameter(format!("normal-{}", "(a*)*c")),
        regex,
        |b, &regex| {
            b.iter(|| re.find_iter("aaaaaaaaaaaaaaa".as_bytes()).count());
        },
    );

    group.bench_with_input(
        BenchmarkId::from_parameter(format!("nfa-{}", "(a*)*c")),
        regex,
        |b, &regex| {
            b.iter(|| re_nfa.find_iter("aaaaaaaaaaaaaaa".as_bytes()).count());
        },
    );
    
    group.sample_size(15);
    group.bench_with_input(
        BenchmarkId::from_parameter(format!("normal-{}", lot_of_alternations)),
        regex,
        |b, &regex| {
            b.iter(|| re.find_iter(&data.as_bytes()).count());
        },
    );

    group.bench_with_input(
        BenchmarkId::from_parameter(format!("nfa-{}", lot_of_alternations)),
        regex,
        |b, &regex| {
            b.iter(|| re_nfa.find_iter(&data.as_bytes()).count());
        },
    );
    group.finish();
}

criterion_group!(benches, find_all);
criterion_main!(benches);
