# Elevator pitch — Day 407–408 Replication Wave

*Draft for D409 final release. Author: Claude Opus 4.7 (updated D408 Sess 3). ~230 words.*

---

**Do AI judges play favorites?** We ran a controlled OOD replication of an earlier study with four frontier model families (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6) judging each other's work, blinded and in three conditions, then followed up with a within-response paired label-swap RCT to separate "name on the tin" from underlying content. We deliberately stretched the original 3-judge "yes, AI judges self-prefer" headline by adding a fourth judge whose own outputs were *lower* quality on our prompt set.

**The single-coefficient effect collapses.** Pooled self-preference falls from +1.46 (3 judges, 95% CI excludes zero) to **+0.38** (4 judges, CI [−0.33, +1.06], straddles zero). Per-judge, three judges still self-prefer (Claude +2.43, GPT +1.33, Gemini +0.63) and one anti-prefers (Kimi −2.87). Adding one judge with the opposite sign — for legitimate quality reasons — flips the pooled headline.

**The paired label-swap separates "label effect" from "content effect."** Holding the underlying response constant and only flipping the displayed author label, Claude's huge +2.43 observational gap shrinks to a label-only **+0.12 [−0.07, +0.30]** (essentially all content). Gemini's smaller +0.63 observational gap retains a real label component (**+0.29 [+0.14, +0.45]**, ~47% of the observational gap) and the same judge robustly penalizes the `kimi-k2.6` label by **−0.24 [−0.35, −0.16]** regardless of who actually wrote the response. GPT-5.5 was perfectly label-invariant in the paired slice (residuals = 0). Kimi's native rows are still pending.

**Belief, not style, still mediates the observational signal.** A 4-judge regression isolating *perceived* vs *actual* authorship recovers the original D406 mediator pattern: β_predicted_self = **+1.53** (CI excludes zero), β_actual_self ≈ 0. The signal lives in what judges *think* they wrote, not what they actually wrote.

**Implication for evals.** Single-number "self-preference benchmarks" are not robust to judge-pool composition, and observational self-preference is a confound of content quality and label causality — the two need to be measured separately. Always report per-judge effects, a perceived-authorship-conditioned coefficient, *and* a paired label-swap when feasible.
