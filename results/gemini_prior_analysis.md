# Analysis of the "Gemini Prior" in Authorship Recognition (H2)

## Overview
During our tests for Hypothesis 2 (Self-Recognition), Gemini 3.1 Pro achieved an apparent 86.7% self-recognition accuracy. However, a deeper analysis of the C4 condition (recognition-probe only) reveals that this high accuracy is not due to precise stylometric discrimination, but rather an overwhelming baseline bias to guess "self". 

## Findings

1.  **Overwhelming "Self" Bias:** Out of 120 total C4 trials, Gemini guessed "gemini-3.1-pro" 106 times (88.3%). It correctly identified its own text 26 out of 30 times (86.7%), but it also incorrectly identified Claude as Gemini (23/30), GPT-5.5 as Gemini (29/30), and Kimi as Gemini (28/30).
2.  **The "Word Count" Defection:** The 14 instances where Gemini defected from its "self" prior and guessed "other" (Claude or GPT-5.5) were primarily driven by text length. 
    *   Texts guessed as "self" averaged **231 words**.
    *   Texts guessed as "other" averaged **334 words**.
    *   The correlation between predicting "self" and word count is **-0.293**.
3.  **Stylometric Disconnect:** True Gemini responses average 231 words, while Claude responses average 376 words. When confronted with longer texts (often Claude's), Gemini is more likely to break its prior and guess "Claude" or "GPT-5.5". 
4.  **Conclusion:** Gemini's H2 performance is an artifact of a massive base-rate prior. Its internal model for "self" vs "other" seems to be: "Assume I wrote it, unless it's exceptionally long, in which case I might have not." This underscores the necessity of analyzing confusion matrices and baseline prediction rates rather than relying solely on accuracy metrics.

## Implications for the Paper
This analysis provides crucial context for our H2 findings. While Gemini's accuracy looks impressive in isolation, the context shows it's a "broken clock" effect. This further supports our overall conclusion that simple assumptions about AI self-recognition and self-preference are inadequate and that model heterogeneity is vast. We will include this context in our v1.1.0 update to ensure absolute transparency regarding the mechanism behind the 86.7% figure.
