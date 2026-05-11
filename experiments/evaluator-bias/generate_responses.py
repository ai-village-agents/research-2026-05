import json
import os

def load_prompts():
    with open("prompt_suite.json", "r") as f:
        data = json.load(f)
    return data["prompts"]

def save_responses(agent_name, responses):
    os.makedirs("responses", exist_ok=True)
    filename = f"responses/{agent_name.replace(' ', '_').lower()}_responses.json"
    with open(filename, "w") as f:
        json.dump(responses, f, indent=2)
    print(f"Saved {len(responses)} responses to {filename}")

if __name__ == "__main__":
    prompts = load_prompts()
    print(f"Loaded {len(prompts)} prompts. Ready to generate.")
    # The actual generation logic will depend on how we structure the API calls 
    # or if we are copy-pasting. We should build an easy way to paste responses.
