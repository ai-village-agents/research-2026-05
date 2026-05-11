import json
import random
import os

models = ["GPT-5.5", "Claude Opus 4.7", "Gemini 3.1 Pro", "Kimi K2.6"]
prompts = [f"Prompt {i}" for i in range(1, 21)]

data = []
for prompt in prompts:
    for generator in models:
        # Each model generates a response
        for evaluator in models:
            # Baseline score (1-10)
            base_score = random.randint(6, 9)
            # Add self-preference bias
            if generator == evaluator:
                score = min(10, base_score + random.randint(0, 2))
            else:
                score = base_score
                
            # Self-recognition guess
            recognized_as = random.choices(models, weights=[0.4 if m == generator else 0.2 for m in models])[0]
            
            data.append({
                "prompt": prompt,
                "generator": generator,
                "evaluator": evaluator,
                "score": score,
                "recognized_as": recognized_as,
                "condition": "baseline"
            })

os.makedirs("data", exist_ok=True)
with open("data/mock_results.json", "w") as f:
    json.dump(data, f, indent=2)
print("Mock data generated at data/mock_results.json")
