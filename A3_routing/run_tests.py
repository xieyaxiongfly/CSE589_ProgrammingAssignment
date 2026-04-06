#!/usr/bin/env python3
"""
run_tests.py — batch test runner for the routing simulator

Usage:
    python run_tests.py ALGORITHM [event_or_dir ...] [--timeout SECONDS]

    ALGORITHM   : DV | DV_SH | LS | GENERIC
                  Long aliases DISTANCE_VECTOR, DISTANCE_VECTOR_SPLIT_HORIZON,
                  and LINK_STATE are still accepted.
    event_or_dir: one or more .event files or directories containing them
                  (defaults to events/ directory)

Examples:
    python run_tests.py LS
    python run_tests.py DV events/demo.event
    python run_tests.py DV_SH events/testing_suite/
    python run_tests.py LS events/ --timeout 180

Exit code: 0 if all tests pass, 1 if any fail.
A detailed log is always saved to output/test_results_<ALGORITHM>.txt
"""

import os
import re
import sys
import subprocess
from datetime import datetime

# ── ANSI colours (terminal only) ─────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _c(text, *codes):
    if sys.stdout.isatty():
        return "".join(codes) + text + RESET
    return text


# ── Event collection ─────────────────────────────────────────────────────────

def collect_events(paths):
    result = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(".event"):
            result.append(p)
        elif os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith(".event"):
                    result.append(os.path.join(p, f))
        else:
            print(_c(f"Warning: {p!r} is not a .event file or directory — skipped", YELLOW))
    return result


# ── Output parser ─────────────────────────────────────────────────────────────

def parse_output(text):
    """
    Parse simulation output into structured results.

    Returns a dict:
        messages  : int   — total routing messages sent
        checks    : list of dicts, each:
            time      : str   — e.g. "800"
            kind      : str   — "DRAW_PATH" or "DRAW_TREE"
            args      : str   — e.g. "0 → 1" or "from 0"
            passed    : bool
            correct   : str   — correct path/length line
            student   : str   — student path/length line
    """
    messages = 0
    m = re.search(r"Total messages sent:\s*(\d+)", text)
    if m:
        messages = int(m.group(1))

    checks = []
    lines = text.splitlines()

    # Track the current DRAW command context
    current_cmd = None   # {"time", "kind", "args"}
    current_src_dst = None  # for DRAW_TREE sub-pairs

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect DRAW_PATH / DRAW_TREE banner lines like "[T=800   ] DRAW_PATH 0 1"
        m = re.match(r"\[T=(\d+)\s*\]\s+(DRAW_PATH|DRAW_TREE)\s+(.*)", line)
        if m:
            current_cmd = {
                "time": m.group(1),
                "kind": m.group(2),
                "args": m.group(3).strip(),
            }
            current_src_dst = None
            i += 1
            continue

        # DRAW_TREE sub-pair: "from 0 to 3:"
        m2 = re.match(r"from\s+(\S+)\s+to\s+(\S+):", line)
        if m2 and current_cmd and current_cmd["kind"] == "DRAW_TREE":
            current_src_dst = f"{m2.group(1)} → {m2.group(2)}"
            i += 1
            continue

        # Correct/student path lines
        correct_line = ""
        student_line = ""
        if line.startswith("correct_path:") and i + 1 < len(lines):
            correct_line = line.strip()
            student_line = lines[i + 1].strip() if lines[i + 1].startswith("student_path:") else ""

        # Verdict line
        if "student's solution is correct!" in line or "student's solution is incorrect!" in line:
            passed = "incorrect" not in line

            if current_cmd:
                if current_cmd["kind"] == "DRAW_PATH":
                    label = "→".join(current_cmd["args"].split())
                else:
                    # DRAW_TREE: use sub-pair if available, else whole tree
                    src = current_cmd["args"].split()[0] if current_cmd["args"] else "?"
                    label = current_src_dst if current_src_dst else f"tree from {src}"
                    current_src_dst = None  # reset after consuming

                # Look back a few lines for correct/student_path if not captured yet
                if not correct_line:
                    for back in range(1, 6):
                        if i - back >= 0 and lines[i - back].startswith("correct_path:"):
                            correct_line = lines[i - back].strip()
                            if i - back + 1 < len(lines):
                                student_line = lines[i - back + 1].strip()
                            break

                checks.append({
                    "time":    current_cmd["time"],
                    "kind":    current_cmd["kind"],
                    "label":   label,
                    "passed":  passed,
                    "correct": correct_line,
                    "student": student_line,
                })

        i += 1

    return {"messages": messages, "checks": checks}


