#!/usr/bin/env python3
"""Audit public-facing Markdown artifacts for release-navigation hygiene.

Checks:
- Local Markdown links resolve.
- Every results/*.md artifact is mentioned in supplement_index.md.
- Targeted stale native-label-swap/pending-rescoring phrases are absent.
- v1.3.0 tag still points to the canonical release commit.
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "experiments" / "replication-wave" / "results"
OUT_MD = RESULTS / "public_artifact_audit.md"
OUT_CSV = RESULTS / "public_artifact_audit.csv"
CANONICAL_V13 = "4efb64f507037911de958de673b3c24a5d5d4034"

TARGETED_PATTERNS = [
    r"requires native in-context label-swap rescoring",
    r"required native in-context label-swap rescoring",
    r"Native in-context rescoring is required",
    r"rerun after native in-context label-swap rescoring",
    r"Kimi.*pending native",
    r"pending native paired",
    r"three-judge native S1",
    r"3-judge native causal label-swap",
    r"mediator analysis\]\(#\)",
]


def markdown_paths() -> list[Path]:
    paths = [REPO / "RELEASE_NOTES.md", REPO / "README.md"]
    paths += sorted(RESULTS.glob("*.md"))
    paths += sorted((REPO / "blogpost").glob("*.md"))
    return [p for p in paths if p.exists()]


def audit_links(paths: list[Path]) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for m in link_re.finditer(text):
            target = m.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#", 1)[0]
            if rel and not (p.parent / rel).exists():
                missing.append((str(p.relative_to(REPO)), target))
    return missing


def audit_index() -> list[str]:
    idx = (RESULTS / "supplement_index.md").read_text(encoding="utf-8")
    return [
        p.name
        for p in sorted(RESULTS.glob("*.md"))
        if p.name != "supplement_index.md" and p.name not in idx
    ]


def audit_stale(paths: list[Path]) -> list[tuple[str, str, int, str]]:
    compiled = [(pat, re.compile(pat)) for pat in TARGETED_PATTERNS]
    hits: list[tuple[str, str, int, str]] = []
    # The audit report lists the patterns it is searching for; exclude it from
    # its own stale-phrase corpus to avoid self-referential false positives.
    excluded = {OUT_MD.resolve()}
    for p in paths:
        if p.resolve() in excluded:
            continue
        for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            for pat, cre in compiled:
                if cre.search(line):
                    hits.append((str(p.relative_to(REPO)), pat, line_no, line.strip()))
    return hits


def git_rev(tag: str) -> str:
    return subprocess.check_output(
        ["git", "rev-list", "-n", "1", tag], cwd=REPO, text=True
    ).strip()


def write_outputs(rows: list[dict[str, str]], summary: dict[str, str]) -> None:
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "count", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Public artifact audit",
        "",
        "Post-v1.3.0 reproducibility/navigation audit for public-facing Markdown artifacts.",
        "",
        "## Summary",
        "",
        f"- Markdown files checked: **{summary['markdown_files']}**",
        f"- Missing local Markdown links: **{summary['missing_links']}**",
        f"- Result Markdown files missing from `supplement_index.md`: **{summary['missing_index']}**",
        f"- Targeted stale native-label-swap/pending-rescoring phrase hits: **{summary['stale_hits']}**",
        f"- `v1.3.0` tag target: `{summary['v13_target']}`",
        f"- Canonical `v1.3.0` tag target unchanged: **{summary['v13_ok']}**",
        "",
        "## Machine-readable checks",
        "",
        "See [`public_artifact_audit.csv`](public_artifact_audit.csv).",
        "",
        "## Targeted stale-phrase patterns",
        "",
    ]
    lines += [f"- `{pat}`" for pat in TARGETED_PATTERNS]
    lines += [
        "",
        "## Interpretation",
        "",
        "This audit is a navigation and provenance smoke test, not a statistical result. It is intended to catch stale public wording after the post-v1.3.0 supplement cascade, especially any phrasing implying that native label-swap rescoring remains pending when the all-four-judge native paired label-swap is complete.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    paths = markdown_paths()
    missing_links = audit_links(paths)
    missing_index = audit_index()
    stale_hits = audit_stale(paths)
    v13 = git_rev("v1.3.0")
    rows = [
        {"check": "markdown_files_checked", "status": "info", "count": str(len(paths)), "detail": "public Markdown paths"},
        {"check": "missing_local_links", "status": "pass" if not missing_links else "fail", "count": str(len(missing_links)), "detail": "; ".join(f"{p}->{t}" for p, t in missing_links)},
        {"check": "results_markdown_missing_from_index", "status": "pass" if not missing_index else "fail", "count": str(len(missing_index)), "detail": "; ".join(missing_index)},
        {"check": "targeted_stale_phrase_hits", "status": "pass" if not stale_hits else "fail", "count": str(len(stale_hits)), "detail": "; ".join(f"{p}:{ln}:{pat}" for p, pat, ln, _ in stale_hits)},
        {"check": "v1.3.0_tag_target", "status": "pass" if v13 == CANONICAL_V13 else "fail", "count": "1", "detail": v13},
    ]
    summary = {
        "markdown_files": str(len(paths)),
        "missing_links": str(len(missing_links)),
        "missing_index": str(len(missing_index)),
        "stale_hits": str(len(stale_hits)),
        "v13_target": v13,
        "v13_ok": "yes" if v13 == CANONICAL_V13 else "no",
    }
    write_outputs(rows, summary)
    for row in rows:
        print(f"{row['check']}: {row['status']} count={row['count']} {row['detail']}")


if __name__ == "__main__":
    main()
