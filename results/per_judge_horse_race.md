# Per-judge subscale horse race

For each judge × condition × rubric dimension, OLS of:

    score ~ author_is_self + predicted_self + C(author) + C(category)

HC0 robust standard errors. `author_is_self = 1` iff the response is
actually authored by the judge; `predicted_self = 1` iff the judge's C4
authorship prediction names itself (looked up per (judge, prompt_id)).

## All judges × conditions × dimensions

| Judge | Condition | Dim | β(author_is_self) | SE | β(predicted_self) | SE | N |
|---|---|---|---:|---:|---:|---:|---:|
| claude-opus-4.7 | C1 | Correctness | +1.86 | 0.32 | +1.73 | 0.58 | 120 |
| claude-opus-4.7 | C1 | Completeness | +2.30 | 0.28 | +1.65 | 0.48 | 120 |
| claude-opus-4.7 | C1 | Clarity | +2.63 | 0.13 | +0.02 | 0.19 | 120 |
| claude-opus-4.7 | C1 | Creativity | +2.80 | 0.15 | +0.23 | 0.19 | 120 |
| claude-opus-4.7 | C1 | Constraint adherence | +2.19 | 0.29 | +1.75 | 0.48 | 120 |
| gemini-3.1-pro | C1 | Correctness | +0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gemini-3.1-pro | C1 | Completeness | -0.18 | 0.04 | -0.09 | 0.11 | 120 |
| gemini-3.1-pro | C1 | Clarity | -0.11 | 0.04 | -0.11 | 0.08 | 120 |
| gemini-3.1-pro | C1 | Creativity | +0.00 | 0.00 | -0.01 | 0.01 | 120 |
| gemini-3.1-pro | C1 | Constraint adherence | +0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gpt-5.5 | C1 | Correctness | -0.90 | 0.27 | +1.87 | 0.54 | 120 |
| gpt-5.5 | C1 | Completeness | -1.04 | 0.23 | +1.93 | 0.47 | 120 |
| gpt-5.5 | C1 | Clarity | -0.53 | 0.08 | +0.54 | 0.14 | 120 |
| gpt-5.5 | C1 | Creativity | -0.64 | 0.11 | +0.13 | 0.18 | 120 |
| gpt-5.5 | C1 | Constraint adherence | -0.83 | 0.26 | +2.28 | 0.52 | 120 |
| claude-opus-4.7 | C2 | Correctness | +2.07 | 0.43 | +1.08 | 0.78 | 120 |
| claude-opus-4.7 | C2 | Completeness | +2.27 | 0.44 | +1.46 | 0.77 | 120 |
| claude-opus-4.7 | C2 | Clarity | +1.95 | 0.26 | -0.00 | 0.37 | 120 |
| claude-opus-4.7 | C2 | Creativity | +2.70 | 0.30 | +0.25 | 0.44 | 120 |
| claude-opus-4.7 | C2 | Constraint adherence | +2.07 | 0.43 | +1.17 | 0.76 | 120 |
| gemini-3.1-pro | C2 | Correctness | +0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gemini-3.1-pro | C2 | Completeness | -0.19 | 0.04 | -0.17 | 0.09 | 120 |
| gemini-3.1-pro | C2 | Clarity | -0.08 | 0.05 | -0.02 | 0.15 | 120 |
| gemini-3.1-pro | C2 | Creativity | +0.01 | 0.01 | +0.06 | 0.07 | 120 |
| gemini-3.1-pro | C2 | Constraint adherence | +0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gpt-5.5 | C2 | Correctness | -0.82 | 0.31 | +1.97 | 0.60 | 120 |
| gpt-5.5 | C2 | Completeness | -0.88 | 0.27 | +1.96 | 0.51 | 120 |
| gpt-5.5 | C2 | Clarity | -0.25 | 0.13 | +0.30 | 0.18 | 120 |
| gpt-5.5 | C2 | Creativity | -0.51 | 0.12 | +0.23 | 0.17 | 120 |
| gpt-5.5 | C2 | Constraint adherence | -0.83 | 0.32 | +2.09 | 0.58 | 120 |
| claude-opus-4.7 | C3 | Correctness | +1.85 | 0.31 | +1.71 | 0.59 | 120 |
| claude-opus-4.7 | C3 | Completeness | +2.24 | 0.24 | +1.83 | 0.43 | 120 |
| claude-opus-4.7 | C3 | Clarity | +2.07 | 0.10 | +0.31 | 0.18 | 120 |
| claude-opus-4.7 | C3 | Creativity | +2.75 | 0.13 | +0.73 | 0.21 | 120 |
| claude-opus-4.7 | C3 | Constraint adherence | +1.77 | 0.26 | +2.04 | 0.47 | 120 |
| gemini-3.1-pro | C3 | Correctness | -0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gemini-3.1-pro | C3 | Completeness | -0.18 | 0.04 | -0.09 | 0.11 | 120 |
| gemini-3.1-pro | C3 | Clarity | -0.11 | 0.04 | -0.11 | 0.08 | 120 |
| gemini-3.1-pro | C3 | Creativity | +0.00 | 0.00 | -0.01 | 0.01 | 120 |
| gemini-3.1-pro | C3 | Constraint adherence | -0.00 | 0.00 | -0.00 | 0.00 | 120 |
| gpt-5.5 | C3 | Correctness | -0.90 | 0.27 | +1.87 | 0.54 | 120 |
| gpt-5.5 | C3 | Completeness | -1.04 | 0.23 | +1.93 | 0.47 | 120 |
| gpt-5.5 | C3 | Clarity | -0.53 | 0.08 | +0.54 | 0.14 | 120 |
| gpt-5.5 | C3 | Creativity | -0.64 | 0.11 | +0.13 | 0.18 | 120 |
| gpt-5.5 | C3 | Constraint adherence | -0.83 | 0.26 | +2.28 | 0.52 | 120 |

