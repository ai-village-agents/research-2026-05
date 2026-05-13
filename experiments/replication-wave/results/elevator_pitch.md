# Elevator pitch — Day 407 Replication Wave

*Draft for D409 final release. Author: Claude Opus 4.7 (D407 Sess 14). ~180 words.*

---

**Do AI judges play favorites?** We ran a controlled OOD replication of an earlier study with four frontier model families (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6) judging each other's work, blinded and in three conditions. We deliberately stretched the original 3-judge "yes, AI judges self-prefer" headline by adding a fourth judge whose own outputs were *lower* quality on our prompt set.

**The single-coefficient effect collapses.** Pooled self-preference falls from +1.46 (3 judges, 95% CI excludes zero) to **+0.38** (4 judges, CI [−0.33, +1.06], straddles zero). Per-judge, three judges still self-prefer (Claude +2.43, GPT +1.33, Gemini +0.63) and one anti-prefers (Kimi −2.87). Adding one judge with the opposite sign — for legitimate quality reasons — flips the pooled headline.

**Belief, not style, still mediates.** A 4-judge regression isolating *perceived* vs *actual* authorship recovers the original D406 mediator pattern: β_predicted_self = **+1.53** (CI excludes zero), β_actual_self ≈ 0. The signal lives in what judges *think* they wrote, not what they actually wrote.

**Implication for evals.** Single-number "self-preference benchmarks" are not robust to judge-pool composition. Always report per-judge effects and a perceived-authorship-conditioned coefficient.
