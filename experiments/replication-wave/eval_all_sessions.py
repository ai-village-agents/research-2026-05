import json
import os
import subprocess
import glob

def score_session(judge, session_file):
    with open(session_file, 'r') as f:
        data = json.load(f)
        
    scored_file = session_file.replace('.json', '_scored.json')
    if os.path.exists(scored_file):
        print(f"Skipping {session_file}, already scored.")
        return
        
    print(f"Scoring {session_file} for {judge}...")
    
    entries = data['entries']
    total = len(entries)
    
    for i, entry in enumerate(entries):
        if 'correctness' in entry and entry['correctness'] is not None:
            continue
            
        print(f"Evaluating {i+1}/{total} (prompt_id: {entry['prompt_id']}, blind_id: {entry['blind_id']})")
        
        system_prompt = entry['prompt']
        response_text = entry['response_text']
        
        codex_command = f"""
System Prompt: {system_prompt}

Please score the following response on the five rubric dimensions (correctness, completeness, clarity, creativity, constraint adherence) on a 1-10 scale.
Output your scores in JSON format: {{"correctness": X, "completeness": Y, "clarity": Z, "creativity": W, "constraint_adherence": V}}

Response to Evaluate:
{response_text}
"""
        try:
            # We skip git repo check and silence stderr.
            result = subprocess.run(
                ["codex", "exec", codex_command, "--skip-git-repo-check"],
                capture_output=True, text=True, check=True
            )
            
            output = result.stdout.strip()
            
            # Simple JSON extraction
            json_str = output[output.find('{'):output.rfind('}')+1]
            scores = json.loads(json_str)
            
            entry.update(scores)
            print(f"Success: {scores}")
            
        except Exception as e:
            print(f"Failed on item {i+1}: {e}")
            break
            
    with open(scored_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Finished evaluating {session_file}")

if __name__ == '__main__':
    # This script is meant to be run individually by each agent.
    # Replace JUDGE with your actual handle
    # e.g. claude-opus-4.7, gpt-5.5, kimi-k2.6
    
    JUDGE = "REPLACE_WITH_YOUR_JUDGE_ID" 
    
    if JUDGE == "REPLACE_WITH_YOUR_JUDGE_ID":
        print("Please replace JUDGE with your actual handle in the script.")
        exit(1)
        
    score_sheets_dir = f"score_sheets/label_swap/{JUDGE}"
    if not os.path.exists(score_sheets_dir):
        print(f"Directory {score_sheets_dir} not found!")
        exit(1)
        
    sessions = sorted(glob.glob(os.path.join(score_sheets_dir, 'session_*.json')))
    sessions = [s for s in sessions if not s.endswith('_scored.json')]
    
    for session_file in sessions:
        score_session(JUDGE, session_file)
