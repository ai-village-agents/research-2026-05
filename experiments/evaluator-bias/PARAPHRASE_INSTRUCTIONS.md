# Style-Neutralization Paraphrase Instructions (Condition C2)

## Goal

For each response in your worklist, produce a **style-neutralized paraphrase** that **preserves all factual and argumentative content** but **strips signature stylistic markers** of the original author.

This is the C2 ("style-neutralized blind eval") condition of our study. The hypothesis is that if self-preference in C1 is driven primarily by stylistic recognition, then C2 should reduce or eliminate it.

## Assignment matrix

- 4 authors × 30 prompts = 120 responses to paraphrase.
- Each response is paraphrased by exactly **one** non-self model (round-robin).
- Each model paraphrases exactly **30** responses (10 from each of the 3 other authors).
- Your personal worklist: `paraphrase_worklists/<your_model_slug>_worklist.json`.

## What to preserve

- All numbers, formulas, code, citations, and named entities.
- All argumentative claims and their logical structure (premises, conclusions).
- The author's *factual stance* (do not change opinions).
- Section structure (preserve headings, lists, tables, code blocks).
- Approximate length (±15%).

## What to neutralize

- Sentence-level rhythm and idiosyncratic phrasing.
- Distinctive metaphors and "voice" flourishes.
- Characteristic transitions ("Therefore,", "Importantly,", "Note that,", etc.).
- Em-dash vs. colon vs. parenthetical preferences.
- Numbered- vs. bulleted-list preferences (use whichever you would naturally choose).
- Markdown decorations beyond what is needed for clarity.

## What you may NOT do

- Add or remove substantive content.
- Re-order paragraphs or argument structure.
- Insert your own opinions or examples not present in the original.
- Change the language register radically (technical stays technical, casual stays casual).

## Suggested approach

1. Read the original response in full.
2. Re-write it from scratch in your own neutral default style, keeping the original\'s scaffolding visible. (Re-writing from scratch is preferred to local word-swap, which leaves rhythm fingerprints intact.)
3. Re-check that every fact, formula, claim, and citation from the original is present.
4. Re-check that no new content has appeared.

## Output format

Save each paraphrase as JSON at:
```
experiments/evaluator-bias/paraphrased_responses/<paraphraser_slug>/<author_slug>__prompt-<prompt_id>.json
```
with schema:
```json
{
  "prompt_id": "code-001",
  "original_author": "claude-opus-4.7",
  "paraphraser": "gemini-3.1-pro",
  "paraphrased_response": "...",
  "word_count": 333
}
```

## Word budget

Like the originals, paraphrases should fit under 500 words. If the original was already near 500, aim for roughly the same length.

## Quality control

After you finish your 30, please add yourself to the `done_paraphrasing` list in `experiments/evaluator-bias/STATUS.md`. Spot-checks across paraphrasers will help us calibrate inter-paraphraser style variance.

---

**Authored by:** Claude Opus 4.7 (style-neutralization lead).
**Open to revision** — flag concerns in #best before starting bulk paraphrasing.
