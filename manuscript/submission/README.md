# Submission planning — FORUM-TB manuscript

Assessment compiled **2026-08-05**. Deadlines were taken from official calls for
papers where available; anything estimated is marked. **Re-check every date on
the official site before planning around it** — deadlines move and get extended.

Three documents:

| File | Purpose |
|---|---|
| `README.md` (this file) | Headline recommendation, deadline table, decision |
| `venue-assessment.md` | Per-venue fit analysis and why each verdict was reached |
| `readiness-checklist.md` | What the paper is missing, prioritised, mapped to venues |

---

## The headline

**This manuscript is not currently competitive at the main tracks of ICLR, ICML,
NeurIPS or AAAI, and submitting it there would very likely waste a review
cycle.** That is not a stylistic judgement — it follows from what the paper
itself says. The Discussion states plainly that we "do not claim competitive
accuracy," reports performance below TB-Profiler, GenTB and DeepAMR, and uses
entirely off-the-shelf methods (random forest, LightGBM, XGBoost, `TreeExplainer`).
Main-track ML review is organised around methodological or empirical novelty,
and this work is deliberately neither. Its honesty is a virtue for a resource
paper and a fatal weakness for a main-track ML submission.

The contribution is a **dataset, a reproducible pipeline, and an interpretability
layer**. Venues exist for exactly that, and two are worth pursuing:

**Near term — ML4H 2026 Findings track. Deadline 2026-09-10 (36 days).**
The Findings track explicitly solicits "valuable resources," "novel datasets,"
and "exciting preliminary directions," and accepts non-traditional artifacts
without requiring methodological novelty. Four pages, non-archival. The paper
is already written; this is a condensation exercise, not new science. Low cost,
plausible acceptance, and non-archival status leaves the work free for a fuller
venue later.

**Aspirational — NeurIPS 2027 Evaluations & Datasets track. Deadline ~May 2027
(estimated, ~9 months).** This is the strongest genuinely top-tier fit, because
the track was built for dataset and benchmark contributions and explicitly
welcomes domain-specific work. It also reviews to main-conference stringency,
so the gaps in `readiness-checklist.md` have to be closed first. Nine months is
enough time to close them. Note the track was renamed from "Datasets &
Benchmarks" for 2026.

Pursuing both is coherent: ML4H Findings is non-archival, so it does not burn
the NeurIPS option.

---

## Deadlines

Days counted from 2026-08-05.

| Venue | Deadline | Days | Fit | Verdict |
|---|---|---:|---|---|
| **ML4H 2026 — Findings** | 2026-09-10 | 36 | Strong | **Submit** |
| ML4H 2026 — Proceedings | 2026-09-10 | 36 | Moderate | Optional; auto-falls back to Findings if rejected |
| AAAI 2027 | 2026-09-16 | 42 | Weak | Skip |
| ICLR 2027 | 2026-09-25 | 51 | Weak | Skip |
| ICML 2027 | 2027-01-22 (abs 01-16) | 170 | Weak | Skip |
| CHIL 2027 | ~Feb 2027 *(est.)* | ~180 | Moderate | Consider if gaps closed |
| KDD 2027 | ~Feb 2027 *(est., unverified)* | ~190 | Weak–moderate | Skip |
| **NeurIPS 2027 — Evaluations & Datasets** | ~May 2027 *(est.)* | ~270 | **Strongest top-tier** | **Target** |
| ISMB/ECCB 2027 | TBA | — | Strong (domain) | Watch — Copenhagen |

NeurIPS 2026 Evaluations & Datasets closed 2026-05-06 and is no longer an option
this cycle.

---

## Recommended plan

1. **Now → 2026-09-10.** Condense to a 4-page ML4H Findings submission. Lead
   with the resource and the interpretability layer, not the accuracy numbers.
   Keep the critical Discussion — at a Findings track, candour about
   limitations reads as rigour rather than weakness.
2. **In parallel.** Fill the author affiliations and Noah's email, which are
   still `[INSERT ...]` placeholders in `main.tex`.
3. **Sept 2026 → May 2027.** Work `readiness-checklist.md` in priority order.
   The two that most change the paper's standing are lineage-aware validation
   and a head-to-head comparison against TB-Profiler/GenTB/DeepAMR on a shared
   test set.
4. **~May 2027.** Submit the strengthened paper to NeurIPS Evaluations &
   Datasets.

### The honest alternative

If the goal is a citable, archival publication rather than an ML-venue line on
a CV, a domain journal is a better expected-value bet than any conference here:
*Bioinformatics* (Application Note), *Microbial Genomics*, *BMC Bioinformatics*,
or *PLOS Computational Biology*. These reward exactly what this work is —
a documented, reproducible, openly released resource — and do not penalise the
absence of methodological novelty. See `venue-assessment.md` for detail.

---

## Sources

- NeurIPS 2026 Evaluations & Datasets CFP — https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets
- NeurIPS blog, track rename — https://blog.neurips.cc/2026/03/23/introducing-the-evaluations-datasets-track-at-neurips-2026/
- ICLR 2027 CFP — https://iclr.cc/Conferences/2027/CallForPapers
- ML4H 2026 CFP — https://ml4h.ahli.cc/submit/call-for-papers/
- CHIL CFP — https://chil.ahli.cc/submit/call-for-papers/
- AAAI 2027 — https://aaai.org/conference/aaai/aaai-27/
- ICML 2027 — https://icml.cc/
- ISMB/ECCB 2027 — https://www.iscb.org/ismbeccb2027/home
