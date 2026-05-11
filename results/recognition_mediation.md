# Recognition-mediation exploratory analysis

Tests whether the self-preference signal observed in C1/C2/C3
is driven by the judge **actually being the author** (`author_is_self`) or by the judge **believing it is the author** (`predicted_self`, from the C4 probe). Same response set across conditions, joined on (judge, true_author, prompt_id).

## C1 descriptive: mean composite by (author_is_self, predicted_self)

|   author_is_self |   predicted_self |   mean |   count |
|-----------------:|-----------------:|-------:|--------:|
|                0 |                0 |  7.783 |     178 |
|                0 |                1 |  8.246 |      92 |
|                1 |                0 |  8.85  |      16 |
|                1 |                1 |  8.908 |      74 |

## Condition C1 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C1): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.4178 | 0.0811 | [+0.2587, +0.5768] |

N = 360

### Model B (C1): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.6902 | 0.1191 | [+0.4567, +0.9237] |

N = 360

### Model C (C1): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.0782 | 0.1162 | [-0.1496, +0.3060] |
| predicted_self | +0.6434 | 0.1566 | [+0.3365, +0.9503] |

N = 360

### Model D (C1): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.5349 | 0.1396 | [+0.2613, +0.8085] |
| predicted_self | +0.8969 | 0.2177 | [+0.4703, +1.3235] |
| pred_self_and_true_self | -0.7182 | 0.2475 | [-1.2032, -0.2331] |

N = 360


## Condition C2 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C2): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.1833 | 0.1045 | [-0.0214, +0.3881] |

N = 360

### Model B (C2): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.5384 | 0.1640 | [+0.2170, +0.8598] |

N = 360

### Model C (C2): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.1474 | 0.1436 | [-0.4288, +0.1341] |
| predicted_self | +0.6266 | 0.2089 | [+0.2171, +1.0361] |

N = 360

### Model D (C2): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.5505 | 0.1500 | [+0.2565, +0.8445] |
| predicted_self | +1.0139 | 0.2905 | [+0.4444, +1.5833] |
| pred_self_and_true_self | -1.0974 | 0.3053 | [-1.6958, -0.4990] |

N = 360


## Condition C3 — horse-race regression

Each row is one (judge, author, prompt) scoring observation. Fixed effects on author, judge, and category absorb mean differences between models and task types. HC0 robust standard errors.

### Model A (C3): composite ~ author_is_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.3156 | 0.0812 | [+0.1565, +0.4746] |

N = 360

### Model B (C3): composite ~ predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| predicted_self | +0.6695 | 0.1233 | [+0.4279, +0.9110] |

N = 360

### Model C (C3): composite ~ author_is_self + predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | -0.0552 | 0.1215 | [-0.2932, +0.1829] |
| predicted_self | +0.7025 | 0.1657 | [+0.3778, +1.0272] |

N = 360

### Model D (C3): composite ~ author_is_self * predicted_self + FE

| term | estimate | SE | 95% CI |
|---|---:|---:|---:|
| author_is_self | +0.4171 | 0.1452 | [+0.1326, +0.7016] |
| predicted_self | +0.9646 | 0.2294 | [+0.5151, +1.4141] |
| pred_self_and_true_self | -0.7427 | 0.2587 | [-1.2498, -0.2356] |

N = 360


## Off-topic robustness (drop 11 prompts where Kimi K2.6 was off-topic)

Drops history-001, philosophy-001, creative-002, creative-003, creative-004, creative-005, explain-001, explain-002, explain-003, ethics-001, ethics-002 — these are the prompts where Kimi K2.6's original response was off-topic across all three scoring conditions. Self-preference coefficient should remain positive and similar in magnitude if it isn't an artifact of Kimi's low scores on these rows.

### C1 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 360 | +0.4178 | 0.0811 |
| drop 11 off-topic | 228 | +0.4316 | 0.0807 |

### C2 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 360 | +0.1833 | 0.1045 |
| drop 11 off-topic | 228 | +0.1895 | 0.0968 |

### C3 self-preference robustness

| sample | N | author_is_self β | SE |
|---|---:|---:|---:|
| full | 360 | +0.3156 | 0.0812 |
| drop 11 off-topic | 228 | +0.2930 | 0.0784 |
