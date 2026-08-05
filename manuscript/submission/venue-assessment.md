# Venue assessment

Compiled 2026-08-05. Verify all dates on the official call for papers.

## What we are actually submitting

Stating this precisely matters, because it determines fit more than any other
factor. Per the manuscript's own Results and Discussion:

| Dimension | Reality |
|---|---|
| New algorithm | None. Random forest, LightGBM, XGBoost, linear SVM, regularized logistic regression, `shap.TreeExplainer` — all off-the-shelf. |
| Performance | Per-drug AUC-ROC 0.883–0.976; **below** TB-Profiler, GenTB and DeepAMR on comparable drugs, and covering 4 drugs rather than 13. |
| New data | Derived, not primary: 9,798 isolates re-processed from public ENA/SRA runs into a 9,798 × 2,693 feature matrix. |
| Genuinely new | (a) an openly released ML-ready feature matrix with a documented pipeline; (b) a per-isolate SHAP interpretability layer with a public dashboard; (c) a cross-drug attribution analysis — which the paper itself says is probably confounded by population structure. |
| Validation | Single train/test split, no confidence intervals, no external cohort, no lineage stratification. |

The paper is a **resource and reproducibility contribution with an
interpretability angle**. It is not a methods paper and not a
state-of-the-art claim.

---

## Tier 1 — Main ML tracks: not viable

### ICLR 2027 · deadline 2026-09-25 · Verdict: skip

ICLR reviews on novelty and significance of the learning contribution. This
paper offers no new representation, objective, architecture or theory, and its
empirical results are explicitly below existing tools. Reviewers would not need
to be hostile to reject it — the paper concedes the grounds itself. Submitting
costs ~7 weeks of preparation and returns near-certain rejection plus public
OpenReview reviews stating the work is not competitive, which is a real
reputational cost for a preprint that will be cited from the repository.

### ICML 2027 · deadline 2027-01-22 (abstract 01-16) · Verdict: skip

Same reasoning as ICLR. The five-month lead time is better spent on the
readiness gaps than on a submission that fails the novelty bar regardless of
polish.

### AAAI 2027 · deadline 2026-09-16 · Verdict: skip

AAAI is broader than ICLR/ICML and has an AI-for-social-impact angle that a TB
diagnostics paper could in principle target. But the core track still expects a
technical contribution, and the 42-day runway does not permit closing any
substantive gap. If an AAAI-family venue is wanted, its **Journal Track** or a
health-focused workshop is a better route than the main track.

### NeurIPS 2026 main / Evaluations & Datasets · CLOSED

Abstract 2026-05-04, paper 2026-05-06. Both passed.

---

## Tier 2 — The realistic targets

### ML4H 2026 Findings · deadline 2026-09-10 · Verdict: SUBMIT

The best near-term option, and the fit is explicit rather than inferred. The
Findings track solicits "new insights, valuable resources, or exciting
preliminary directions" and accepts non-traditional artifacts including novel
datasets, negative results and reproducibility studies. It does not require
methodological novelty.

- **Format:** 4 pages at submission, appendices permitted without penalty.
- **Archival:** No — made public on OpenReview on acceptance. This is an
  advantage: it does not consume the work's eligibility for a later archival
  venue.
- **Timeline:** submissions open 2026-08-10; decisions 2026-10-22;
  camera-ready 2026-11-07 (tentative); event 2026-12-06/07.
- **Work required:** condensation only. No new experiments.
- **Risk:** the 4-page limit forces hard choices. Recommended emphasis — the
  resource, the interpretability layer, and the honest performance context;
  relegate the full benchmark tables to the appendix.

### ML4H 2026 Proceedings · deadline 2026-09-10 · Verdict: optional

Archival, PMLR-published, 8 pages, and looking for "a high degree of technical
sophistication." That bar is above what this paper offers, but **rejected
Proceedings submissions transfer automatically to Findings consideration**, so
submitting to Proceedings is close to a free option on the higher tier. The
only cost is writing 8 pages instead of 4. Worth doing if time allows.

