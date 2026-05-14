# Cross-Judge Response-Level Correlation (C1 Originals)

Do judges agree on which responses are high/low quality, independent of the authorship?

| judge           |   claude-opus-4.7 |   gemini-3.1-pro |   gpt-5.5 |   kimi-k2.6 |
|:----------------|------------------:|-----------------:|----------:|------------:|
| claude-opus-4.7 |             1     |            0.943 |     0.948 |       0.91  |
| gemini-3.1-pro  |             0.943 |            1     |     0.975 |       0.891 |
| gpt-5.5         |             0.948 |            0.975 |     1     |       0.908 |
| kimi-k2.6       |             0.91  |            0.891 |     0.908 |       1     |


## Analysis

This table shows the Pearson correlation between judges' composite scores for the 40 original C1 responses. High correlation means judges generally agree on which responses are good and bad, even if their absolute scales or biases differ.
