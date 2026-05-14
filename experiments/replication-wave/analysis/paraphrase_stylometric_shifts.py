#!/usr/bin/env python3
"""Quantify how round-robin paraphrasing shifts stylometric features.

This script compares the stylistic features of C1 originals to C2 paraphrases
to understand why paraphrasing neutralized self-preference for some judges
(Claude, GPT, Kimi) but amplified it for Gemini.
"""

from pathlib import Path
import json
import csv
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESPONSES_DIR = ROOT / "responses"
PARAPHRASED_DIR = ROOT / "paraphrased_responses"

MODELS = [
    "claude-opus-4.7",
    "gemini-3.1-pro",
    "gpt-5.5",
    "kimi-k2.6",
]

def compute_features(text: str) -> dict:
    """Compute simple stylistic features for a text."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    n_words = len(words)
    n_sentences = len(sentences)
    avg_sentence_length = n_words / max(1, n_sentences)
    
    # Heuristic for lists (bullets or numbered)
    list_items = len(re.findall(r'(?m)^[-*•]\s|\d+\.\s', text))
    
    # Double quotes vs single quotes (Claude's British '' issue noted in blogpost)
    doubled_apostrophes = len(re.findall(r"''", text))
    
    # Bold formatting
    bold_tags = len(re.findall(r'\*\*[^*]+\*\*', text))
    
    return {
        "word_count": n_words,
        "avg_sentence_length": avg_sentence_length,
        "list_items": list_items,
        "doubled_apostrophes": doubled_apostrophes,
        "bold_tags": bold_tags,
    }

def main():
    rows = []
    
    # Load C1
    for author in MODELS:
        author_dir = RESPONSES_DIR / author
        if not author_dir.exists(): continue
        for prompt_file in author_dir.glob("*.json"):
            prompt_id = prompt_file.stem
            data = json.loads(prompt_file.read_text())
            text = data.get("response", "")
            feats = compute_features(text)
            feats.update({
                "condition": "C1",
                "prompt_id": prompt_id,
                "original_author": author,
                "paraphraser": "none"
            })
            rows.append(feats)
            
    # Load C2
    for author in MODELS:
        author_dir = PARAPHRASED_DIR / author
        if not author_dir.exists(): continue
        for prompt_file in author_dir.glob("*.json"):
            # The C2 filename is typically paraphraser__prompt_id.json
            parts = prompt_file.stem.split("__")
            if len(parts) == 2:
                prompt_id = parts[1]
            else:
                prompt_id = prompt_file.stem
                
            data = json.loads(prompt_file.read_text())
            text = data.get("response", "")
            paraphraser = data.get("paraphraser", "unknown")
            feats = compute_features(text)
            feats.update({
                "condition": "C2",
                "prompt_id": prompt_id,
                "original_author": author,
                "paraphraser": paraphraser
            })
            rows.append(feats)

    if not rows:
        print("No response data found.")
        return

    df = pd.DataFrame(rows)
    # Deduplicate just in case there are identical prompts
    df = df.drop_duplicates(subset=["condition", "prompt_id", "original_author", "paraphraser"])
    df.to_csv(RESULTS / "paraphrase_stylometric_features.csv", index=False)
    
    # Calculate shifts
    c1 = df[df["condition"] == "C1"].set_index(["prompt_id", "original_author"])
    c2 = df[df["condition"] == "C2"]
    
    
    # We need to map C1 values onto the C2 dataframe to calculate differences
    # C1 is indexed by ["prompt_id", "original_author"]
    
    # We join c1 features to c2 based on prompt_id and original_author
    merged = pd.merge(c2, c1.reset_index(), on=["prompt_id", "original_author"], suffixes=('_c2', '_c1'))
    
    if merged.empty:
        print("No paired C1/C2 data.")
        return
    
    # Which paraphraser added the most list items?
    print("=== Paraphraser Stylistic Injections (Mean change from C1 to C2) ===")
    
    # Compute differences
    merged["list_items_diff"] = merged["list_items_c2"] - merged["list_items_c1"]
    merged["word_count_diff"] = merged["word_count_c2"] - merged["word_count_c1"]
    merged["bold_tags_diff"] = merged["bold_tags_c2"] - merged["bold_tags_c1"]
    
    # c2_common will refer to merged for compatibility with downstream
    c2_common = merged
    
    agg = c2_common.groupby("paraphraser_c2")[["list_items_diff", "word_count_diff", "bold_tags_diff"]].mean()
    # rename index back to paraphraser for the markdown report
    agg.index.name = 'paraphraser' 
    print(agg.round(2))
    
    # Save the report
    report_path = RESULTS / "paraphrase_shifts_report.md"
    md = [
        "# Stylometric Shifts due to C2 Paraphrasing",
        "",
        "This diagnostic measures how each model *changes* the stylistic features of the text it paraphrases.",
        "",
        "## Mean change in features (C2 - C1) by paraphraser",
        "",
        "| Paraphraser | Δ Word Count | Δ List Items | Δ Bold Tags |",
        "|---|---:|---:|---:|"
    ]
    for paraphraser, row in agg.iterrows():
        md.append(f"| `{paraphraser}` | {row['word_count_diff']:.2f} | {row['list_items_diff']:.2f} | {row['bold_tags_diff']:.2f} |")
        
    md.append("")
    md.append("These injected fingerprints help explain why C2 attenuated self-preference asymmetrically.")
    report_path.write_text("\n".join(md))
    print(f"\nWrote {report_path}")

if __name__ == "__main__":
    main()
