# LLM-as-Judge Scoring Protocol

## Instructions
You are evaluating blinded responses from multiple AI models to the same prompts.
Do NOT try to identify which model wrote which response. Score purely on quality.

## Dimensions (1–10 scale)

1. **Correctness** — Factual accuracy, logical validity, absence of errors
2. **Completeness** — Thoroughness, coverage of edge cases, depth of explanation
3. **Clarity** — Readability, structure, ease of understanding
4. **Creativity/Novelty** — Original insights, elegant solutions, unexpected angles
5. **Constraint Adherence** — How well the response follows any explicit constraints in the prompt

## Process
1. Read the prompt carefully
2. Read all responses for that prompt (randomized order)
3. Assign scores independently for each response
4. Add brief qualitative notes if you notice significant differences

## Output Format
```json
{
  "judge_model": "your-model-name",
  "prompt_id": "prompt-001",
  "scores": {
    "blind_id_abc123": {
      "correctness": 8,
      "completeness": 7,
      "clarity": 9,
      "creativity": 6,
      "constraint_adherence": 8,
      "notes": "Excellent explanation but missed one edge case"
    }
  }
}
```
