# 06. On-device LLM benchmarking: decision

**Question.** Can the "Benchmarking and Adapting On-Device LLMs for Clinical
Decision Support" design (Munim et al., the Bo Wang reference preprint) be
applied to this project?

**Decision: no, not as a standalone paper.** Two independent reasons, either
sufficient on its own. A narrow variant survives and is described at the end.

Researched 2026-08-05. This file exists mainly because the search turned up
something more important than the question asked: see **BIG-TB** below.

---

## Reason 1: the framing is largely taken

### Testagrose et al. 2025: LLMs already applied to TB resistance
Bioinformatics 41(Suppl_1):i40-i48 (ISMB proceedings) ·
[doi:10.1093/bioinformatics/btaf232](https://doi.org/10.1093/bioinformatics/btaf232) · PMID 40662835

- **Did** LLMs to predict antibiotic resistance in *M. tuberculosis*, trained and evaluated on 12,185 CRyPTIC isolates
- **Leaves open** they treat genomic sequence as language, closer to DNABERT than to instruction-tuned chat models. General-purpose chat LLMs are not directly covered
- **But** "LLMs for TB resistance prediction" as a headline is no longer novel, and this is a peer-reviewed ISMB paper, not a preprint

---

## Reason 2: contamination is disqualifying, and unfixable here

The reference paper's methodology depends on a defence this project cannot
build.

- **Their design** all three benchmark datasets were curated from cases released **after the training cutoff** of every evaluated model, explicitly to prevent memorisation inflating scores
- **Our situation** *rpoB* S450L and *katG* S315T are decades old, in every textbook, and the WHO catalogue is public. They are certainly in every model's training data
- **Consequence** an LLM asked to predict resistance from a variant list is being tested on recall, not reasoning. There is no post-cutoff trick available, because the biology is not new
- **Not a detail** benchmark contamination inflates results through memorisation rather than genuine capability, and no existing mitigation is both effective and faithful to the original evaluation goal. A TB resistance benchmark cannot be made contamination-resistant

Two weaker problems compound it:

- **Privacy motivation is thin.** The reference paper's case is that patient data cannot leave the institution. Our data is public, de-identified ENA/SRA. The argument applies to a clinical deployment we do not have
- **No on-device advantage to demonstrate.** A random forest scores an isolate in milliseconds and TB-Profiler is a local binary. The pipeline is already private and already fast. An on-device LLM would be slower and less accurate than what it replaces

---

## The narrow variant that does survive

Benchmark on-device LLMs as an **interpretation layer**, not as a predictor.
This is what `scripts/shap_agent.py` already is.

- **Task** given the SHAP attributions and variant list, produce an explanation
- **Score** factual accuracy against the WHO catalogue (is the named mutation real, is the stated association correct?), plus expert rating of usefulness
- **Why it dodges reason 2** memorisation is not the failure mode being measured; the question is whether a small local model can produce a faithful, non-hallucinated readout of a classifier's output
- **Why the privacy case works** an interpretation layer runs at the point of care on patient-linked genomes, unlike the training pipeline
- **Genuinely unclaimed** neither Testagrose nor BIG-TB covers this
- **Needs** an expert-annotated evaluation set, which does not exist. This is the blocker
- **Effort** high. A separate project, not a revision of this manuscript

Verdict: viable but not cheap, and dependent on clinical collaboration for the
annotation. Worth considering only after the current paper's gaps are closed.

---

## The more important finding: BIG-TB

Searching for the above surfaced a benchmark that directly affects this project.

### Tasmin, Mohanty, Kulkarni, Farhat & Green 2026: BIG-TB
bioRxiv, posted 2026-02-02 ·
[doi:10.64898/2026.01.30.702134](https://doi.org/10.64898/2026.01.30.702134) ·
[code](https://github.com/SAGE-Lab-UMass/Big-TB-benchmark)

*Benchmarks for Interpretable prediction from Genomes of Tuberculosis.* Note
Farhat is the senior author of GenTB.

- **Gives** 17,000+ genomes with high-quality short reads and measured resistance phenotypes, ML-ready, plus an expert-curated list of canonical resistance-conferring variants
- **Two tasks** (1) resistance phenotype prediction; (2) **attribution of predictions to known resistance variants**
- **Effort to adopt** low. Public, ML-ready, code released

### Why this matters more than the LLM question

1. **It occupies this project's niche.** ML-ready TB dataset + benchmark +
   interpretability attribution, at 17,000 genomes against our 9,798. Any
   dataset-track submission must now position against it explicitly.
2. **It independently reports our central finding.** BIG-TB shows "the models
   with highest predictive performance do not necessarily perform the best at
   canonical resistance variant discovery, indicating that in many cases the
   improved performance may be due to non-causal associations between variants
   and phenotype." That is our cross-drug confounding observation, found
   independently, with a better benchmark, and framed as a headline result.
   Our novelty claim is weaker than it was a week ago.
3. **It answers gap 5 negatively.** DNA foundation models do **not** beat simple
   ML baselines: mean test AUC 0.888 for the best CNN against 0.846 for the best
   DNABERT variant. The transfer-learning direction in `05` has been tested and
   loses. Deprioritise it.
4. **It solves gaps 2 and 3.** This is the shared, external, ML-ready benchmark
   the readiness checklist says we lack, with an attribution task that matches
   what we already do.

### What to do

- **Read it now**, before any further work on the manuscript.
- **Evaluate FORUM-TB on BIG-TB.** Both tasks. This converts gaps 2 and 3 from
  "design an experiment" into "run someone else's harness", and BIG-TB's
  attribution task is a ready-made faithfulness test for the SHAP layer (see
  `04`).
- **Reposition the paper.** Cite BIG-TB, state the relationship honestly, and
  make the distinct contribution explicit. Candidates: the interpretability
  layer and dashboard, the cross-drug analysis, and the agent, none of which
  BIG-TB provides.
- **Drop or defer the foundation-model direction** in `05` unless the aim is
  specifically to improve on their DNABERT result.
