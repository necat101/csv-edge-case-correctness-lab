#!/usr/bin/env python3
"""
generate_cases.py – CSV edge-case test suite generator

Deterministic test cases covering CSV parsing/writing edge cases.
Ground truth is planted during generation, not inferred post-hoc.

Seed: 42
"""
import json
import pathlib

SEED = 42
CASES_PATH = pathlib.Path(__file__).parent / "cases" / "cases.json"

# Each case: id, category, rows (list of lists), dialect settings, description,
# expected_to_fail_naive (bool), skip_naive_reason
CASES = [
    # plain
    {
        "id": "plain_simple",
        "category": "plain",
        "rows": [["a", "b", "c"], ["1", "2", "3"], ["x", "y", "z"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Plain ASCII, no quoting needed",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "plain_numbers",
        "category": "plain",
        "rows": [["id", "score"], ["1", "95"], ["2", "87"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Simple numeric data",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    # commas in fields
    {
        "id": "comma_in_field",
        "category": "comma_in_field",
        "rows": [["name", "city"], ["Smith, Bob", "New York"], ["Doe, Jane", "Boston"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": 'Comma inside quoted field: "Smith, Bob"',
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    {
        "id": "comma_multi",
        "category": "comma_in_field",
        "rows": [["a", "b"], ["one,two,three", "x"], ["y", "four,five"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Multiple commas in fields",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    # quotes in fields
    {
        "id": "quote_in_field",
        "category": "quotes",
        "rows": [["msg"], ['He said "hi"'], ['She said "bye"']],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Double quotes inside field, must be doubled",
        "naive_split_ok": True,  # split still works, no comma
        "naive_join_ok": False,  # join produces invalid CSV
    },
    {
        "id": "doubled_quotes",
        "category": "quotes",
        "rows": [["text"], ['Say ""hello""'], ['""quoted""']],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Doubled quotes per RFC 4180",
        "naive_split_ok": True,
        "naive_join_ok": False,
    },
    {
        "id": "quote_and_comma",
        "category": "quotes",
        "rows": [["note"], ['He said "hi, there"'], ['"quoted", stuff']],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Quotes AND commas together",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    # newlines in fields
    {
        "id": "newline_lf",
        "category": "newline",
        "rows": [["id", "text"], ["1", "hello\nworld"], ["2", "foo\nbar\nbaz"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal", "lineterminator": "\n"},
        "description": "LF newlines inside quoted fields",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    {
        "id": "newline_crlf_data",
        "category": "newline",
        "rows": [["a", "b"], ["x", "line1\r\nline2"], ["y", "z"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal", "lineterminator": "\n"},
        "description": "CRLF inside field data (not record terminator)",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    # CRLF line endings
    {
        "id": "crlf_records",
        "category": "line_ending",
        "rows": [["a", "b"], ["1", "2"], ["3", "4"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal", "lineterminator": "\r\n"},
        "description": "CRLF record terminators (RFC 4180)",
        "naive_split_ok": True,
        "naive_join_ok": True,  # naive join uses \n, still parses correctly usually
    },
    # empty fields
    {
        "id": "empty_fields",
        "category": "empty",
        "rows": [["a", "b", "c"], ["", "x", ""], ["y", "", "z"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Empty fields in various positions",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "trailing_empty",
        "category": "empty",
        "rows": [["a", "b", "c"], ["1", "2", ""], ["x", "", ""]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Trailing empty fields",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "all_empty",
        "category": "empty",
        "rows": [["", "", ""], ["", "", ""]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "All fields empty",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    # spaces
    {
        "id": "leading_trailing_spaces",
        "category": "spaces",
        "rows": [["a", "b"], ["  foo  ", " bar"], ["baz ", " qux"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal", "skipinitialspace": False},
        "description": "Leading/trailing spaces preserved",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    # unicode / emoji
    {
        "id": "unicode_basic",
        "category": "unicode",
        "rows": [["text"], ["café"], ["naïve"], ["résumé"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "UTF-8 accented characters",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "emoji",
        "category": "unicode",
        "rows": [["msg"], ["hello 👋"], ["🌍 world"], ["test 💯 ok"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Emoji in fields",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "unicode_comma",
        "category": "unicode",
        "rows": [["name"], ["José, María"], ["François, Pierre"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Unicode + comma (needs quoting)",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    # BOM
    {
        "id": "utf8_bom",
        "category": "bom",
        "rows": [["a", "b"], ["1", "2"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "bom": "utf-8-sig",
        "description": "UTF-8 BOM at start of file",
        "naive_split_ok": True,
        "naive_join_ok": True,
        "note": "BOM is a file-level concern, csv.reader handles it if opened with utf-8-sig",
    },
    # semicolon delimiter (locale)
    {
        "id": "semicolon_delim",
        "category": "alt_delimiter",
        "rows": [["name", "score"], ["Alice", "95"], ["Bob", "87"]],
        "dialect": {"delimiter": ";", "quotechar": '"', "quoting": "minimal"},
        "description": "Semicolon delimiter (European locale)",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "naive_reason": "naive_split uses comma",
    },
    {
        "id": "semicolon_with_comma_data",
        "category": "alt_delimiter",
        "rows": [["amount"], ["12,34"], ["56,78"]],
        "dialect": {"delimiter": ";", "quotechar": '"', "quoting": "minimal"},
        "description": "Semicolon-delimited, comma as decimal separator",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "naive_reason": "naive_split uses comma",
    },
    # tab delimiter
    {
        "id": "tab_delim",
        "category": "alt_delimiter",
        "rows": [["a", "b", "c"], ["1", "2", "3"], ["x", "y", "z"]],
        "dialect": {"delimiter": "\t", "quotechar": '"', "quoting": "minimal"},
        "description": "Tab-delimited (TSV)",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "naive_reason": "naive_split uses comma; tsv_split handles this",
        "tsv_ok": True,
    },
    {
        "id": "tab_with_spaces",
        "category": "alt_delimiter",
        "rows": [["name", "value"], ["foo bar", "baz qux"]],
        "dialect": {"delimiter": "\t", "quotechar": '"', "quoting": "minimal"},
        "description": "TSV with spaces (no quoting needed)",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "naive_reason": "wrong delimiter",
        "tsv_ok": True,
    },
    # look-alike values
    {
        "id": "looks_like_numbers",
        "category": "lookalike",
        "rows": [["val"], ["12345"], ["3.14"], ["-42"], ["0"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Strings that look like numbers",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "looks_like_bool_null",
        "category": "lookalike",
        "rows": [["val"], ["true"], ["false"], ["null"], ["TRUE"], ["NULL"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Strings that look like booleans/null",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "looks_like_date",
        "category": "lookalike",
        "rows": [["date"], ["2024-01-15"], ["01/15/2024"], ["15.01.2024"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Date-like strings in various formats",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "looks_like_currency",
        "category": "lookalike",
        "rows": [["price"], ["$19.99"], ["€42,50"], ["¥1000"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Currency strings",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "decimal_comma",
        "category": "lookalike",
        "rows": [["wert"], ["12,34"], ["56,78"]],
        "dialect": {"delimiter": ";", "quotechar": '"', "quoting": "minimal"},
        "description": "Decimal comma values (European) with semicolon delimiter",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "naive_reason": "wrong delimiter",
    },
    # ragged rows
    {
        "id": "ragged_short",
        "category": "ragged",
        "rows": [["a", "b", "c"], ["1", "2"], ["x"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Ragged rows – fewer fields than header",
        "naive_split_ok": True,
        "naive_join_ok": True,
        "note": "csv.reader accepts ragged rows; not an error per se",
    },
    {
        "id": "ragged_long",
        "category": "ragged",
        "rows": [["a", "b"], ["1", "2", "3", "4"], ["x", "y"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Ragged rows – more fields than header",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    # comment/header garbage (bank export style)
    {
        "id": "comment_garbage",
        "category": "garbage",
        "rows": [["a", "b"], ["1", "2"]],
        "prepend_lines": ["# Bank Export", "# Account: 12345", "# Date: 2024-01-01", ""],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Comment/header garbage rows before data (bank export style)",
        "naive_split_ok": True,
        "naive_join_ok": True,
        "note": "csv.reader will parse comment lines as data rows unless filtered",
        "expected_parse_mismatch": True,
    },
    # malformed – unclosed quote
    {
        "id": "malformed_unclosed_quote",
        "category": "malformed",
        "raw_csv": 'a,b\n1,"unclosed\n2,3\n',
        "expected_rows": None,
        "dialect": {"delimiter": ",", "quotechar": '"'},
        "description": "MALFORMED: unclosed quote – should error or produce wrong output",
        "naive_split_ok": False,
        "naive_join_ok": False,
        "expect_parse_fail": True,
    },
    # file-content style
    {
        "id": "file_content",
        "category": "file_content",
        "rows": [["path", "content"], ["/etc/passwd", "root:x:0:0"], ["/tmp/foo", "hello\nworld"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "File paths and file-like content with newlines",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
    # escape hell
    {
        "id": "backslashes",
        "category": "escape",
        "rows": [["path"], ["C:\\Users\\Bob"], ["a\\b\\c"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Backslashes in fields (not special in CSV)",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    {
        "id": "mixed_quotes",
        "category": "escape",
        "rows": [["text"], ['He said "it\'s fine"'], ["'single' and \"double\""]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Mixed single and double quotes",
        "naive_split_ok": True,
        "naive_join_ok": False,
    },
    # pipe in field (naive split on pipe would fail, comma is fine)
    {
        "id": "pipe_char",
        "category": "escape",
        "rows": [["cmd"], ["foo | bar"], ["a | b | c"]],
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "Pipe characters in field (harmless for comma CSV)",
        "naive_split_ok": True,
        "naive_join_ok": True,
    },
    # big-ish case
    {
        "id": "big_100_rows",
        "category": "big",
        "generate": {"rows": 100, "cols": 5},
        "dialect": {"delimiter": ",", "quotechar": '"', "quoting": "minimal"},
        "description": "100 rows × 5 cols, mixed plain/quoted data",
        "naive_split_ok": False,
        "naive_join_ok": False,
    },
]

def expand_generated_cases():
    """Expand cases with 'generate' key into actual rows."""
    import random
    random.seed(SEED)
    out = []
    for case in CASES:
        c = dict(case)
        if "generate" in c:
            gen = c.pop("generate")
            n_rows = gen["rows"]
            n_cols = gen["cols"]
            rows = [[f"r{0}c{col}" for col in range(n_cols)]]
            for r in range(1, n_rows):
                row = []
                for col in range(n_cols):
                    # Mix in some edge cases
                    if random.random() < 0.1:
                        row.append(f"val,{r},{col}")
                    elif random.random() < 0.1:
                        row.append(f'say "hi {r}"')
                    elif random.random() < 0.05:
                        row.append(f"line{r}\nline{col}")
                    else:
                        row.append(f"v{r}_{col}")
                rows.append(row)
            c["rows"] = rows
        out.append(c)
    return out

def main():
    cases = expand_generated_cases()
    out_path = CASES_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(cases)} test cases -> {out_path}")
    # Summary by category
    from collections import Counter
    cats = Counter(c["category"] for c in cases)
    for cat, n in sorted(cats.items()):
        print(f"  {cat:20s} {n} cases")
    # Naive fail count
    naive_fail = sum(1 for c in cases if not c.get("naive_split_ok", True))
    print(f"\nNaive split expected to fail: {naive_fail}/{len(cases)} cases")
    naive_join_fail = sum(1 for c in cases if not c.get("naive_join_ok", True))
    print(f"Naive join expected to fail: {naive_join_fail}/{len(cases)} cases")

if __name__ == "__main__":
    main()
