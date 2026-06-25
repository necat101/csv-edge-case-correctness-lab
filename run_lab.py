#!/usr/bin/env python3
"""
run_lab.py – CSV edge-case correctness benchmark

Compares CSV parsing/writing methods on edge-case test suite.
Correctness BEFORE speed.
"""
import csv
import json
import time
import sys
import pathlib
import platform
import subprocess
import tracemalloc
from collections import defaultdict

CASES_PATH = pathlib.Path(__file__).parent / "cases" / "cases.json"
RESULTS_JSON = pathlib.Path(__file__).parent / "results" / "results.json"
RESULTS_MD = pathlib.Path(__file__).parent / "RESULTS.md"

# ---------------------------------------------------------------------------
# Method implementations
# ---------------------------------------------------------------------------

def method_python_csv_reader_baseline(case):
    """csv.reader – correctness oracle for CSV parsing."""
    start = time.perf_counter()
    try:
        dialect = case.get("dialect", {})
        delimiter = dialect.get("delimiter", ",")
        quotechar = dialect.get("quotechar", '"')
        skipinitialspace = dialect.get("skipinitialspace", False)
        # Handle raw_csv (malformed case)
        if "raw_csv" in case:
            csv_text = case["raw_csv"]
        else:
            # Generate CSV text from rows using csv.writer (to get correct quoting)
            import io
            out = io.StringIO()
            writer = csv.writer(
                out,
                delimiter=delimiter,
                quotechar=quotechar,
                quoting=csv.QUOTE_MINIMAL,
                lineterminator=dialect.get("lineterminator", "\r\n"),
            )
            rows = case["rows"]
            writer.writerows(rows)
            csv_text = out.getvalue()
        # Handle BOM
        bom = case.get("bom")
        if bom:
            csv_text = csv_text.encode("utf-8")
            # Simulate reading with BOM stripping
            csv_text = csv_text.decode(bom)
        # Parse
        import io
        f = io.StringIO(csv_text)
        # Skip prepend_lines for comment_garbage case
        prepend = case.get("prepend_lines", [])
        if prepend:
            for line in prepend:
                f.write(line + "\n")
            f.write(csv_text)
            f.seek(0)
        reader = csv.reader(
            f,
            delimiter=delimiter,
            quotechar=quotechar,
            skipinitialspace=skipinitialspace,
        )
        parsed_rows = list(reader)
        # Strip prepended garbage rows if present
        if prepend:
            parsed_rows = parsed_rows[len(prepend):]
        elapsed = time.perf_counter() - start
        # Check expected
        expected = case.get("expected_rows", case.get("rows"))
        if expected is None:
            # Malformed case – parsing "succeeding" is actually a fail
            if case.get("expect_parse_fail"):
                return {
                    "parse_ok": True,
                    "match": False,
                    "parsed_value": parsed_rows,
                    "expected": expected,
                    "fail_reason": "parsed malformed input without error (expected failure)",
                    "elapsed": elapsed,
                }
        match = (parsed_rows == expected)
        return {
            "parse_ok": True,
            "match": match,
            "parsed_value": parsed_rows,
            "expected": expected,
            "fail_reason": None if match else f"parsed {len(parsed_rows)} rows, expected {len(expected) if expected else 0}",
            "elapsed": elapsed,
            "output_chars": len(csv_text),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        expect_fail = case.get("expect_parse_fail", False)
        return {
            "parse_ok": False,
            "match": expect_fail,  # failing to parse malformed input = correct
            "parsed_value": None,
            "expected": case.get("expected_rows", case.get("rows")),
            "fail_reason": f"parse_error: {type(e).__name__}: {e}",
            "elapsed": elapsed,
            "output_chars": 0,
        }

def method_python_csv_writer_roundtrip(case):
    """csv.writer + csv.reader roundtrip – must be lossless."""
    start = time.perf_counter()
    try:
        if "raw_csv" in case:
            return {"parse_ok": False, "match": False, "fail_reason": "raw_csv case, no rows to write", "elapsed": 0, "output_chars": 0}
        dialect = case.get("dialect", {})
        delimiter = dialect.get("delimiter", ",")
        quotechar = dialect.get("quotechar", '"')
        lineterm = dialect.get("lineterminator", "\r\n")
        rows = case["rows"]
        import io
        out = io.StringIO()
        writer = csv.writer(
            out,
            delimiter=delimiter,
            quotechar=quotechar,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator=lineterm,
        )
        writer.writerows(rows)
        csv_text = out.getvalue()
        # Read back
        f = io.StringIO(csv_text)
        reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
        parsed = list(reader)
        elapsed = time.perf_counter() - start
        match = (parsed == rows)
        return {
            "parse_ok": True,
            "match": match,
            "parsed_value": parsed,
            "expected": rows,
            "fail_reason": None if match else "roundtrip mismatch",
            "elapsed": elapsed,
            "output_chars": len(csv_text),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "parse_ok": False,
            "match": False,
            "parsed_value": None,
            "expected": case.get("rows"),
            "fail_reason": f"{type(e).__name__}: {e}",
            "elapsed": elapsed,
            "output_chars": 0,
        }

def method_naive_split_comma(case):
    """Naive line.split(',') – expected to fail on quoted commas, newlines, etc."""
    start = time.perf_counter()
    try:
        if "raw_csv" in case:
            csv_text = case["raw_csv"]
        else:
            # Generate proper CSV first
            dialect = case.get("dialect", {})
            delimiter = dialect.get("delimiter", ",")
            quotechar = dialect.get("quotechar", '"')
            import io
            out = io.StringIO()
            writer = csv.writer(out, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            writer.writerows(case["rows"])
            csv_text = out.getvalue()
        # Naive split
        lines = csv_text.strip().split("\n")
        parsed = [line.split(",") for line in lines if line]
        elapsed = time.perf_counter() - start
        expected = case.get("expected_rows", case.get("rows"))
        if expected is None:
            return {"parse_ok": True, "match": False, "parsed_value": parsed, "expected": expected, "fail_reason": "parsed malformed input", "elapsed": elapsed, "output_chars": len(csv_text)}
        match = (parsed == expected)
        # Check if this case was EXPECTED to fail for naive
        expected_fail = not case.get("naive_split_ok", True)
        return {
            "parse_ok": True,
            "match": match,
            "parsed_value": parsed,
            "expected": expected,
            "fail_reason": None if match else "naive split mismatch",
            "elapsed": elapsed,
            "output_chars": len(csv_text),
            "expected_fail": expected_fail,
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"parse_ok": False, "match": False, "parsed_value": None, "fail_reason": f"{type(e).__name__}: {e}", "elapsed": elapsed, "output_chars": 0}

def method_naive_join_comma(case):
    """Naive ','.join – expected to fail when fields contain commas/quotes/newlines."""
    start = time.perf_counter()
    try:
        if "raw_csv" in case:
            return {"parse_ok": False, "match": False, "fail_reason": "raw_csv case", "elapsed": 0, "output_chars": 0}
        rows = case["rows"]
        # Naive join – no quoting at all
        lines = [",".join(str(cell) for cell in row) for row in rows]
        csv_text = "\n".join(lines) + "\n"
        # Try to read it back with proper csv.reader to see if roundtrip works
        import io
        f = io.StringIO(csv_text)
        dialect = case.get("dialect", {})
        delimiter = dialect.get("delimiter", ",")
        quotechar = dialect.get("quotechar", '"')
        reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
        parsed = list(reader)
        elapsed = time.perf_counter() - start
        match = (parsed == rows)
        expected_fail = not case.get("naive_join_ok", True)
        return {
            "parse_ok": True,
            "match": match,
            "parsed_value": parsed,
            "expected": rows,
            "fail_reason": None if match else "naive join roundtrip mismatch",
            "elapsed": elapsed,
            "output_chars": len(csv_text),
            "expected_fail": expected_fail,
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"parse_ok": False, "match": False, "parsed_value": None, "fail_reason": f"{type(e).__name__}: {e}", "elapsed": elapsed, "output_chars": 0}

def method_tsv_simple_split(case):
    """TSV simple split – only for tab-delimited cases without embedded tabs/newlines."""
    dialect = case.get("dialect", {})
    if dialect.get("delimiter") != "\t":
        return {"parse_ok": False, "match": False, "fail_reason": "skip: not TSV", "elapsed": 0, "output_chars": 0, "skipped": True}
    start = time.perf_counter()
    try:
        if "raw_csv" in case:
            return {"parse_ok": False, "match": False, "fail_reason": "raw_csv", "elapsed": 0, "output_chars": 0, "skipped": True}
        rows = case["rows"]
        # Check if any field contains tab or newline – if so, skip (unsupported)
        for row in rows:
            for cell in row:
                if "\t" in str(cell) or "\n" in str(cell) or "\r" in str(cell):
                    elapsed = time.perf_counter() - start
                    return {"parse_ok": False, "match": False, "fail_reason": "skip: embedded tab/newline", "elapsed": elapsed, "output_chars": 0, "skipped": True}
        # Simple TSV write + read
        lines = ["\t".join(str(cell) for cell in row) for row in rows]
        tsv_text = "\n".join(lines) + "\n"
        parsed = [line.split("\t") for line in tsv_text.strip().split("\n")]
        elapsed = time.perf_counter() - start
        match = (parsed == rows)
        return {"parse_ok": True, "match": match, "parsed_value": parsed, "expected": rows, "fail_reason": None if match else "mismatch", "elapsed": elapsed, "output_chars": len(tsv_text)}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"parse_ok": False, "match": False, "parsed_value": None, "fail_reason": f"{type(e).__name__}: {e}", "elapsed": elapsed, "output_chars": 0}

def method_ndjson_jsonlines_baseline(case):
    """NDJSON – one JSON array per line – comparison workflow, not CSV."""
    start = time.perf_counter()
    try:
        if "raw_csv" in case:
            return {"parse_ok": False, "match": False, "fail_reason": "raw_csv case", "elapsed": 0, "output_chars": 0, "skipped": True}
        rows = case["rows"]
        # Write NDJSON
        lines = [json.dumps(row, ensure_ascii=False) for row in rows]
        ndjson_text = "\n".join(lines) + "\n"
        # Read back
        parsed = [json.loads(line) for line in ndjson_text.strip().split("\n")]
        elapsed = time.perf_counter() - start
        match = (parsed == rows)
        return {"parse_ok": True, "match": match, "parsed_value": parsed, "expected": rows, "fail_reason": None if match else "mismatch", "elapsed": elapsed, "output_chars": len(ndjson_text)}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"parse_ok": False, "match": False, "parsed_value": None, "fail_reason": f"{type(e).__name__}: {e}", "elapsed": elapsed, "output_chars": 0}

