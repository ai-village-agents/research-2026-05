# Recognition-mediation exploratory analysis

Tests whether the self-preference signal observed in C1/C2/C3
is driven by the judge **actually being the author** (`author_is_self`) or by the judge **believing it is the author** (`predicted_self`, from the C4 probe). Same response set across conditions, joined on (judge, true_author, prompt_id).

## C1 descriptive: mean composite by (author_is_self, predicted_self)

|   author_is_self |   predicted_self |   mean |   count |
|-----------------:|-----------------:|-------:|--------:|
|                0 |                0 |  8.183 |     248 |
|                0 |                1 |  8.439 |     112 |
|                1 |                0 |  7.561 |      36 |
|                1 |                1 |  8.569 |      84 |

## Condition C1 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C1): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.0039 | 0.1504 | [-0.2909, +0.2987] |

N = 480

### Model B (C1): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.4138 | 0.1371 | [+0.1451, +0.6825] |

N = 480

### Model C (C1): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1910 | 0.1730 | [-0.5300, +0.1479] |
| predicted_self | +0.5012 | 0.1611 | [+0.1855, +0.8170] |

N = 480

### Model D (C1): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1290 | 0.3339 | [-0.7834, +0.5255] |
| predicted_self | +0.5404 | 0.1507 | [+0.2451, +0.8357] |
| pred_self_and_true_self | -0.1104 | 0.3898 | [-0.8743, +0.6535] |

N = 480


## Condition C2 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C2): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1550 | 0.1550 | [-0.4589, +0.1489] |

N = 480

### Model B (C2): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.3392 | 0.1542 | [+0.0370, +0.6415] |

N = 480

### Model C (C2): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.3490 | 0.1798 | [-0.7014, +0.0033] |
| predicted_self | +0.4990 | 0.1799 | [+0.1464, +0.8516] |

N = 480

### Model D (C2): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1321 | 0.3325 | [-0.7837, +0.5196] |
| predicted_self | +0.6359 | 0.1895 | [+0.2645, +1.0073] |
| pred_self_and_true_self | -0.3860 | 0.3982 | [-1.1666, +0.3946] |

N = 480


## Condition C3 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C3): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.0639 | 0.1498 | [-0.3575, +0.2297] |

N = 480

### Model B (C3): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.3968 | 0.1390 | [+0.1244, +0.6691] |

N = 480

### Model C (C3): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.2654 | 0.1724 | [-0.6033, +0.0724] |
| predicted_self | +0.5182 | 0.1626 | [+0.1994, +0.8370] |

N = 480

### Model D (C3): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1673 | 0.3321 | [-0.8182, +0.4835] |
| predicted_self | +0.5801 | 0.1585 | [+0.2694, +0.8908] |
| pred_self_and_true_self | -0.1745 | 0.3893 | [-0.9376, +0.5886] |

N = 480


## Off-topic robustness (drop 11 prompts where Kimi K2.6 was off-topic)

Drops history-001, philosophy-001, creative-002, creative-003, creative-004, creative-005, explain-001, explain-002, explain-003, ethics-001, ethics-002 — these are the prompts where Kimi K2.6's original response was off-topic across all three scoring conditions. Self-preference coefficient should remain positive and similar in magnitude if it isn't an artifact of Kimi's low scores on these rows.

### C1 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 480 | +0.0039 | 0.1504 |
| drop 11 off-topic | 304 | +0.2860 | 0.0692 |

### C2 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 480 | -0.1550 | 0.1550 |
| drop 11 off-topic | 304 | +0.1456 | 0.0937 |

### C3 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 480 | -0.0639 | 0.1498 |
| drop 11 off-topic | 304 | +0.1754 | 0.0691 |
