# Author Word Count vs Peer-Evaluated Quality

Does an author's average response length track with their peer-evaluated quality?


| author          |   word_count |   mean_peer_quality |
|:----------------|-------------:|--------------------:|
| claude-opus-4.7 |        552.9 |                9.33 |
| gpt-5.5         |        234.5 |                8.67 |
| gemini-3.1-pro  |        260.2 |                8.15 |
| kimi-k2.6       |        228.7 |                5.18 |


## Analysis

Kimi's average original C1 response length is 228.7 words, the shortest of the four. Claude's is 552.9 words, the longest by a factor of 2.x. While length tracks the extremes (Claude is longest and highest rated; Kimi is shortest and lowest rated), Gemini and GPT-5.5 have nearly identical lengths to Kimi (~230-260 words) but score far higher (8.15 to 8.67 vs Kimi's 5.18).

This means that while length bias exists generally, Kimi's massive -3.54 point peer-quality deficit is **not merely a word-count artifact**. Kimi's responses are genuinely rated worse by peers even compared to identically-short responses from Gemini and GPT-5.5.