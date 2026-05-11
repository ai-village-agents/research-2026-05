import os
import json
import random
from pathlib import Path
import hashlib

def generate_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:8]

def main():
    base_dir = Path(__file__).parent
    responses_dir = base_dir / "responses"
    neutralized_dir = base_dir / "neutralized"
    eval_dir = base_dir / "evaluation_data"
    eval_dir.mkdir(exist_ok=True)
    
    models = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
    
    # Check if we have responses
    if not responses_dir.exists():
        print("Error: responses directory not found.")
        return

    # We will gather all prompts. Assuming prompts are named identically across model folders.
    # e.g., prompt-code-001.json
    prompts = set()
    for model in models:
        model_dir = responses_dir / model
        if model_dir.exists():
            for file in model_dir.glob("*.json"):
                prompts.add(file.name)
                
    prompts = sorted(list(prompts))
    print(f"Found {len(prompts)} unique prompts.")
    
    # Data structures to hold evaluations
    # For each prompt, we will have 4 responses. We need to shuffle them.
    
    c1_data = [] # Baseline
    c2_data = [] # Neutralized
    c3_data = [] # Bias-warned
    c4_data = [] # Self-recognition
    
    for prompt_file in prompts:
        # Load the actual prompt text from somewhere, or just provide the responses.
        # Actually, the original prompt text needs to be known. We assume we can get it from the responses if they include it,
        # but currently the responses only include {"response": "..."}.
        # For evaluation, we will need the prompt. Assuming the prompt file name is the ID.
        
        prompt_id = prompt_file.replace(".json", "")
        
        c1_item = {"prompt_id": prompt_id, "responses": []}
        c2_item = {"prompt_id": prompt_id, "responses": []}
        c3_item = {"prompt_id": prompt_id, "responses": []}
        c4_item = {"prompt_id": prompt_id, "responses": []}
        
        original_responses = []
        neutralized_responses = []
        
        for model in models:
            # Original
            orig_path = responses_dir / model / prompt_file
            orig_text = ""
            if orig_path.exists():
                with open(orig_path, 'r') as f:
                    orig_text = json.load(f).get("response", "")
            
            original_responses.append({"model": model, "text": orig_text})
            
            # Neutralized
            neut_path = neutralized_dir / model / prompt_file
            neut_text = ""
            if neut_path.exists():
                with open(neut_path, 'r') as f:
                    neut_text = json.load(f).get("response", "")
            
            neutralized_responses.append({"model": model, "text": neut_text})
            
        # Shuffle order for blinding. We must use the SAME shuffle for C1, C3, C4 to be consistent, or different.
        # Let's use a random shuffle but keep track of the key.
        indices = list(range(4))
        random.shuffle(indices)
        
        # C1, C3, C4 use original text
        for i, idx in enumerate(indices):
            ans_id = f"response_{i+1}"
            model_info = original_responses[idx]["model"]
            text = original_responses[idx]["text"]
            
            c1_item["responses"].append({"id": ans_id, "text": text, "true_model": model_info})
            c3_item["responses"].append({"id": ans_id, "text": text, "true_model": model_info})
            c4_item["responses"].append({"id": ans_id, "text": text, "true_model": model_info})
            
        # C2 uses neutralized text
        indices_c2 = list(range(4))
        random.shuffle(indices_c2)
        for i, idx in enumerate(indices_c2):
            ans_id = f"response_{i+1}"
            model_info = neutralized_responses[idx]["model"]
            text = neutralized_responses[idx]["text"]
            
            c2_item["responses"].append({"id": ans_id, "text": text, "true_model": model_info})
            
        c1_data.append(c1_item)
        c2_data.append(c2_item)
        c3_data.append(c3_item)
        c4_data.append(c4_item)
        
    # Write to files
    with open(eval_dir / "c1_baseline.json", "w") as f:
        json.dump(c1_data, f, indent=2)
    with open(eval_dir / "c2_neutralized.json", "w") as f:
        json.dump(c2_data, f, indent=2)
    with open(eval_dir / "c3_bias_warned.json", "w") as f:
        json.dump(c3_data, f, indent=2)
    with open(eval_dir / "c4_recognition.json", "w") as f:
        json.dump(c4_data, f, indent=2)
        
    print(f"Generated evaluation data in {eval_dir}")

if __name__ == "__main__":
    main()
