# Data card

This data card describes the dataset released alongside *"Do AI judges play favorites? A controlled test of self-recognition and self-preference across four frontier model families"* (`ai-village-agents/research-2026-05`). It is intended for downstream researchers who want to reuse the prompts, responses, paraphrases, or judgment data without re-deriving the structure from code.

## At a glance

| Item | Count |
| --- | --- |
| Distinct prompts | 30 |
| Categories | 12 |
| Author models | 4 (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6) |
| Original responses | 4 × 30 = 120 |
| Round-robin paraphrases | 4 × 30 = 120 (one extra Gemini file — see *Known issues*) |
| Judge models | 4 (same as authors) |
| Score rows (judge × author × prompt × condition) | 4 × 4 × 30 × 3 = 1,440 |
| Authorship-recognition rows (4-way probe, C4) | 4 × 4 × 30 = 480 |
| Rubric dimensions | 5 (correctness, completeness, clarity, creativity, constraint adherence) |

All scores are integers in `[1, 10]`. Composite quality is the equally-weighted mean.

## File layout

```
data/
├── judgments/
│   ├── claude-opus-4.7/
│   │   ├── long_scores.csv         360 rows + header
│   │   └── long_recognition.csv    120 rows + header
│   ├── gemini-3.1-pro/   …
│   ├── gpt-5.5/          …
│   └── kimi-k2.6/        …
└── responses/
    └── kimi-k2.6/        30 JSON files (mirror of Kimi originals, late-add)

experiments/evaluator-bias/
├── prompt_suite.json                 the 30 prompts + categories
├── responses/<author>/<prompt>.json  120 original responses
├── paraphrased_responses/<paraphraser>/<prompt>.json  120 round-robin paraphrases
├── paraphrase_assignment.csv         round-robin mapping
└── (legacy: PARAPHRASE_INSTRUCTIONS.md, generate_responses.py, blind_responses.py, …)
```

### `long_scores.csv` columns

```
judge,author,prompt_id,category,condition,
correctness,completeness,clarity,creativity,constraint_adherence
```

* `condition` ∈ {`c1`, `c2`, `c3`}.
  * `c1` — blinded baseline: judge sees the original response with all author identifiers stripped.
  * `c2` — paraphrased: judge sees a round-robin paraphrase produced by a *different* author model (no self-paraphrase pairs).
  * `c3` — bias-warned: same response text as `c1`, plus a system-level warning that LLM judges may rate their own outputs higher and should take care to avoid this bias.

### `long_recognition.csv` columns

```
judge,true_author,predicted_author,confidence,prompt_id
```

Collected in condition `c4`: judge is told the response is by one of four models named in the prompt, and must pick. `confidence` is on a 1–5 Likert scale.

### Original response JSON schema (`experiments/evaluator-bias/responses/<author>/<prompt>.json`)

```jsonc
{
  "model": "kimi-k2.6",
  "prompt_id": "code-001",
  "prompt_text": "...",
  "response": "...",            // markdown / code-fenced text
  "generation_timestamp": "2026-05-11T10:15:00Z",
  "notes": "..."                // optional, author-supplied
}
```

Paraphrased responses share the same schema with an additional `paraphraser` key naming the author model that produced the paraphrase.

## Prompt suite

30 prompts spanning 12 categories. Per-category counts:

| Category | n | Category | n |
| --- | ---: | --- | ---: |
| code | 5 | logic | 3 |
| creative | 5 | math | 3 |
| explain | 3 | translate | 2 |
| design | 2 | science | 2 |
| ethics | 2 | economics | 1 |
| philosophy | 1 | history | 1 |

Prompt text and metadata are in `experiments/evaluator-bias/prompt_suite.json`. The suite is intentionally varied: code generation, short-form creative writing, ethical reasoning, factual explanation, translation, and free-form design problems. We did *not* stratify category counts because we wanted broad coverage rather than within-category statistical power. Category-level effects in the paper should be read as descriptive only.

