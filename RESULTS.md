# CSV Edge-Case Correctness – Results

Generated: 2026-06-25T23:54:30Z

## Environment

- Python: 3.12.3
- Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
- wc: wc (GNU coreutils) 9.4
- Cases: 36
- Trials per case: 3

## Correctness Summary

| Method | Pass | Fail | Parse Error | Skipped | Median ms |
|--------|------|------|-------------|---------|-----------|
| python_csv_reader_baseline | 35/36 | 1 | 0 | 0 | 0.1842 |
| python_csv_writer_roundtrip | 35/36 | 1 | 1 | 0 | 0.1419 |
| naive_split_comma | 18/36 | 18 | 0 | 0 | 0.0876 |
| naive_join_comma | 22/36 | 14 | 1 | 0 | 0.0969 |
| tsv_simple_split | 2/2 | 0 | 0 | 34 | 0.0995 |
| ndjson_jsonlines_baseline | 35/35 | 0 | 0 | 1 | 0.2030 |
| wc_head_tail | 1/1 | 0 | 0 | 35 | 8.9441 |

## naive_split_comma – failures by category

| Category | Failures |
|----------|----------|
| alt_delimiter | 4 |
| big | 1 |
| comma_in_field | 2 |
| escape | 1 |
| file_content | 1 |
| lookalike | 2 |
| malformed | 1 |
| newline | 2 |
| quotes | 3 |
| unicode | 1 |

## naive_join_comma – failures by category

| Category | Failures |
|----------|----------|
| alt_delimiter | 3 |
| big | 1 |
| comma_in_field | 2 |
| file_content | 1 |
| lookalike | 1 |
| malformed | 1 |
| newline | 2 |
| quotes | 2 |
| unicode | 1 |

## Test Cases

Total: 36 cases

- alt_delimiter: 4
- big: 1
- bom: 1
- comma_in_field: 2
- empty: 3
- escape: 3
- file_content: 1
- garbage: 1
- line_ending: 1
- lookalike: 5
- malformed: 1
- newline: 2
- plain: 2
- quotes: 3
- ragged: 2
- spaces: 1
- unicode: 3

## Tool versions / skip matrix


| Tool | Status |
|------|--------|
| Python csv | 3.12.3 – baseline |
| wc/head/tail | wc (GNU coreutils) 9.4 |
| xsv / xan / miller / csvkit / pandas | not installed – skipped honestly |

## Commands run

```
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

## Limitations


- Synthetic test cases only, seed 42 – real-world CSVs (bank exports, Excel localizations, etc.) are messier
- No performance / throughput benchmarking – correctness only
- No encoding auto-detection – all test data is UTF-8
- No streaming / large-file testing – biggest case is 100 rows
- csv module dialect settings are explicit per case – real-world CSVs often require sniffing
- NDJSON comparison is illustrative only – different data model (no header row convention)
- wc/head/tail test is a minimal ergonomics demo, not a full CSV tool comparison

---

_Correctness before speed. A fast parser that returns wrong values is worse than a slow parser that returns correct values._
