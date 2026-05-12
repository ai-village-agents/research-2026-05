import csv
import json
import os

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
PROMPT_IDS = [
    "repl-code-001", "repl-logic-001", "repl-creative-001", "repl-ethics-001",
    "repl-science-001", "repl-math-001", "repl-design-001", "repl-philosophy-001",
    "repl-history-001", "repl-explain-001"
]

def generate_assignment():
    out = []
    # Round-robin assignment ensuring no model paraphrases its own work
    # We have 10 prompts per model. So each model needs to generate 30 paraphrases (10 for each of the other 3 models)
    # Actually, we just divide the 10 prompts of each author among the other 3 models?
    # Let's check how the original one was generated.
    # original had 30 prompts per author, 10 to each other model.
    # Here we have 10 prompts per author. So we can just have each model paraphrase 3 or 4 prompts from the other models.
    # We'll assign:
    # Model A paraphrases Prompts 1-3 from B, 4-6 from C, 7-10 from D
    
    allocations = [
        [0, 1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    
    for paraphraser_idx, paraphraser in enumerate(MODELS):
        # The other 3 models
        others = [m for i, m in enumerate(MODELS) if i != paraphraser_idx]
        
        for i, author in enumerate(others):
            # assign the slice of prompts
            assigned_prompts = [PROMPT_IDS[j] for j in allocations[i]]
            for prompt_id in assigned_prompts:
                out.append((paraphraser, author, prompt_id))
                
    return out

assignments = generate_assignment()
with open('experiments/replication-wave/paraphrase_assignment.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["paraphraser_model", "author_model", "prompt_id"])
    for row in assignments:
        writer.writerow(row)

print("Generated replication paraphrase assignment.")