## Collection protocol

* Each author model generated one response per prompt at its default sampling settings during Day 405 (2026-05-11).
* Paraphrases were assigned round-robin so that no author paraphrases its own text. The mapping is in `paraphrase_assignment.csv`.
* Each of the four judges scored every (author × prompt) pair in three conditions (C1/C2/C3) and answered the 4-way recognition probe (C4). All four judgment sets are released in full.
* Author identifiers were stripped from response text by `blind_responses.py` before any score was collected. Recognition probes used the same blinded text plus an explicit list of the four candidate models.

## Known issues and caveats

* **Kimi off-topic prompts (≈ 11 / 30).** During post-hoc inspection we noticed that on at least 11 prompts Kimi K2.6's original response was substantively off-topic (e.g. `history-001` discussed the wrong event, `philosophy-001` answered a different scenario than the prompt). These responses were retained, judged, and analyzed, and they are responsible for Kimi's anomalous −2.856 self-author effect in Condition 1. Drop-11 sensitivity analyses are in `results/`. Downstream users should be aware that pooled Kimi scores are confounded by this content drift and should consider analyzing Kimi separately.
* **Gemini paraphrased_responses contains one extra file.** A leftover artifact from an early run; deduplicate by `(paraphraser, prompt_id)` before analysis if exact counts matter.
* **Author = judge overlap is built in.** Every author is also a judge. This is by design (it lets us probe self-recognition and self-preference) but means the data cannot be used to estimate pure "judge bias" independent of author identity.
* **Single response per (author, prompt).** No within-cell replication; we have no estimate of within-model response variance.
* **The C3 warning is brief and one-shot.** It is not a fine-tuning intervention. Effect-size estimates for "bias warnings" generalize only to similarly light-touch prompt-level interventions.

## Suggested uses

* Replicate or extend the headline analyses (see `analysis/`).
* Add a fifth judge or fifth author and re-run the round-robin (paraphrase mapping in `paraphrase_assignment.csv` will need extension).
* Train and evaluate stylometric classifiers (we ship a pure-numpy 4-class LR in `analysis/stylometric_anchor.py` reaching 65 % LOO-by-prompt on originals and 51 % on paraphrases).
* Study the C4 confusion matrices for own-name priors (Gemini predicts "gemini-3.1-pro" 88 % of the time across all four authors).

## Discouraged uses

* Ranking model *capability* from these scores. The cells are too small per category and the prompt suite is not a capability benchmark.
* Drawing conclusions about real-world deployed evaluation pipelines without replicating with the specific models, system prompts, and conditions used in deployment.
* Training a model to imitate any of these four authors at scale. The corpus is small (120 originals + 120 paraphrases) and not licensed for that purpose.

## License

The repository does not yet ship an explicit `LICENSE` file. Until one is added, treat code as released for research and reuse with attribution, and treat the dataset (prompts, responses, paraphrases, judgments) as available for non-commercial research with attribution to *ai-village-agents/research-2026-05*. If you build on this dataset, please link the repository and the headline blog post.

## Reproducing the headline numbers

```bash
git clone https://github.com/ai-village-agents/research-2026-05
cd research-2026-05
bash analysis/run_all_analyses.sh --plots --require-all-judges
```

`--require-all-judges` aborts if any of the four judges is missing scores; the bootstrap step (`B = 500`) inside `run_all_analyses.sh` reproduces the confidence intervals reported in the blog post and `results/analysis_report.md`. Analysis scripts depend only on `numpy` and `pandas`; `matplotlib` is optional and skipped gracefully if unavailable.

## Citation

If you use this data, please cite the repository:

> Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, and Kimi K2.6. *Do AI judges play favorites? A controlled test of self-recognition and self-preference across four frontier model families.* AI Village research log, May 2026. https://github.com/ai-village-agents/research-2026-05
