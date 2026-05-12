# Analysis scripts

This directory contains the preregistered analysis runner plus exploratory scripts
used for the blog-post figures and mechanism checks.

## Dependencies

### Core analysis

Use Python 3.11+ with:

- `pandas`
- `numpy`

These are sufficient for the built-in loading, coverage checks, descriptive
statistics, and fallback linear models used by `run_analysis.py`.

### Optional modeling

- `statsmodels`
- `scipy`

`run_analysis.py` will use these when available for the preregistered mixed/OLS
models and binomial tests, but it has built-in NumPy/pandas fallbacks when they
are absent.

### Markdown tables

- `tabulate`

`tabulate` is optional. Scripts that render pandas tables to markdown fall back
to fenced plain-text tables when `tabulate` is not installed.

### Plot regeneration

- `matplotlib`
- `seaborn`

These are required to regenerate PNG plots. If they are absent, the existing
committed PNGs on blog branches can still be viewed, but the plotting scripts
will not run until the plotting dependencies are installed.

## Example commands

Validate per-judge judgment CSVs before final reruns:

```bash
python3 analysis/validate_judgments.py --strict
python3 analysis/validate_judgments.py --require-all-judges --strict
```

Run the preregistered analysis on per-judge judgment directories:

```bash
python3 analysis/run_analysis.py --from-judgments-dir --report results/analysis_report.md
```

Run exploratory recognition mediation:

```bash
python3 analysis/recognition_mediation.py --report results/recognition_mediation.md
```

Run exploratory subscale analysis:

```bash
python3 analysis/subscale_analysis.py --report results/subscale_analysis.md
```

Run cluster-bootstrap confidence intervals for the per-judge horse-race coefficients:

```bash
python3 analysis/horse_race_bootstrap.py --report results/horse_race_bootstrap.md --bootstrap 500
```

Run per-dimension cluster-bootstrap confidence intervals for exploratory subscale horse-race checks (slower; not part of the default all-analysis runner):

```bash
python3 analysis/horse_race_bootstrap_per_dim.py --report results/horse_race_bootstrap_per_dim.md --bootstrap 500
```

Run confidence stratification:

```bash
python3 analysis/confidence_stratification.py
```

Run exploratory stylometric authorship analysis (core dependencies only):

```bash
python3 analysis/style_authorship.py --report results/style_authorship.md
```

Run exploratory C2 paraphraser-is-judge confound check:

```bash
python3 analysis/paraphraser_confound.py --report results/paraphraser_confound.md
```

Run exploratory inter-judge agreement diagnostics:

```bash
python3 analysis/interjudge_agreement.py --report results/interjudge_agreement.md
```

Regenerate plots after installing plotting dependencies:

```bash
python3 analysis/plot_results.py
python3 analysis/plot_condition_effects.py
python3 analysis/plot_score_distributions.py
python3 analysis/plot_confusion_matrices.py
python3 analysis/plot_subscale.py
```

Run the core/report analysis suite in one command:

```bash
bash analysis/run_all_analyses.sh
```

To also regenerate PNG plots after installing plotting dependencies:

```bash
bash analysis/run_all_analyses.sh --plots
```

For the final-publication/full-dataset check, require all four expected judge directories before running the suite:

```bash
bash analysis/run_all_analyses.sh --plots --require-all-judges
```

## Output hygiene

The `results/` directory is gitignored for regenerated local reports. Commit
files from `results/` only when they are intentionally part of a blog or release
branch.
