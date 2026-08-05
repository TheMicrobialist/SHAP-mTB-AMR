# Readiness checklist

What stands between the manuscript and each venue. Ordered by how much each
item changes the paper's standing, not by effort. Venue choice: `README.md`.

Most of these are the future-work items the Discussion already identifies — the
paper has argued why they matter, so closing them is finishing an existing
argument rather than opening a new one.

## Blocking for any submission

- [ ] Author affiliations — `main.tex:30-31`, both still `[INSERT AFFILIATION ...]`
- [ ] Corresponding author email — `main.tex:31`, `[INSERT EMAIL]` on N. LeGall
- [ ] Confirm authorship order and contributions with the co-author
- [ ] LightGBM page numbers — sources disagree (3146–3154 vs 3149–3157); resolve
      if the venue requires pages. Noted at the top of `references.bib`.

## Scientific gaps, in priority order

**1. Lineage-aware validation.** The cross-drug attribution result is the
paper's most interesting finding and is currently uninterpretable — with a
pooled design it is as consistent with population-structure confounding as with
biology, and the Discussion says so. Assign lineage from the existing VCFs,
re-run per-drug models with stratification or feature weighting (Billows et al.
2023, cited, evaluated this exact setting), and re-run the cross-drug SHAP
analysis within strata.
*Blocks NeurIPS E&D, CHIL, PLOS Comp Biol. Not needed for ML4H Findings.*

**2. Head-to-head on a shared test set.** The Discussion correctly argues
cross-study numbers are incomparable — which also means we have not shown where
this pipeline stands. Run TB-Profiler, GenTB and if feasible DeepAMR on the same
held-out isolates and report side by side, including where FORUM-TB loses. A
negative result is publishable at a resource venue.
*Blocks NeurIPS E&D, CHIL.*

**3. External validation.** Validate on isolates independent of the ENA/SRA
training set. The CRyPTIC compendium (cited) offers quantitative MICs and would
also separate the pyrazinamide label-noise question from the representation
question.
*Blocks NeurIPS E&D, PLOS Comp Biol.*

**4. Statistical rigour.** Random Forest "wins" on margins as small as 0.0015 CV
AUC-ROC from a single split with no confidence intervals. Add repeated splits or
nested CV, report CIs, and either test the ranking or drop the ranking claim.
*Blocks any archival venue. Cheap, and disproportionately improves reviewer confidence.*

**5. Representation.** Add indel and structural-variant features — expected to
help pyrazinamide most, per the *pncA* argument already in the Discussion.
Consider variant- or protein-level aggregation for rare loss-of-function events.

**6. SHAP under feature dependence.** The Discussion concedes the analysis
assumes independence this data violates. Re-derive with a dependence-aware
estimator (Aas et al. 2021, cited) and quantify the effect of the top-50
impurity pre-selection. Leaving a known hole in the headline contribution
invites the sharpest possible review.

**7. Agent tooling.** Run `scripts/shap_agent.py` end to end — it has never been
executed against the API. Then decide whether it belongs in the paper at all; it
is engineering, not science, and may be better left as a repository artifact.

## Venue-specific prep

**ML4H 2026 Findings** — condense to 4pp (appendices unlimited, unpenalised);
lead with the resource and interpretability layer, benchmark tables to appendix;
keep the critical Discussion; reformat from IEEEtran to the ML4H template;
portal opens 2026-08-10. Decide Findings (4pp, non-archival) vs Proceedings
(8pp, archival) — Proceedings auto-falls back, so it is close to a free option.

**NeurIPS 2027 E&D** — close gaps 1–4; add a **Croissant metadata file with
Responsible AI fields** (hard requirement, not currently present); host the
dataset with a permanent DOI (Zenodo — a GitHub path is not sufficient);
**anonymise for double-blind** (repo, Hugging Face dashboard, and the author
names in the dashboard landing text all identify the authors); frame around the
dataset's evaluative role; reformat to the NeurIPS template.

**Journal route** — reformat to target; close gap 4 at minimum; confirm the
data- and code-availability statements meet journal policy (the existing back
matter is close).

## Already covered

Common reviewer complaints that are already handled: all 24 references verified
against PubMed/Crossref/arXiv with PMIDs recorded; every table and in-text
number traceable via `manuscript/PROVENANCE.md`; code, dataset, models and
dashboard publicly released; limitations discussed specifically and with
citations; prior-work comparison present including where this work loses; no
repository paths left in the manuscript body.
