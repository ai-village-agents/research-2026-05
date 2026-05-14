#!/usr/bin/env python3
"""Validate native S1+S2 label-swap scored files.

The paired label-swap analyzers require each judge's session_1_scored.json and
session_2_scored.json to be genuine native in-context scores, not codex-backed
wrapper output. This validator checks both accepted locations:

- score_sheets/label_swap/<judge>/session_{1,2}_scored.json  (canonical)
- data/label_swap_scores/<judge>/session_{1,2}_scored.json   (fallback)

It validates native-format markers, packet blind-ID coverage, duplicate IDs,
displayed-label consistency, and 1–10 numeric rubric dimensions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PACKETS = ROOT / "data" / "label_swap_packets"
CANONICAL = ROOT / "score_sheets" / "label_swap"
FALLBACK = ROOT / "data" / "label_swap_scores"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def packet_entries(judge: str, session: int) -> dict[str, dict[str, Any]]:
    path = PACKETS / judge / f"session_{session}.json"
    if not path.exists():
        return {}
    raw = load_json(path)
    return {e["blind_id"]: e for e in raw.get("entries", [])}


def score_candidates(judge: str, session: int) -> list[Path]:
    rel = f"{judge}/session_{session}_scored.json"
    return [CANONICAL / rel, FALLBACK / rel]


def native_entries(raw: Any) -> tuple[bool, list[dict[str, Any]], str]:
    if isinstance(raw, list):
        return True, raw, "top-level-list"
    if isinstance(raw, dict):
        if raw.get("scoring_method") == "native_in_context":
            entries = raw.get("entries", [])
            if not isinstance(entries, list):
                return False, [], "native dict has non-list entries"
            return True, entries, "native_in_context-dict"
        return False, [], f"dict scoring_method={raw.get('scoring_method')!r}"
    return False, [], f"unsupported top-level type {type(raw).__name__}"


def validate_session(judge: str, session: int) -> tuple[list[str], str | None, int]:
    errors: list[str] = []
    existing = [p for p in score_candidates(judge, session) if p.exists()]
    if not existing:
        return [f"missing {judge} session {session} scored file"], None, 0
    if len(existing) > 1:
        errors.append(f"both canonical and fallback scored files exist for {judge} session {session}; using canonical")
    path = existing[0] if existing[0].is_relative_to(CANONICAL) else existing[0]
    if len(existing) > 1:
        canon = CANONICAL / judge / f"session_{session}_scored.json"
        if canon.exists():
            path = canon
    try:
        raw = load_json(path)
    except Exception as e:  # noqa: BLE001 - validation should report all failures cleanly.
        return [f"could not parse {path}: {e}"], str(path.relative_to(ROOT)), 0
    ok, entries, kind = native_entries(raw)
    if not ok:
        return [f"non-native scored file for {judge} session {session}: {kind}"], str(path.relative_to(ROOT)), 0
    pkt = packet_entries(judge, session)
    if len(pkt) != 40:
        errors.append(f"packet for {judge} session {session} has {len(pkt)} entries, expected 40")
    seen: set[str] = set()
    for i, e in enumerate(entries):
        where = f"{judge} session {session} entry {i}"
        bid = e.get("blind_id")
        if not isinstance(bid, str):
            errors.append(f"{where}: blind_id missing/non-string")
            continue
        if bid in seen:
            errors.append(f"{where}: duplicate blind_id {bid}")
        seen.add(bid)
        if bid not in pkt:
            errors.append(f"{where}: blind_id {bid} not in packet")
            continue
        expected_label = pkt[bid].get("displayed_label")
        if "displayed_label" in e and e.get("displayed_label") != expected_label:
            errors.append(f"{where}: displayed_label {e.get('displayed_label')!r} != packet {expected_label!r}")
        for d in DIMS:
            v = e.get(d)
            if not isinstance(v, (int, float)) or not (1 <= v <= 10):
                errors.append(f"{where}: {d}={v!r} not numeric 1..10")
    missing = sorted(set(pkt) - seen)
    extra = sorted(seen - set(pkt))
    if missing:
        errors.append(f"{judge} session {session}: missing {len(missing)} packet blind_ids")
    if extra:
        errors.append(f"{judge} session {session}: {len(extra)} extra blind_ids")
    if len(entries) != 40:
        errors.append(f"{judge} session {session}: {len(entries)} scored entries, expected 40")
    return errors, f"{path.relative_to(ROOT)} ({kind})", len(entries)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-complete", action="store_true", help="fail if any judge lacks native S1+S2 scored files")
    ap.add_argument("--judges", nargs="*", default=JUDGES, choices=JUDGES)
    args = ap.parse_args()

    all_errors: list[str] = []
    complete: list[str] = []
    incomplete: list[str] = []
    print("Native label-swap validation")
    for judge in args.judges:
        judge_errors: list[str] = []
        found_sessions = 0
        print(f"judge {judge}")
        for session in (1, 2):
            errors, path, n = validate_session(judge, session)
            if path:
                found_sessions += 1
                print(f"  session_{session}: {n} entries from {path}")
            else:
                print(f"  session_{session}: missing")
            judge_errors.extend(errors)
        if found_sessions == 2 and not judge_errors:
            complete.append(judge)
        else:
            incomplete.append(judge)
        for e in judge_errors:
            print(f"  error: {e}")
        all_errors.extend(judge_errors)
    print("complete_judges", complete)
    print("incomplete_judges", incomplete)
    if args.require_complete and incomplete:
        raise SystemExit(1)
    # Without --require-complete, fail on malformed present files but not on missing pending judges.
    malformed = [e for e in all_errors if not e.startswith("missing ")]
    if malformed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
