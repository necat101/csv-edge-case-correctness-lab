# CSV Edge-Case Correctness Lab

A tiny, auditable correctness lab about CSV parsing and writing edge cases.

Inspired by HN thread: https://news.ycombinator.com/item?id=43484382 ("a love letter to the CSV format" – https://github.com/medialab/xan/blob/master/docs/LOVE_LETTER.md)

## What HN users were debating

CSV stays popular because it is:
- **Text** – human-readable, grep-able, diff-able
- **Streamable** – read/write row by row, no need to load entire file
- **Appendable** – add rows without rewriting
- **Compact** – less overhead than JSON/XML for tabular data
- **Universally understood** – Excel, Google Sheets, databases, BI tools, scripting languages

But "CSV is simple" does **not** mean "write your own parser with `split(',')`".

The HN thread is full of war stories:
- **Optional quoting, embedded newlines, doubled quotes, BOMs, encodings, locale semicolons** – real pain points
- **Excel and bank/vendor exports** make the format messier than the happy path
- **Enterprise software** (six-figure e-discovery systems, eCAD tools, bank exports) that can't even escape quotes correctly
- **Decimal comma locales** (most of Europe) – CSV with comma delimiter + comma decimal separator = chaos, hence semicolon-delimited "CSV"
- **UTF-8 BOM** – Excel needs it to detect UTF-8, but the Unicode standard recommends against it
- **"CSV is simple"** attracts inexperienced developers who roll their own parser, which then silently corrupts data when a field contains a comma, quote, or newline
- **No strict spec** – RFC 4180 is from 2005, widely ignored, and doesn't cover UTF-8. Real-world CSVs are a family of incompatible de-facto formats

Alternative formats solve some problems but introduce different tradeoffs:
- **TSV** – tabs are rarer in data than commas, but still occur; same quoting problems
- **NDJSON / JSON Lines** – unambiguous, typed, but no header row convention, more verbose, not spreadsheet-friendly
- **Parquet** – columnar, compressed, typed, fast – excellent for analytics, but binary, not human-readable
- **XLSX** – everyone can open it, but it's a ZIP archive containing XML – complex, and Excel has its own "Norway problem" (dates, boolean localization, etc.)

The point of this lab: **test the HN debate in a tiny reproducible way**. CSV is simple and useful when handled by a real parser. Naive comma splitting and naive string joining break on quotes, commas, newlines, BOMs, locale-ish values, and messy producer output.

Python's `csv` module is the **correctness baseline** here. Not fancy – boring and correct.

## What this lab does

- Generates 30-60 deterministic test cases covering CSV edge cases (seed 42)
- Compares 7 methods: Python csv reader/writer (oracle), naive split/join (expected to fail), TSV split, NDJSON baseline, wc/head/tail ergonomics demo
- Validates parsed values exactly match expected – **correctness before speed**
- Measures: wall time, output chars, subprocess count, memory (tracemalloc)
- No external dependencies – Python stdlib only
- No compilers, no package managers, no root installs, no Docker, no downloading repos

## Test case categories

- Plain rows
- Commas inside fields
- Quotes inside fields (doubled per RFC 4180)
- Newlines inside quoted fields (LF and CRLF)
- CRLF vs LF record terminators
- Empty fields, trailing empty fields
- Leading/trailing spaces
- Unicode and emoji
- UTF-8 BOM
- Semicolon-delimited (locale-style)
- Tab-delimited (TSV)
- Look-alike values: numbers, booleans, null, dates, currency, decimal comma
- Ragged rows (short/long)
- Comment/header garbage rows (bank export style)
- Malformed quote case (expected parse failure)
- File-content style values
- Backslashes, mixed quotes, pipe characters
- Big case: 100 rows × 5 cols

## Methods compared

1. **python_csv_reader_baseline** – `csv.reader`, correctness oracle
2. **python_csv_writer_roundtrip** – `csv.writer` + `csv.reader`, must be lossless
3. **naive_split_comma** – `line.split(",")`, expected to fail on quoted commas/newlines
4. **naive_join_comma** – `",".join(...)`, expected to fail when fields need quoting
5. **tsv_simple_split** – tab-split, only for TSV cases without embedded tabs/newlines
6. **ndjson_jsonlines_baseline** – JSON array per line, comparison workflow (not "JSON is better")
7. **wc_head_tail** – `wc -l` row count demo, only if wc is installed, otherwise skip

No xsv, xan, miller, csvkit, pandas, pyarrow – this is intentionally stdlib-only.

## Running it

```bash
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

Output:
- `RESULTS.md` – correctness tables, timing, skip matrix
- `results/results.json` – full machine-readable results

## Results (summary)

See [RESULTS.md](RESULTS.md) for full tables.

Expected outcome: Python `csv` module passes all valid cases. Naive split/join fail on quoted commas, embedded newlines, quotes – exactly as the HN thread warns. TSV split works for tab-delimited clean data. NDJSON roundtrips losslessly but is a different data model.

## Why this lab is intentionally tiny

- A few hundred lines total
- Python stdlib only
- No external downloads
- No package installs
- Deterministic, reproducible (seed 42)
- Correctness before speed
- Honest skip matrix – if a tool isn't installed, skip clearly, don't fake results

The goal is not to prove CSV is good or bad globally. The goal is to test, in a tiny auditable way, the specific claim from the HN debate: **CSV is simple and useful with a real parser, but naive string splitting breaks silently on real-world edge cases**.

## Related

- Previous CSV lab (command-line tools): https://github.com/necat101/csv-commandline-correctness-lab – compares Python csv vs awk/cut/split, HN thread https://news.ycombinator.com/item?id=36501364
- This lab (edge-case parsing): https://github.com/necat101/csv-edge-case-correctness-lab – focuses on CSV format edge cases (quotes, newlines, BOM, locales, ragged rows), HN thread https://news.ycombinator.com/item?id=43484382
- Shell JSON quoting lab: https://github.com/necat101/shell-json-quoting-correctness-lab

---

_Correctness before speed. A fast parser that returns wrong values is worse than a slow parser that returns correct values._
