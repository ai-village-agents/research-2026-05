#!/usr/bin/env bash
# One-shot driver: stage label-swap packets to score_sheets and run the eval.
# Usage:  ./run_my_label_swap.sh <judge_id>
# Example: ./run_my_label_swap.sh claude-opus-4.7
#
# This is intentionally idempotent: it will skip already-scored sessions
# (the inner eval_all_sessions.py checks for `_scored.json`), and it copies
# packets only if the destination is missing.

set -euo pipefail

JUDGE="${1:-}"
if [[ -z "${JUDGE}" ]]; then
  echo "Usage: $0 <judge_id>  (e.g. claude-opus-4.7)" >&2
  exit 1
fi

cd "$(dirname "$0")"

SRC="data/label_swap_packets/${JUDGE}"
DST="score_sheets/label_swap/${JUDGE}"

if [[ ! -d "${SRC}" ]]; then
  echo "ERROR: packet source ${SRC} not found" >&2
  exit 1
fi

mkdir -p "${DST}"
for s in "${SRC}"/session_*.json; do
  base="$(basename "${s}")"
  if [[ ! -f "${DST}/${base}" ]]; then
    cp -v "${s}" "${DST}/${base}"
  fi
done

# Patch eval_all_sessions.py JUDGE in-place (writes a temp copy so we don't
# mutate the tracked file). Then run.
TMP="$(mktemp)"
sed "s/^    JUDGE = \"REPLACE_WITH_YOUR_JUDGE_ID\"/    JUDGE = \"${JUDGE}\"/" \
  eval_all_sessions.py > "${TMP}"
python3 "${TMP}"
rm -f "${TMP}"

echo "Done. Scored files in ${DST}/."
echo "Next step: 'git add -f ${DST}/session_*_scored.json' to commit."
