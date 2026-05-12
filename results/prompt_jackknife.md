# Prompt-level jackknife robustness

This appendix re-estimates the perceived-authorship horse-race models after dropping each `prompt_id` one at a time. It asks whether the main coefficient signs and magnitudes are artifacts of a single prompt.

Important caveats:
- This is a leave-one-prompt-out sensitivity diagnostic, not a new preregistered hypothesis test.
- The jackknife range is not a confidence interval; prompts are deliberately heterogeneous task clusters.
- `predicted_self` comes from the later C4 authorship probe, so these models remain descriptive rather than causal.
- Within-judge rows omit author fixed effects because, for a single judge, `author_is_self` is collinear with one author identity.

## Model specifications

For each condition C1/C2/C3, the pooled diagnostic fits:

    composite ~ author_is_self + predicted_self + C(author) + C(judge) + C(category)

For each judge × condition, the within-judge descriptive diagnostic fits:

    composite ~ author_is_self + predicted_self + C(category)

## Pooled horse-race stability

| Scope | Condition | Term | Full β | LOO min | LOO max | LOO SD | Sign flips | Extremal prompts |
|---|---|---|---:|---:|---:|---:|---:|---|
| pooled | C1 | `author_is_self` | -0.191 | -0.230 | -0.141 | 0.026 | 0 | min translate-002; max explain-001 |
| pooled | C1 | `predicted_self` | +0.501 | +0.426 | +0.550 | 0.037 | 0 | min explain-001; max translate-002 |
| pooled | C2 | `author_is_self` | -0.349 | -0.416 | -0.302 | 0.028 | 0 | min code-005; max explain-001 |
| pooled | C2 | `predicted_self` | +0.499 | +0.432 | +0.591 | 0.040 | 0 | min explain-001; max code-005 |
| pooled | C3 | `author_is_self` | -0.265 | -0.307 | -0.217 | 0.025 | 0 | min translate-002; max explain-001 |
| pooled | C3 | `predicted_self` | +0.518 | +0.445 | +0.568 | 0.037 | 0 | min explain-001; max science-002 |

## Within-judge descriptive stability

| Scope | Condition | Term | Full β | LOO min | LOO max | LOO SD | Sign flips | Extremal prompts |
|---|---|---|---:|---:|---:|---:|---:|---|
| claude-opus-4.7 | C1 | `author_is_self` | +1.637 | +1.466 | +1.728 | 0.040 | 0 | min code-003; max code-001 |
| claude-opus-4.7 | C1 | `predicted_self` | +0.137 | +0.048 | +0.346 | 0.046 | 0 | min code-001; max code-003 |
| gemini-3.1-pro | C1 | `author_is_self` | +0.007 | -0.001 | +0.016 | 0.004 | 2 | min economics-001; max math-003 |
| gemini-3.1-pro | C1 | `predicted_self` | -0.098 | -0.118 | -0.082 | 0.008 | 0 | min philosophy-001; max science-001 |
| gpt-5.5 | C1 | `author_is_self` | +0.762 | +0.709 | +0.803 | 0.023 | 0 | min logic-001; max math-002 |
| gpt-5.5 | C1 | `predicted_self` | +0.495 | +0.456 | +0.549 | 0.021 | 0 | min creative-005; max logic-001 |
| kimi-k2.6 | C1 | `author_is_self` | -2.850 | -2.963 | -2.680 | 0.108 | 0 | min translate-001; max ethics-001 |
| kimi-k2.6 | C1 | `predicted_self` | -0.050 | -0.153 | +0.085 | 0.073 | 9 | min code-001; max ethics-002 |
| claude-opus-4.7 | C2 | `author_is_self` | +1.427 | +0.905 | +1.684 | 0.121 | 0 | min code-005; max code-004 |
| claude-opus-4.7 | C2 | `predicted_self` | -0.306 | -0.556 | +0.305 | 0.134 | 1 | min code-004; max code-005 |
| gemini-3.1-pro | C2 | `author_is_self` | -0.013 | -0.018 | -0.004 | 0.004 | 0 | min explain-002; max math-003 |
| gemini-3.1-pro | C2 | `predicted_self` | -0.067 | -0.099 | -0.051 | 0.009 | 0 | min logic-002; max science-001 |
| gpt-5.5 | C2 | `author_is_self` | +0.821 | +0.762 | +0.872 | 0.025 | 0 | min creative-002; max math-001 |
| gpt-5.5 | C2 | `predicted_self` | +0.454 | +0.395 | +0.525 | 0.024 | 0 | min creative-002; max logic-001 |
| kimi-k2.6 | C2 | `author_is_self` | -2.972 | -3.085 | -2.808 | 0.107 | 0 | min translate-001; max ethics-001 |
| kimi-k2.6 | C2 | `predicted_self` | +0.068 | -0.037 | +0.203 | 0.070 | 8 | min code-001; max ethics-002 |
| claude-opus-4.7 | C3 | `author_is_self` | +1.227 | +1.059 | +1.281 | 0.040 | 0 | min code-003; max code-005 |
| claude-opus-4.7 | C3 | `predicted_self` | +0.327 | +0.279 | +0.539 | 0.045 | 0 | min code-001; max code-003 |
| gemini-3.1-pro | C3 | `author_is_self` | +0.007 | -0.001 | +0.016 | 0.004 | 2 | min economics-001; max math-003 |
| gemini-3.1-pro | C3 | `predicted_self` | -0.098 | -0.118 | -0.082 | 0.008 | 0 | min philosophy-001; max logic-002 |
| gpt-5.5 | C3 | `author_is_self` | +0.762 | +0.709 | +0.803 | 0.023 | 0 | min logic-001; max math-002 |
| gpt-5.5 | C3 | `predicted_self` | +0.495 | +0.456 | +0.549 | 0.021 | 0 | min creative-005; max logic-001 |
| kimi-k2.6 | C3 | `author_is_self` | -2.850 | -2.963 | -2.680 | 0.108 | 0 | min translate-001; max ethics-001 |
| kimi-k2.6 | C3 | `predicted_self` | -0.050 | -0.153 | +0.085 | 0.073 | 9 | min code-001; max ethics-002 |

## Reading the diagnostic

Across the three pooled condition-level fits, `predicted_self` stays positive in 3/3 leave-one-prompt-out ranges. `author_is_self` stays strictly positive in 0/3 ranges and strictly negative in 3/3 ranges.
Thus the prompt-jackknife check supports the paper's qualitative framing: the perceived-authorship channel is more stable than a universal actual-authorship self-preference coefficient, while judge-specific profiles remain heterogeneous.

The machine-readable summary behind these tables is [`prompt_jackknife.csv`](prompt_jackknife.csv).

