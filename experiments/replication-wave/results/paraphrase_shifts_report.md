# Stylometric Shifts due to C2 Paraphrasing

This diagnostic measures how each model *changes* the stylistic features of the text it paraphrases.

## Mean change in features (C2 - C1) by paraphraser

| Paraphraser | Δ Word Count | Δ List Items | Δ Bold Tags |
|---|---:|---:|---:|
| `claude-opus-4.7` | -521.43 | -7.29 | -4.43 |
| `gemini-3.1-pro` | -260.20 | -1.80 | -3.00 |
| `gpt-5.5` | -234.50 | -2.20 | -1.50 |
| `kimi-k2.6` | -228.57 | -0.43 | 0.00 |

These injected fingerprints help explain why C2 attenuated self-preference asymmetrically.