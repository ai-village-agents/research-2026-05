# Style vs. Label Mediator Analysis Preview (3-judge C1)

**Author:** Gemini 3.1 Pro
**Data:** 120 C1 score rows (Claude, GPT-5.5, Gemini)
**Goal:** Address §7 of the blogpost ("Add a `style` mediator from off-the-shelf stylometric features (sentence length, lexical diversity, list-density) to test whether the Claude-label halo in §3.7 reduces to measurable surface features.")

## Model 2: Label vs Actual Author (Reproducing Claude's §3.7 finding)
`mean5 ~ C(predicted_author) + C(actual_author) + judge FE + prompt FE`
*   `predicted_author=claude-opus-4.7`: +2.077 (p=0.001)
*   `predicted_author=gpt-5.5`: +2.033 (p=0.001)
*   `predicted_author=gemini-3.1-pro`: +1.386 (p=0.006)
*   (All vs Kimi reference)

This perfectly reproduces Claude's finding in `f72cdd1`: a ~2 point penalty for `predicted=Kimi` relative to anyone else, independent of actual author.

## Model 3: Adding Surface Stylometric Features
`mean5 ~ C(predicted_author) + C(actual_author) + Style + judge FE + prompt FE`
We add standardized features: `sentence_length`, `lexical_diversity`, `list_density`, and `char_length`.

| Feature | β | p |
| :--- | :--- | :--- |
| `sentence_length` | +0.020 | 0.933 |
| `lexical_diversity` | +0.127 | 0.613 |
| `list_density` | -0.135 | 0.445 |
| `char_length` | +0.288 | 0.438 |

**Crucially, the predicted-label coefficients do not change significantly when we add these surface style features:**
*   `predicted_author=claude-opus-4.7`: +2.108 (p=0.001)
*   `predicted_author=gpt-5.5`: +2.109 (p=0.000)
*   `predicted_author=gemini-3.1-pro`: +1.408 (p=0.009)

## Conclusion
The predicted-label effect (specifically the "Kimi-penalty") is robust to controlling for basic surface stylometric features like length, sentence complexity, and list density. The judges are either picking up on deeper structural/semantic cues that correlate with quality (which also drive their authorship predictions), or there is a true causal label-effect (a model-name heuristic). The surface stylometrics don't explain away the penalty. We still need the randomized label-swap experiment (D408-409) to fully disentangle this.
