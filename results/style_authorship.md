# Stylometric authorship analysis

How much of the 'raw style' authorship signal survives C2 paraphrasing? This is a mechanistic anchor for the per-judge horse-race finding that clarity/creativity authorship effects survive paraphrasing. If stylometric features still differentiate authors after paraphrasing, judges have a 'raw style' channel to latch onto independent of their belief about authorship.

N = 120 originals, 120 paraphrases. 4 authors x 30 prompts each.

## Per-author means (originals)

| feature | claude-opus-4.7 | gemini-3.1-pro | gpt-5.5 | kimi-k2.6 |
|---|---|---|---|---|
| word_count | 374.033 | 237.567 | 199.600 | 178.267 |
| mean_sentence_length | 19.420 | 25.221 | 22.112 | 21.696 |
| mean_word_length | 4.687 | 4.823 | 4.913 | 4.864 |
| type_token_ratio | 0.536 | 0.545 | 0.627 | 0.606 |
| markdown_header_rate | 0.077 | 0.021 | 0.007 | 0.005 |
| bullet_rate | 0.113 | 0.115 | 0.050 | 0.049 |
| emdash_per_1k | 0.858 | 0.130 | 0.034 | 1.324 |
| first_person_per_100w | 1.340 | 1.736 | 0.782 | 0.854 |
| bold_count | 5.233 | 3.033 | 1.367 | 0.033 |
| colons_per_100w | 1.839 | 3.032 | 2.485 | 2.860 |
| semicolons_per_100w | 0.624 | 0.239 | 0.654 | 0.304 |

## Per-author means (paraphrases, indexed by ORIGINAL author)

| feature | claude-opus-4.7 | gemini-3.1-pro | gpt-5.5 | kimi-k2.6 |
|---|---|---|---|---|
| word_count | 370.633 | 227.967 | 215.933 | 186.733 |
| mean_sentence_length | 19.285 | 26.485 | 23.720 | 23.515 |
| mean_word_length | 4.934 | 4.753 | 4.974 | 4.913 |
| type_token_ratio | 0.557 | 0.564 | 0.617 | 0.612 |
| markdown_header_rate | 0.056 | 0.024 | 0.007 | 0.004 |
| bullet_rate | 0.078 | 0.110 | 0.047 | 0.049 |
| emdash_per_1k | 0.840 | 0.166 | 0.134 | 0.464 |
| first_person_per_100w | 0.975 | 1.146 | 0.543 | 0.811 |
| bold_count | 3.433 | 2.933 | 1.233 | 0.033 |
| colons_per_100w | 1.730 | 2.909 | 2.174 | 2.183 |
| semicolons_per_100w | 0.366 | 0.279 | 0.449 | 0.344 |

## Authorship signal per feature

One-way F-statistic across the 4 authors (higher = stronger authorship signal). Style attenuation % = (1 - F_para/F_orig) × 100.

| feature | F_orig | F_para | atten % |
|---|---:|---:|---:|
| word_count | 34.20 | 26.86 | 21.5% |
| bold_count | 15.22 | 8.94 | 41.3% |
| markdown_header_rate | 14.21 | 7.28 | 48.8% |
| emdash_per_1k | 5.90 | 3.54 | 40.0% |
| type_token_ratio | 3.63 | 1.92 | 47.1% |
| semicolons_per_100w | 3.45 | 0.42 | 87.9% |
| bullet_rate | 2.22 | 1.53 | 31.0% |
| first_person_per_100w | 1.71 | 0.69 | 59.7% |
| colons_per_100w | 0.82 | 0.82 | 0.5% |
| mean_sentence_length | 0.68 | 0.91 | -33.4% |
| mean_word_length | 0.44 | 0.53 | -19.7% |

## Author classifier (LOO cross-validated)

4-class multinomial logistic regression on z-scored style features, leave-one-prompt-out cross-validation. Chance = 25%.

- **Originals: 65.0% accuracy**
  - claude-opus-4.7: 80.0%
  - gemini-3.1-pro: 56.7%
  - gpt-5.5: 66.7%
  - kimi-k2.6: 56.7%
- **Paraphrases: 50.8% accuracy**
  - claude-opus-4.7: 73.3%
  - gemini-3.1-pro: 40.0%
  - gpt-5.5: 20.0%
  - kimi-k2.6: 70.0%

## Interpretation

Paraphrasing (C2) attenuates *surface* style markers (em-dashes, bold count, semicolons) substantially but largely **preserves length, structure, and lexical-richness signatures**. A simple stylometric classifier trained on originals achieves 65% authorship accuracy (chance 25%); on paraphrases it still achieves 51%.

This is a mechanistic anchor for why C2 paraphrasing only *partially* attenuates the pooled self-preference effect (45.2% attenuation, not 100%) and why the form-dimension (clarity/creativity) authorship coefficients survive paraphrasing in the per-judge horse-race: the raw-style channel still has signal — paraphrases retain author-typical length, structural markers, and lexical richness, even after surface rewording.
