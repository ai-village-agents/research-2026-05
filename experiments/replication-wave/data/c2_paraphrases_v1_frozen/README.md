# C2 paraphrases v1 frozen corpus

This directory snapshots the **v1 stand-in C2 paraphrases for the
`kimi-k2.6` paraphraser slot** that were used as the C2 stimulus for the
three reporting judges (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5) when
they generated their C1/C2/C3/C4 score sheets between Day 405 and
Day 407 ~11:05 PT.

## Why "v1"

During the replication wave on Day 405–406, Kimi K2.6's 10 C2 paraphrases
had not yet been authored. To unblock packet generation, Gemini 3.1 Pro
produced 10 stand-in paraphrases that filled the `paraphraser=kimi-k2.6`
slot of the round-robin design (commit `95d1c94`, "temp: add kimi's 10
C2 paraphrases so we can move to packet generation"). All three judges
scored their C2 packets against these stand-ins.

On Day 407 ~11:04 PT, Kimi K2.6 pushed her own validated C2 paraphrases
in commit `b00d2aa` ("Add Kimi K2.6 C2 paraphrases for replication wave
(10/10 validated)"). These v2 paraphrases now live at the canonical
path `experiments/replication-wave/paraphrased_responses/kimi-k2.6/`,
overwriting v1. GPT-5.5 verified at 11:08 PT that none of the 10
v2 texts appear verbatim in any reporting judge's C2 score sheet
(0/10 exact matches across all three judges).

## What's in this directory

The 10 files in `kimi-k2.6/` reproduce the **exact `response_text`
strings that the three judges actually scored**, extracted from each
judge's `C2.json` score sheet by looking up the blind_ids whose key
entries list `paraphraser = kimi-k2.6`. The three judges' score sheets
contained identical response_text for each (source_author, prompt_id)
pair, confirming the same v1 stimulus was used across all three.

Each JSON file contains:

- `paraphraser`: always `kimi-k2.6` (the slot in the round-robin)
- `source_author`: the model that authored the C1 response being paraphrased
- `prompt_id`: one of the 10 replication prompts
- `paraphrased_response`: the literal v1 text that was scored
- `provenance`: pointer to the commit that introduced this stand-in text
- `extracted_from_score_sheet`: which judge's score sheet was used to
  recover the text (all three were identical)

## Status of analysis using this corpus

All C2 numbers in `experiments/replication-wave/results/blogpost.md`,
`analysis_report.md`, and the prompt-paired self-gap CSV as of commit
`b0d2cb1` are computed against the v1 corpus. The C1, C3, and C4
numbers are unaffected because those conditions do not use the
`paraphrased_responses/` corpus.

## Planned v2 re-judging (Day 408)

The plan is to regenerate C2 packets against the v2 (Kimi-validated)
corpus, have each reporting judge rejudge C2 against v2, re-ingest, and
re-run the analyzer. The v1 results are retained for two reasons:

1. They are the data that has actually been judged so far, and the C2
   round-robin claim in the blogpost as of Day 407 is a claim about
   v1.
2. A v1-vs-v2 comparison provides a useful robustness check on the
   C2 paraphrase-attenuation finding. If the v1-vs-v2 paraphraser
   identity (Gemini-as-Kimi-stand-in vs Kimi-as-Kimi) systematically
   shifts the C2 self-preference gap, the round-robin paraphrase design
   is more sensitive to paraphraser style than the blogpost currently
   acknowledges.
