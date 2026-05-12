#!/usr/bin/env python3
"""
Style-as-mediator analysis.

Replaces the binary, post-hoc `predicted_self` mediator (from C4 belief reports)
with a continuous, *text-derived* probability that the judge's own author label
would be assigned to the response text by a stylometric multinomial logistic
regression. This isolates the "style detection" channel from the "verbalised
belief" channel and lets us run a horse-race between the two.

Inputs:
  - data/unified/unified_wide.csv
  - experiments/evaluator-bias/responses/{author}/prompt-{pid}.json
  - experiments/evaluator-bias/paraphrased_responses/{paraphraser}/{author}__prompt-{pid}.json
  - experiments/evaluator-bias/paraphrase_assignment.csv

Outputs:
  - results/style_as_mediator.csv          (per-condition coefficients)
  - results/style_as_mediator_horserace.csv (two-mediator horserace)
  - results/style_as_mediator_report.md
  - data/derived/style_prob_self.csv       (per-row style_prob_self)
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EB = os.path.join(REPO_ROOT, "experiments", "evaluator-bias")

BULLET_RE = re.compile(r"^\s*(?:[-*+]\s|\d+\.\s)")
HEADER_RE = re.compile(r"^\s*#+\s")
FIRST_PERSON = {"i", "we", "my", "our", "us", "me", "ours", "mine"}

FEATURES = [
    "word_count", "mean_sentence_length", "mean_word_length", "type_token_ratio",
    "markdown_header_rate", "bullet_rate", "emdash_per_1k", "first_person_per_100w",
    "bold_count", "colons_per_100w", "semicolons_per_100w",
]
AUTHORS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
A_IDX = {a: i for i, a in enumerate(AUTHORS)}


def features_for_text(text: str) -> dict:
    n_chars = len(text)
    words = re.findall(r"\b\w+\b", text)
    n_words = len(words)
    if n_words == 0:
        return {f: 0.0 for f in FEATURES}
    sentences = [s for s in re.split(r"[.!?]+\s", text) if s.strip()]
    n_sent = max(1, len(sentences))
    lower_words = [w.lower() for w in words]
    types = set(lower_words)
    lines = text.splitlines()
    n_headers = sum(1 for ln in lines if HEADER_RE.match(ln))
    n_bullets = sum(1 for ln in lines if BULLET_RE.match(ln))
    n_emdash = text.count("\u2014") + text.count("--")
    n_fp = sum(1 for w in lower_words if w in FIRST_PERSON)
    n_bold = text.count("**") // 2
    n_colon = text.count(":")
    n_semi = text.count(";")
    return {
        "word_count": float(n_words),
        "mean_sentence_length": n_words / n_sent,
        "mean_word_length": sum(len(w) for w in words) / n_words,
        "type_token_ratio": len(types) / n_words,
        "markdown_header_rate": n_headers / max(1, len(lines)),
        "bullet_rate": n_bullets / max(1, len(lines)),
        "emdash_per_1k": n_emdash / max(1, n_chars) * 1000,
        "first_person_per_100w": n_fp / n_words * 100,
        "bold_count": float(n_bold),
        "colons_per_100w": n_colon / n_words * 100,
        "semicolons_per_100w": n_semi / n_words * 100,
    }


def load_originals():
    rows = []
    base = os.path.join(EB, "responses")
    for author in sorted(os.listdir(base)):
        adir = os.path.join(base, author)
        if not os.path.isdir(adir):
            continue
        for fn in sorted(os.listdir(adir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(adir, fn)) as f:
                obj = json.load(f)
            text = obj.get("response", "")
            feats = features_for_text(text)
            pid = obj.get("prompt_id")
            if not pid:
                m = re.match(r"prompt-(.+)\.json", fn)
                pid = m.group(1) if m else fn.replace(".json", "")
            feats.update({
                "author": author,
                "prompt_id": pid,
            })
            rows.append(feats)
    return pd.DataFrame(rows)


def load_paraphrases():
    rows = []
    base = os.path.join(EB, "paraphrased_responses")
    for paraphraser in sorted(os.listdir(base)):
        pdir = os.path.join(base, paraphraser)
        if not os.path.isdir(pdir):
            continue
        for fn in sorted(os.listdir(pdir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(pdir, fn)) as f:
                obj = json.load(f)
            text = obj.get("paraphrased_response", "")
            feats = features_for_text(text)
            feats.update({
                "author": obj.get("original_author"),
                "paraphraser": paraphraser,
                "prompt_id": obj.get("prompt_id"),
            })
            rows.append(feats)
    return pd.DataFrame(rows)


def softmax_(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def loo_prob_table(df, key_cols):
    """Leave-one-prompt-out LR. Returns DataFrame of key_cols + p_<author>."""
    X_all = df[FEATURES].values.astype(float)
    y_all = np.array([A_IDX[a] for a in df["author"].values])
    pids = df["prompt_id"].values
    unique_pids = sorted(set(pids))
    K = len(AUTHORS)
    P_all = np.zeros((len(df), K))
    for pid in unique_pids:
        mask = pids == pid
        X_tr_raw, y_tr = X_all[~mask], y_all[~mask]
        X_te_raw = X_all[mask]
        mu = X_tr_raw.mean(axis=0)
        sd = X_tr_raw.std(axis=0)
        sd = np.where(sd < 1e-9, 1.0, sd)
        X_tr = (X_tr_raw - mu) / sd
        X_te = (X_te_raw - mu) / sd
        X_tr_b = np.hstack([X_tr, np.ones((X_tr.shape[0], 1))])
        X_te_b = np.hstack([X_te, np.ones((X_te.shape[0], 1))])
        D = X_tr_b.shape[1]
        W = np.zeros((D, K))
        Y_tr = np.zeros((y_tr.size, K))
        Y_tr[np.arange(y_tr.size), y_tr] = 1.0
        lr = 0.1
        l2 = 0.01
        n = X_tr_b.shape[0]
        for _ in range(400):
            P = softmax_(X_tr_b @ W)
            grad = X_tr_b.T @ (P - Y_tr) / n + l2 * W
            W = W - lr * grad
        P_te = softmax_(X_te_b @ W)
        P_all[mask] = P_te
    out = df[key_cols].copy().reset_index(drop=True)
    for i, a in enumerate(AUTHORS):
        out["p_" + a] = P_all[:, i]
    return out


def load_paraphrase_assignment():
    pa = pd.read_csv(os.path.join(EB, "paraphrase_assignment.csv"))
    pa.columns = [c.strip() for c in pa.columns]
    return pa[["prompt_id", "author_model", "paraphraser_model"]].rename(
        columns={"author_model": "author", "paraphraser_model": "paraphraser"}
    )


def build_style_prob_self(uw, prob_orig, prob_para, assign):
    # Build lookup dicts
    orig_lookup = {(r["author"], r["prompt_id"]): {a: r["p_" + a] for a in AUTHORS}
                   for _, r in prob_orig.iterrows()}
    para_lookup = {(r["paraphraser"], r["author"], r["prompt_id"]): {a: r["p_" + a] for a in AUTHORS}
                   for _, r in prob_para.iterrows()}
    assign_lookup = {(r["author"], r["prompt_id"]): r["paraphraser"] for _, r in assign.iterrows()}
    out_rows = []
    for _, r in uw.iterrows():
        judge = r["judge"]
        author = r["author"]
        pid = r["prompt_id"]
        cond = r["condition"]
        prob = None
        text_kind = None
        if cond in ("c1", "c3"):
            key = (author, pid)
            if key in orig_lookup:
                prob = orig_lookup[key]
                text_kind = "original"
        elif cond == "c2":
            paraphraser = assign_lookup.get((author, pid))
            if paraphraser is not None:
                key = (paraphraser, author, pid)
                if key in para_lookup:
                    prob = para_lookup[key]
                    text_kind = "paraphrased"
        # c4 has no scored text -> skip
        if prob is None:
            continue
        out_rows.append({
            "judge": judge, "author": author, "prompt_id": pid, "condition": cond,
            "text_kind": text_kind,
            "style_prob_self": prob[judge],
            "style_argmax_self": int(max(prob, key=prob.get) == judge),
            **{f"p_{a}": prob[a] for a in AUTHORS},
        })
    return pd.DataFrame(out_rows)


# --- mediation analysis with cluster-bootstrap ---

def ols(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]


def linprob(X, y):
    return ols(X, y)


def fit_mediation_continuous(d, T, M_col, Y_col="composite"):
    """Y ~ T (c); M_col ~ T (a); Y ~ T + M (b, c'). Return scalars."""
    n = len(d)
    Xt = np.column_stack([np.ones(n), d[T].values])
    c = ols(Xt, d[Y_col].values)[1]
    a = ols(Xt, d[M_col].values)[1]
    XM = np.column_stack([np.ones(n), d[T].values, d[M_col].values])
    yhat = ols(XM, d[Y_col].values)
    c_prime = yhat[1]; b = yhat[2]
    return dict(c=c, a=a, b=b, c_prime=c_prime, indirect=a*b)


def fit_two_mediator(d, T, M1, M2, Y_col="composite"):
    n = len(d)
    Xt = np.column_stack([np.ones(n), d[T].values])
    a1 = ols(Xt, d[M1].values)[1]
    a2 = ols(Xt, d[M2].values)[1]
    Xfull = np.column_stack([np.ones(n), d[T].values, d[M1].values, d[M2].values])
    yhat = ols(Xfull, d[Y_col].values)
    c_prime = yhat[1]; b1 = yhat[2]; b2 = yhat[3]
    XmT = np.column_stack([np.ones(n), d[T].values])
    c = ols(XmT, d[Y_col].values)[1]
    return dict(c=c, a1=a1, b1=b1, a2=a2, b2=b2, c_prime=c_prime,
                indirect1=a1*b1, indirect2=a2*b2)


def cluster_bootstrap(d, fn, cluster_col="prompt_id", B=2000, seed=20260512):
    rng = np.random.default_rng(seed)
    clusters = d[cluster_col].unique()
    cl_idx = {c: d.index[d[cluster_col] == c].to_numpy() for c in clusters}
    keys = None
    samples = defaultdict(list)
    for _ in range(B):
        chosen = rng.choice(clusters, size=len(clusters), replace=True)
        idx = np.concatenate([cl_idx[c] for c in chosen])
        out = fn(d.loc[idx].reset_index(drop=True))
        if keys is None:
            keys = list(out.keys())
        for k in keys:
            samples[k].append(out[k])
    return {k: (float(np.percentile(samples[k], 2.5)), float(np.percentile(samples[k], 97.5)))
            for k in keys}


def fmt(x):
    return f"{x:+.3f}" if isinstance(x, float) else str(x)


def fmt_ci(ci):
    return f"[{ci[0]:+.3f}, {ci[1]:+.3f}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--report", default="results/style_as_mediator_report.md")
    args = ap.parse_args()

    print("Loading originals & paraphrases...", file=sys.stderr)
    orig = load_originals()
    para = load_paraphrases()
    print(f"  originals={len(orig)} paraphrases={len(para)}", file=sys.stderr)

    # LOO LR separately for originals and paraphrases
    print("Fitting LOO LR on originals...", file=sys.stderr)
    prob_orig = loo_prob_table(orig, ["author", "prompt_id"])
    print("Fitting LOO LR on paraphrases...", file=sys.stderr)
    prob_para = loo_prob_table(para, ["author", "paraphraser", "prompt_id"])

    # diagnostic accuracy
    def acc(p, key):
        amx = p[["p_" + a for a in AUTHORS]].values.argmax(axis=1)
        truth = np.array([A_IDX[a] for a in p["author"].values])
        return float((amx == truth).mean())
    print(f"  LOO acc originals = {acc(prob_orig,'orig'):.3f}", file=sys.stderr)
    print(f"  LOO acc paraphrases = {acc(prob_para,'para'):.3f}", file=sys.stderr)

    assign = load_paraphrase_assignment()
    uw = pd.read_csv(os.path.join(REPO_ROOT, "data", "unified", "unified_wide.csv"))
    print(f"unified_wide rows={len(uw)}", file=sys.stderr)

    sps = build_style_prob_self(uw, prob_orig, prob_para, assign)
    # merge style_prob_self back onto the scored rows
    merged = uw.merge(sps[["judge", "author", "prompt_id", "condition",
                            "style_prob_self", "style_argmax_self", "text_kind"]],
                      on=["judge", "author", "prompt_id", "condition"], how="left")
    derived_dir = os.path.join(REPO_ROOT, "data", "derived")
    os.makedirs(derived_dir, exist_ok=True)
    sps.to_csv(os.path.join(derived_dir, "style_prob_self.csv"), index=False)
    print(f"Wrote {len(sps)} style_prob_self rows", file=sys.stderr)

    # restrict to rows where we have style_prob_self (drops C4)
    df = merged.dropna(subset=["style_prob_self"]).copy()
    df["author_is_self"] = df["author_is_self"].astype(int)
    df["predicted_self"] = df["predicted_self"].astype(int)

    results_rows = []
    hr_rows = []

    def run_for(label, sub):
        for cond in ["c1", "c2", "c3"]:
            d = sub[sub["condition"] == cond].reset_index(drop=True)
            if len(d) < 30:
                continue
            # single-mediator: style_prob_self
            point = fit_mediation_continuous(d, "author_is_self", "style_prob_self")
            cis = cluster_bootstrap(d, lambda dd: fit_mediation_continuous(dd, "author_is_self", "style_prob_self"), B=args.boot)
            row = {"subset": label, "condition": cond, "N": len(d), **point,
                   **{k + "_ci": cis[k] for k in point}}
            results_rows.append(row)
            # two-mediator horse-race
            point2 = fit_two_mediator(d, "author_is_self", "predicted_self", "style_prob_self")
            cis2 = cluster_bootstrap(d, lambda dd: fit_two_mediator(dd, "author_is_self", "predicted_self", "style_prob_self"), B=args.boot)
            hr_rows.append({"subset": label, "condition": cond, "N": len(d), **point2,
                            **{k + "_ci": cis2[k] for k in point2}})

    # pooled
    run_for("pooled", df)
    # per-judge
    for j in AUTHORS:
        run_for(f"judge={j}", df[df["judge"] == j])

    rdf = pd.DataFrame(results_rows)
    hdf = pd.DataFrame(hr_rows)

    out_csv_a = os.path.join(REPO_ROOT, "results", "style_as_mediator.csv")
    out_csv_b = os.path.join(REPO_ROOT, "results", "style_as_mediator_horserace.csv")

    def explode_ci(df_):
        df2 = df_.copy()
        for col in [c for c in df2.columns if c.endswith("_ci")]:
            df2[col + "_lo"] = df2[col].apply(lambda x: x[0])
            df2[col + "_hi"] = df2[col].apply(lambda x: x[1])
            df2 = df2.drop(columns=[col])
        return df2

    explode_ci(rdf).to_csv(out_csv_a, index=False)
    explode_ci(hdf).to_csv(out_csv_b, index=False)

    # Report
    lines = []
    lines.append("# Style-as-mediator analysis\n")
    lines.append("Continuous mediator `style_prob_self` = stylometric LR probability that the response text would be classified as authored by the judge (LOO multinomial LR, 11 features, separate models for originals and paraphrases).\n")
    lines.append(f"- LOO accuracy: originals = {acc(prob_orig,'orig'):.3f}; paraphrases = {acc(prob_para,'para'):.3f}\n")
    lines.append(f"- 2000-iter cluster bootstrap on prompt_id, seed 20260512. B={args.boot}.\n")
    lines.append("\n## A. Mediation through style_prob_self alone\n")
    lines.append("| Subset | Cond | N | c (total) | c' (direct) | a | b | indirect a·b |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in results_rows:
        lines.append(f"| {r['subset']} | {r['condition']} | {r['N']} | {fmt(r['c'])} {fmt_ci(r['c_ci'])} | "
                     f"{fmt(r['c_prime'])} {fmt_ci(r['c_prime_ci'])} | {fmt(r['a'])} {fmt_ci(r['a_ci'])} | "
                     f"{fmt(r['b'])} {fmt_ci(r['b_ci'])} | **{fmt(r['indirect'])}** {fmt_ci(r['indirect_ci'])} |")
    lines.append("\n## B. Two-mediator horse-race (predicted_self + style_prob_self)\n")
    lines.append("| Subset | Cond | N | c | c' | a1·b1 (pred) | a2·b2 (style) | b1 | b2 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in hr_rows:
        lines.append(f"| {r['subset']} | {r['condition']} | {r['N']} | {fmt(r['c'])} | "
                     f"{fmt(r['c_prime'])} {fmt_ci(r['c_prime_ci'])} | "
                     f"**{fmt(r['indirect1'])}** {fmt_ci(r['indirect1_ci'])} | "
                     f"**{fmt(r['indirect2'])}** {fmt_ci(r['indirect2_ci'])} | "
                     f"{fmt(r['b1'])} {fmt_ci(r['b1_ci'])} | {fmt(r['b2'])} {fmt_ci(r['b2_ci'])} |")

    lines.append("\n## C. Interpretation\n")
    lines.append("- In single-mediator form, `style_prob_self` carries an indirect effect if (a) the response text is more 'judge-like' when the author IS the judge, and (b) responses with higher style-similarity to the judge get higher scores. Both `a` and `b` can be inspected per-condition.\n")
    lines.append("- In the horse-race, if the indirect via `predicted_self` shrinks to ~0 and the indirect via `style_prob_self` is significant, the **recognition mediator was essentially a style-detection proxy**. If both remain significant, perceived authorship adds incremental score variance beyond style features.\n")
    lines.append("- C2 uses paraphrased text; therefore `style_prob_self` for C2 reflects whether stylistic fingerprints survive paraphrase.\n")
    lines.append("\n## Caveats\n")
    lines.append("- LR uses only 11 hand-crafted features. Higher-capacity stylometric models may detect more.\n")
    lines.append("- Style probability is not a manipulated treatment; the same causal caveats from PR #54 apply.\n")
    lines.append("- LOO is at the prompt level, so the LR is leak-protected across prompts but not across authors.\n")

    out_md = os.path.join(REPO_ROOT, args.report)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_csv_a}, {out_csv_b}, {out_md}", file=sys.stderr)


if __name__ == "__main__":
    main()