### NeurIPS 2027 Evaluations & Datasets · ~May 2027 (estimated) · Verdict: TARGET

The strongest genuinely top-tier fit. The track (renamed from "Datasets &
Benchmarks" in 2026) exists for dataset and benchmark contributions and
explicitly welcomes domain-specific work, including "benchmarks on new or
existing datasets" and "systematic analyses of systems on novel datasets."

Two features of the track suit this paper unusually well:

1. It requires submissions to "clearly articulate the evaluative role their
   contribution plays: what claims it supports, under what assumptions, and
   what limitations apply." The manuscript's critical Discussion — the
   SHAP-under-dependence problem, the pyrazinamide label noise, the lineage
   confounding — is written in precisely that register. What would sink the
   paper at ICLR is an asset here.
2. It reviews **to main-conference stringency**, so the gaps must be closed.
   Nine months is enough.

Hard requirements to note now: data and code must be hosted, accessible and
documented at submission; **Croissant metadata with Responsible AI fields is
required for datasets**; double-blind by default, which means the repository
and dashboard must be anonymised for review.

### CHIL 2027 · ~February 2027 (estimated) · Verdict: consider

Health-focused, receptive to applied clinical ML and datasets, and less
novelty-obsessed than the general ML venues. A reasonable intermediate archival
target if the readiness gaps are partly closed but a NeurIPS submission looks
premature. CHIL 2026 closed 2026-02-04; assume a comparable 2027 date and
confirm when the CFP appears.

### KDD 2027 · ~February 2027 (estimated, unverified) · Verdict: skip

The applied data science track can host domain applications, but KDD rewards
scale and deployment impact, and this work has neither yet. The deadline is
also unconfirmed — inferred from historical pattern (2025 and 2026 were both
around 10 February), not from a published 2027 CFP.

### ISMB/ECCB 2027, Copenhagen · deadline TBA · Verdict: watch

Domain-wise this is the natural home, and ISCB proceedings papers are indexed
in *Bioinformatics*. Deadlines for 2027 are not yet published; ISMB proceedings
deadlines typically fall in the preceding January. Worth monitoring, and a
stronger cultural fit than any general ML venue — a bioinformatics audience
will not penalise the absence of a new algorithm.

---

## Tier 3 — Journals, and why they may be the right answer

If the objective is an archival, citable publication rather than an ML-conference
credential, journals dominate on expected value. They review resources on
whether the resource is correct, documented and useful — the criteria this work
actually meets.

| Journal | Fit | Note |
|---|---|---|
| *Bioinformatics* (Application Note) | Very strong | Purpose-built for tools/resources; 2-page format; the dashboard and agent suit it. Would require trimming to a tool announcement. |
| *Microbial Genomics* | Strong | TB genomics readership; receptive to WGS resistance-prediction resources. |
| *BMC Bioinformatics* | Strong | Where the Ngo & Teo benchmarking paper we cite appeared; comfortable with pipeline/benchmark papers. |
| *PLOS Computational Biology* | Moderate | Higher bar; would need the external validation and lineage analysis first. |
| *Scientific Data* | Moderate–strong | Descriptor format built for exactly this kind of released dataset; no novelty requirement, but demands rigorous data documentation. |

The manuscript's current IEEEtran preprint format is closest to a conference
submission, but the content — full Methods, dataset tables, honest limitations —
converts to any of these with modest reformatting.

---

## Summary

| Path | Effort | Probability | Payoff |
|---|---|---|---|
| ML4H Findings, Sept 2026 | Low (condense) | Good | Visibility, feedback, non-archival |
| ML4H Proceedings, Sept 2026 | Low–moderate | Lower, with Findings fallback | Archival PMLR |
| NeurIPS E&D, May 2027 | High (close gaps) | Moderate if gaps closed | Top-tier archival |
| *Bioinformatics* / *Microbial Genomics* | Low–moderate | Good | Archival, indexed, domain-appropriate |
| ICLR / ICML / AAAI main | Moderate | Very low | — |
