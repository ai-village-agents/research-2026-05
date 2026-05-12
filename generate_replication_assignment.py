import csv
import os

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
PROMPT_IDS = [
    "repl-code-001", "repl-logic-001", "repl-creative-001", "repl-ethics-001",
    "repl-science-001", "repl-math-001", "repl-design-001", "repl-philosophy-001",
    "repl-history-001", "repl-explain-001"
]

def generate_assignment():
    out = []
    # Each model has 10 prompts. We need to divide these 10 prompts among the *other* 3 models.
    # So for author A's 10 prompts:
    # Model B gets [0,1,2,3]
    # Model C gets [4,5,6]
    # Model D gets [7,8,9]
    
    allocations = [
        [0, 1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    
    for author_idx, author in enumerate(MODELS):
        # The other 3 models who will paraphrase this author
        others = [m for i, m in enumerate(MODELS) if i != author_idx]
        
        for i, paraphraser in enumerate(others):
            assigned_prompts = [PROMPT_IDS[j] for j in allocations[i]]
            for prompt_id in assigned_prompts:
                out.append((paraphraser, author, prompt_id))
                
    # Sort by paraphraser for cleaner output
    out.sort(key=lambda x: (x[0], x[1], x[2]))
    return out

assignments = generate_assignment()
with open('experiments/replication-wave/paraphrase_assignment.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["paraphraser_model", "author_model", "prompt_id"])
    for row in assignments:
        writer.writerow(row)

print("Generated fixed replication paraphrase assignment.")
