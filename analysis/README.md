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

Regenerate plots after installing plotting dependencies:

```bash
python3 analysis/plot_results.py
python3 analysis/plot_condition_effects.py
python3 analysis/plot_score_distributions.py
python3 analysis/plot_confusion_matrices.py
python3 analysis/plot_subscale.py
```

## Output hygiene

The `results/` directory is gitignored for regenerated local reports. Commit
files from `results/` only when they are intentionally part of a blog or release
branch.
