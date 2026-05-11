#!/usr/bin/env bash
# Run the evaluator-bias analysis suite from the repository root.
#
# Default mode runs all core/report analyses that work in the default village
# Python environment (pandas + numpy). Add --plots to also regenerate PNG plots;
# plotting requires matplotlib/seaborn.

set -euo pipefail

if [[ ! -d analysis || ! -d data ]]; then
  echo "Please run this script from the repository root." >&2
  exit 2
fi

RUN_PLOTS=0
REQUIRE_ALL_JUDGES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plots)
      RUN_PLOTS=1
      ;;
    --require-all-judges)
      REQUIRE_ALL_JUDGES=1
      ;;
    *)
      echo "Usage: bash analysis/run_all_analyses.sh [--plots] [--require-all-judges]" >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p results

echo "==> Validate judgment CSVs"
VALIDATOR_ARGS=(--strict)
if [[ "$REQUIRE_ALL_JUDGES" -eq 1 ]]; then
  VALIDATOR_ARGS+=(--require-all-judges)
fi
python3 -u analysis/validate_judgments.py "${VALIDATOR_ARGS[@]}"

echo "==> Preregistered analysis"
python3 -u analysis/run_analysis.py --from-judgments-dir --report results/analysis_report.md

echo "==> Exploratory perceived-authorship analysis"
python3 -u analysis/recognition_mediation.py --report results/recognition_mediation.md

echo "==> Exploratory subscale analysis"
python3 -u analysis/subscale_analysis.py --report results/subscale_analysis.md

echo "==> Exploratory per-judge horse-race analysis"
python3 -u analysis/per_judge_horse_race.py --report results/per_judge_horse_race.md

echo "==> Exploratory per-judge horse-race bootstrap CIs"
python3 -u analysis/horse_race_bootstrap.py --report results/horse_race_bootstrap.md --bootstrap 500

echo "==> Exploratory confidence stratification"
python3 -u analysis/confidence_stratification.py

echo "==> Exploratory stylometric authorship analysis"
python3 -u analysis/style_authorship.py --report results/style_authorship.md

echo "==> Exploratory C2 paraphraser-is-judge confound check"
python3 -u analysis/paraphraser_confound.py --report results/paraphraser_confound.md

echo "==> Exploratory inter-judge agreement diagnostics"
python3 -u analysis/interjudge_agreement.py --report results/interjudge_agreement.md


echo "==> Exploratory variance decomposition"
python3 -u analysis/variance_decomposition.py --report results/variance_decomposition.md

if [[ "$RUN_PLOTS" -eq 1 ]]; then
  echo "==> Plot regeneration"
  python3 -u analysis/plot_results.py
  python3 -u analysis/plot_condition_effects.py
  python3 -u analysis/plot_score_distributions.py
  python3 -u analysis/plot_confusion_matrices.py
  python3 -u analysis/plot_subscale.py
else
  echo "==> Skipping PNG plot regeneration (pass --plots after installing matplotlib/seaborn)."
fi

echo "==> Analysis suite complete. Review results/ and analysis/plots/ before committing regenerated artifacts."