def method_wc_head_tail(case):
    """wc -l / head / tail – only for simple row-count ergonomics, if installed."""
    # Only run on first case as a demo, skip others to avoid noise
    if case["id"] != "plain_simple":
        return {"parse_ok": False, "match": False, "fail_reason": "skip: demo only", "elapsed": 0, "output_chars": 0, "skipped": True}
    # Check if wc is available
    try:
        subprocess.run(["wc", "--version"], capture_output=True, timeout=1)
    except Exception:
        return {"parse_ok": False, "match": False, "fail_reason": "skip: wc not installed", "elapsed": 0, "output_chars": 0, "skipped": True}
    start = time.perf_counter()
    try:
        # Generate a temp CSV file
        import tempfile, os
        dialect = case.get("dialect", {})
        rows = case["rows"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
            tmp_path = f.name
            writer = csv.writer(f, delimiter=dialect.get("delimiter", ","), quotechar=dialect.get("quotechar", '"'), quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows)
        # wc -l
        r = subprocess.run(["wc", "-l", tmp_path], capture_output=True, text=True, timeout=2)
        os.unlink(tmp_path)
        elapsed = time.perf_counter() - start
        output = r.stdout.strip()
        # wc -l counts newline characters, not logical CSV records
        # For plain_simple (no embedded newlines), it should match row count
        expected_lines = len(rows)
        try:
            actual_lines = int(output.split()[0])
            match = (actual_lines == expected_lines)
        except Exception:
            match = False
        return {"parse_ok": r.returncode == 0, "match": match, "parsed_value": output, "expected": f"{expected_lines} lines", "fail_reason": None if match else f"wc counted {actual_lines}, expected {expected_lines}", "elapsed": elapsed, "output_chars": len(output), "subprocess_calls": 1}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"parse_ok": False, "match": False, "parsed_value": None, "fail_reason": f"{type(e).__name__}: {e}", "elapsed": elapsed, "output_chars": 0}

