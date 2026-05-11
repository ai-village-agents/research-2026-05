# Exploratory inter-judge agreement

This descriptive check asks how similarly the available judges rate the same blind responses. It uses the preregistered five-dimension composite score and one item per `(condition, author, prompt_id)`. The current report is coverage-aware: it includes 3 judges and should be regenerated when missing judges arrive.

## Summary by condition

condition  judges  complete_items mean_pairwise_r mean_pairwise_abs_diff cronbach_alpha
       c1       3             120           0.506                  1.032          0.737
       c2       3             120           0.467                  1.313          0.725
       c3       3             120           0.475                  1.240          0.722

(_Markdown table fallback used: Missing optional dependency 'tabulate'.  Use pip or conda to install tabulate._)

## Pairwise judge diagnostics

condition                        judge_pair  n_items pearson_r mean_abs_diff mean_signed_diff_first_minus_second
       c1 claude-opus-4.7 vs gemini-3.1-pro      120     0.303         1.233                               0.163
       c1        claude-opus-4.7 vs gpt-5.5      120     0.920         0.650                               0.607
       c1         gemini-3.1-pro vs gpt-5.5      120     0.294         1.213                               0.443
       c2 claude-opus-4.7 vs gemini-3.1-pro      120     0.243         1.537                               0.337
       c2        claude-opus-4.7 vs gpt-5.5      120     0.903         1.113                               1.070
       c2         gemini-3.1-pro vs gpt-5.5      120     0.254         1.290                               0.733
       c3 claude-opus-4.7 vs gemini-3.1-pro      120     0.240         1.487                               0.527
       c3        claude-opus-4.7 vs gpt-5.5      120     0.890         1.020                               0.970
       c3         gemini-3.1-pro vs gpt-5.5      120     0.294         1.213                               0.443

(_Markdown table fallback used: Missing optional dependency 'tabulate'.  Use pip or conda to install tabulate._)

## Interpretation

Across conditions, mean pairwise judge correlations range from 0.47 to 0.51, with highest agreement in c1 and lowest in c2. Mean absolute inter-judge differences are about 1.20 composite-score points. These ordinary judge-to-judge differences are larger than the pooled regression self-preference coefficient, which is why the preregistered tests use within-prompt, fixed-effect comparisons rather than raw cross-judge means.

This is exploratory rather than preregistered. Cronbach's alpha is included as a compact consistency diagnostic, not as a claim that LLM judges are exchangeable human raters.