# ── Run one event file ────────────────────────────────────────────────────────

def run_event(algorithm, event_file, root, timeout_s):
    cmd = [sys.executable, os.path.join(root, "sim.py"), algorithm, event_file]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=root, timeout=timeout_s
        )
        combined = result.stdout + result.stderr
        timed_out = False
    except subprocess.TimeoutExpired:
        combined = ""
        timed_out = True

    parsed = parse_output(combined)
    parsed["timed_out"] = timed_out
    parsed["raw"] = combined
    return parsed


# ── Report writers ────────────────────────────────────────────────────────────

def format_check(chk, indent="    "):
    status = "PASS" if chk["passed"] else "FAIL"
    line = f"{indent}[T={chk['time']:>6}] {chk['kind']:<10} {chk['label']:<20}  {status}"
    detail = []
    if not chk["passed"]:
        if chk["correct"]:
            detail.append(f"{indent}  {chk['correct']}")
        if chk["student"]:
            detail.append(f"{indent}  {chk['student']}")
    return line, detail


def write_log(log_path, algorithm, results, started_at, timeout_s):
    """Write detailed plain-text log to file."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    lines = []
    sep = "=" * 72

    lines.append(sep)
    lines.append(f"  Routing Simulator Test Report")
    lines.append(f"  Algorithm : {algorithm}")
    lines.append(f"  Date/Time : {started_at}")
    lines.append(sep)
    lines.append("")

    total_pass = total_fail = total_msgs = 0
    file_verdicts = []

    for label, parsed in results:
        checks  = parsed["checks"]
        msgs    = parsed["messages"]
        passed  = sum(1 for c in checks if c["passed"])
        failed  = sum(1 for c in checks if not c["passed"])
        total_pass += passed
        total_fail += failed
        total_msgs += msgs

        if parsed["timed_out"]:
            verdict = "TIMEOUT"
        elif failed > 0:
            verdict = "FAIL"
        elif len(checks) == 0:
            verdict = "NO CHECKS"
        else:
            verdict = "PASS"

        file_verdicts.append((label, verdict, passed, failed, msgs))

    # ── Summary table ──────────────────────────────────────────────────────
    lines.append("SUMMARY")
    lines.append("-" * 72)
    lines.append(f"  {'File':<44} {'Msgs':>6}  {'Checks':>9}  Result")
    lines.append(f"  {'-'*44} {'-'*6}  {'-'*9}  ------")
    for label, verdict, passed, failed, msgs in file_verdicts:
        chk_str = f"{passed}/{passed+failed}"
        lines.append(f"  {label:<44} {msgs:>6}  {chk_str:>9}  {verdict}")
    lines.append(f"  {'-'*44} {'-'*6}  {'-'*9}  ------")
    total_chk = total_pass + total_fail
    overall = "ALL PASS" if total_fail == 0 else f"{total_fail} FAILED"
    tot_str = f"{total_pass}/{total_chk}"
    lines.append(f"  {'TOTAL':<44} {total_msgs:>6}  {tot_str:>9}  {overall}")
    lines.append("")

    # ── Per-file detail ────────────────────────────────────────────────────
    lines.append("DETAIL")
    lines.append("-" * 72)
    for (label, parsed), (_, verdict, passed, failed, msgs) in zip(results, file_verdicts):
        lines.append("")
        lines.append(f"  [{verdict}]  {label}")
        lines.append(f"  Messages sent: {msgs}")
        if parsed["timed_out"]:
            lines.append(f"  TIMEOUT — simulation did not finish within {timeout_s} s")
            continue
        if not parsed["checks"]:
            lines.append("  No DRAW_PATH / DRAW_TREE checks in this file.")
            continue
        for chk in parsed["checks"]:
            row, detail = format_check(chk, indent="    ")
            lines.append(row)
            lines.extend(detail)

    lines.append("")
    lines.append(sep)
    lines.append(f"  Overall result: {overall}  ({total_pass}/{total_chk} checks, {total_msgs} messages)")
    lines.append(sep)

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    timeout_s = 60

    if "--timeout" in args:
        idx = args.index("--timeout")
        try:
            timeout_s = int(args[idx + 1])
        except (IndexError, ValueError):
            print("Invalid --timeout value.")
            print(__doc__)
            sys.exit(1)
        del args[idx:idx + 2]

    valid_algorithms = [
        "GENERIC",
        "DV",
        "DISTANCE_VECTOR",
        "DV_SH",
        "DISTANCE_VECTOR_SPLIT_HORIZON",
        "LS",
        "LINK_STATE",
    ]
    if not args or args[0] not in valid_algorithms:
        print(__doc__)
        sys.exit(1)

    algorithm = args[0]
    targets   = args[1:] if len(args) > 1 else ["events"]
    root      = os.path.dirname(os.path.abspath(__file__))
    targets   = [t if os.path.isabs(t) else os.path.join(root, t) for t in targets]

    events = collect_events(targets)
    if not events:
        print(_c("No .event files found.", YELLOW))
        sys.exit(1)

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(_c(f"\nRunning {len(events)} test(s) with {algorithm} (timeout={timeout_s}s)\n", BOLD))

    # Column header
    W_FILE, W_MSG, W_CHK = 44, 7, 9
    hdr = f"  {'File':<{W_FILE}} {'Msgs':>{W_MSG}}  {'Checks':>{W_CHK}}  Result"
    div = "  " + "-" * (W_FILE + W_MSG + W_CHK + 14)
    print(hdr)
    print(div)

    results     = []
    total_pass  = 0
    total_fail  = 0
    total_msgs  = 0
    any_fail    = False

    for event_file in events:
        label  = os.path.relpath(event_file, root)
        parsed = run_event(algorithm, event_file, root, timeout_s)
        results.append((label, parsed))

        checks = parsed["checks"]
        msgs   = parsed["messages"]
        passed = sum(1 for c in checks if c["passed"])
        failed = sum(1 for c in checks if not c["passed"])
        total_pass += passed
        total_fail += failed
        total_msgs += msgs

        if parsed["timed_out"]:
            verdict = _c("TIMEOUT", RED, BOLD)
            any_fail = True
        elif failed > 0:
            verdict = _c("FAIL", RED, BOLD)
            any_fail = True
        elif len(checks) == 0:
            verdict = _c("NO CHECKS", YELLOW)
        else:
            verdict = _c("PASS", GREEN, BOLD)

        chk_str = f"{passed}/{passed+failed}"
        print(f"  {label:<{W_FILE}} {msgs:>{W_MSG}}  {chk_str:>{W_CHK}}  {verdict}")

    # Totals row
    print(div)
    total_chk = total_pass + total_fail
    tot_chk_str = f"{total_pass}/{total_chk}"
    overall_str = "ALL PASS" if not any_fail else f"{total_fail} FAILED"
    overall_col = _c(overall_str, GREEN if not any_fail else RED, BOLD)
    print(f"  {'TOTAL':<{W_FILE}} {total_msgs:>{W_MSG}}  {tot_chk_str:>{W_CHK}}  {overall_col}")

    # ── Inline failure detail (terminal) ──────────────────────────────────
    if any_fail:
        print()
        print(_c("  FAILURES", RED, BOLD))
        print("  " + "-" * 50)
        for label, parsed in results:
            if parsed["timed_out"]:
                print(_c(f"\n  {label}", RED, BOLD))
                print(f"    TIMEOUT — simulation did not finish within {timeout_s} s")
                continue
            failed_checks = [c for c in parsed["checks"] if not c["passed"]]
            if not failed_checks:
                continue
            print(_c(f"\n  {label}", RED, BOLD))
            for chk in failed_checks:
                print(f"    [T={chk['time']:>6}] {chk['kind']} {chk['label']}")
                if chk["correct"]:
                    print(f"      {chk['correct']}")
                if chk["student"]:
                    print(f"      {chk['student']}")

    # ── Save log file ──────────────────────────────────────────────────────
    log_path = os.path.join(root, "output", f"test_results_{algorithm}.txt")
    write_log(log_path, algorithm, results, started_at, timeout_s)
    print()
    print(_c(f"  Log saved → {os.path.relpath(log_path, root)}", CYAN))
    print()

    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