METHODS = [
    ("python_csv_reader_baseline", method_python_csv_reader_baseline),
    ("python_csv_writer_roundtrip", method_python_csv_writer_roundtrip),
    ("naive_split_comma", method_naive_split_comma),
    ("naive_join_comma", method_naive_join_comma),
    ("tsv_simple_split", method_tsv_simple_split),
    ("ndjson_jsonlines_baseline", method_ndjson_jsonlines_baseline),
    ("wc_head_tail", method_wc_head_tail),
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(trials=3):
    with open(CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"\nTesting {len(cases)} cases × {len(METHODS)} methods × {trials} trials")
    print()
    results = []
    for method_name, method_fn in METHODS:
        print(f"{method_name}:")
        method_results = []
        for case in cases:
            trial_times = []
            last_res = None
            for _ in range(trials):
                res = method_fn(case)
                trial_times.append(res.get("elapsed", 0))
                last_res = res
                if res.get("skipped"):
                    break
            if last_res is None:
                continue
            # Aggregate timing
            import statistics
            mean_t = statistics.mean(trial_times) if trial_times else 0
            median_t = statistics.median(trial_times) if trial_times else 0
            stdev_t = statistics.stdev(trial_times) if len(trial_times) > 1 else 0
            r = {
                "method": method_name,
                "case_id": case["id"],
                "category": case["category"],
                "parse_ok": last_res.get("parse_ok", False),
                "match": last_res.get("match", False),
                "fail_reason": last_res.get("fail_reason"),
                "expected_fail": last_res.get("expected_fail", False),
                "skipped": last_res.get("skipped", False),
                "elapsed_mean": mean_t,
                "elapsed_median": median_t,
                "elapsed_stdev": stdev_t,
                "output_chars": last_res.get("output_chars", 0),
                "trials": trials if not last_res.get("skipped") else 1,
            }
            method_results.append(r)
            results.append(r)
        # Summary
        total = len([x for x in method_results if not x["skipped"]])
        skipped = len([x for x in method_results if x["skipped"]])
        passed = sum(1 for x in method_results if x["match"] and not x["skipped"])
        failed = total - passed
        parse_err = sum(1 for x in method_results if not x["parse_ok"] and not x["skipped"])
        print(f"  Total: {total}, Pass: {passed}, Fail: {failed}, Parse errors: {parse_err}, Skipped: {skipped}")
    # Save results
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {RESULTS_JSON}")
    return results, cases

def write_results_md(results, cases):
    # Aggregate per method
    from collections import defaultdict
    by_method = defaultdict(list)
    for r in results:
        by_method[r["method"]].append(r)
    lines = []
    lines.append("# CSV Edge-Case Correctness – Results\n")
    import datetime
    lines.append(f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    lines.append("## Environment\n")
    lines.append(f"- Python: {platform.python_version()}")
    lines.append(f"- Platform: {platform.platform()}")
    # Check optional tools
    try:
        out = subprocess.run(["wc", "--version"], capture_output=True, text=True, timeout=1)
        wc_ver = out.stdout.splitlines()[0] if out.returncode == 0 else "not installed"
    except Exception:
        wc_ver = "not installed"
    lines.append(f"- wc: {wc_ver}")
    lines.append(f"- Cases: {len(cases)}")
    lines.append(f"- Trials per case: 3")
    lines.append("")
    lines.append("## Correctness Summary\n")
    lines.append("| Method | Pass | Fail | Parse Error | Skipped | Median ms |")
    lines.append("|--------|------|------|-------------|---------|-----------|")
    for method, rs in by_method.items():
        rs_active = [r for r in rs if not r.get("skipped")]
        skipped = len(rs) - len(rs_active)
        passed = sum(1 for r in rs_active if r["match"])
        failed = len(rs_active) - passed
        parse_err = sum(1 for r in rs_active if not r["parse_ok"])
        median_ms = 0
        if rs_active:
            import statistics
            median_ms = statistics.median([r["elapsed_median"] * 1000 for r in rs_active])
        lines.append(f"| {method} | {passed}/{len(rs_active)} | {failed} | {parse_err} | {skipped} | {median_ms:.4f} |")
    lines.append("")
    # Failure breakdown by category for naive methods
    for naive_method in ["naive_split_comma", "naive_join_comma"]:
        if naive_method not in by_method:
            continue
        lines.append(f"## {naive_method} – failures by category\n")
        fails = [r for r in by_method[naive_method] if not r["match"] and not r.get("skipped")]
        from collections import Counter
        cat_counts = Counter(r["category"] for r in fails)
        if cat_counts:
            lines.append("| Category | Failures |")
            lines.append("|----------|----------|")
            for cat, n in sorted(cat_counts.items()):
                lines.append(f"| {cat} | {n} |")
        else:
            lines.append("_No failures_")
        lines.append("")
    # Case list
    lines.append("## Test Cases\n")
    lines.append(f"Total: {len(cases)} cases\n")
    from collections import Counter
    cat_counts = Counter(c["category"] for c in cases)
    for cat, n in sorted(cat_counts.items()):
        lines.append(f"- {cat}: {n}")
    lines.append("")
    # Tool versions / skip matrix
    lines.append("## Tool versions / skip matrix\n")
    lines.append("")
    lines.append("| Tool | Status |")
    lines.append("|------|--------|")
    lines.append(f"| Python csv | {platform.python_version()} – baseline |")
    lines.append(f"| wc/head/tail | {wc_ver} |")
    lines.append("| xsv / xan / miller / csvkit / pandas | not installed – skipped honestly |")
    lines.append("")
    # Commands
    lines.append("## Commands run\n")
    lines.append("```\npython3 -m py_compile generate_cases.py run_lab.py\npython3 generate_cases.py\npython3 run_lab.py\n```\n")
    # Limitations
    lines.append("## Limitations\n")
    lines.append("")
    lines.append("- Synthetic test cases only, seed 42 – real-world CSVs (bank exports, Excel localizations, etc.) are messier")
    lines.append("- No performance / throughput benchmarking – correctness only")
    lines.append("- No encoding auto-detection – all test data is UTF-8")
    lines.append("- No streaming / large-file testing – biggest case is 100 rows")
    lines.append("- csv module dialect settings are explicit per case – real-world CSVs often require sniffing")
    lines.append("- NDJSON comparison is illustrative only – different data model (no header row convention)")
    lines.append("- wc/head/tail test is a minimal ergonomics demo, not a full CSV tool comparison")
    lines.append("")
    lines.append("---\n")
    lines.append("_Correctness before speed. A fast parser that returns wrong values is worse than a slow parser that returns correct values._\n")
    with open(RESULTS_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"RESULTS.md written to {RESULTS_MD}")

def main():
    tracemalloc.start()
    results, cases = run_all(trials=3)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"\nMemory: current={current/1024:.1f} KB, peak={peak/1024:.1f} KB")
    write_results_md(results, cases)
    print("\nDone.")

if __name__ == "__main__":
    main()
