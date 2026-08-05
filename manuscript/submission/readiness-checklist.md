# Readiness checklist

What stands between the current manuscript and each target venue. Ordered by
how much each item changes the paper's standing, not by effort.

Most of these are not invented here — they are the future-work items the
manuscript's own Discussion already identifies. That is convenient: the paper
has already argued why they matter.

---

## Blocking for any submission

- [ ] **Author affiliations.** `main.tex:30-31` still reads
      `[INSERT AFFILIATION -- INSTITUTION, DEPARTMENT]` for both authors.
- [ ] **Corresponding author email.** `main.tex:31` still reads
      `[INSERT EMAIL]` on Noah LeGall's line.
- [ ] **Confirm authorship order and contributions** with the co-author before
      anything is submitted anywhere.
- [ ] **LightGBM page numbers.** Secondary sources disagree (3146–3154 vs
      3149–3157); NeurIPS proceedings are not Crossref-indexed. Resolve against
      the published volume if the venue requires page numbers. Flagged in a
      comment at the top of `references.bib`.

---

## Scientific gaps, in priority order

### 1. Lineage-aware validation — the one that matters most

The cross-drug attribution result is the paper's most interesting finding and
is currently uninterpretable: with a pooled, lineage-agnostic design it is as
consistent with population-structure confounding as with anything biological,
and the Discussion says so. Until this is resolved the paper's novel claim is
unusable.

- [ ] Assign lineage to isolates (e.g. barcode-based typing from the existing VCFs).
- [ ] Re-run per-drug models with lineage stratification or a feature-weighted
      scheme (Billows et al. 2023, already cited, evaluated this exact setting).
- [ ] Re-run the cross-drug SHAP analysis within lineage strata and report
      whether the attribution shifts survive.

**Blocks:** NeurIPS E&D, CHIL, PLOS Comp Biol. Not required for ML4H Findings.

### 2. Head-to-head comparison on a shared test set

The Discussion currently argues, correctly, that cross-study numbers are not
comparable — but that argument also means we have not demonstrated where this
pipeline stands. Running TB-Profiler, GenTB and (if feasible) DeepAMR on the
same held-out isolates would convert a hedge into a result, whichever way it
falls. A negative result here is publishable at a resource venue and would
strengthen the paper's credibility.

- [ ] Define a held-out evaluation set.
- [ ] Run the comparators on it.
- [ ] Report side-by-side, including where FORUM-TB loses.

**Blocks:** NeurIPS E&D, CHIL. Strongly desirable for journals.

### 3. External validation cohort

- [ ] Validate on isolates independent of the ENA/SRA training set — the
      CRyPTIC compendium (already cited) offers quantitative MICs and would
      also let the pyrazinamide label-noise question be separated from the
      representation question.

**Blocks:** NeurIPS E&D, PLOS Comp Biol.

### 4. Statistical rigour of the model comparison

The paper reports that Random Forest wins on all four drugs, on margins as
small as 0.0015 CV AUC-ROC from a single split, with no confidence intervals.
The Discussion already concedes the tree ensembles are indistinguishable.

- [ ] Repeated splits or nested CV.
- [ ] Confidence intervals on every reported metric.
- [ ] A significance test for the model ranking, or drop the ranking claim.

**Blocks:** any archival venue. Cheap to do and disproportionately improves
reviewer confidence.

### 5. Representation limits

- [ ] Add indel and structural-variant features — expected to benefit
      pyrazinamide most, per the *pncA* argument already made in the Discussion.
- [ ] Consider variant- or protein-level aggregation for rare loss-of-function
      events.

**Blocks:** nothing outright; strengthens everything.

### 6. Interpretability layer under feature dependence

The Discussion concedes the SHAP analysis assumes feature independence that
this data violates.

- [ ] Re-derive attributions with a dependence-aware estimator (Aas et al. 2021,
      already cited).
- [ ] Quantify the effect of the top-50 impurity pre-selection on the resulting
      attributions.

**Blocks:** nothing outright, but this is the paper's headline contribution —
leaving a known methodological hole in it invites the sharpest possible review.

### 7. Agent tooling

- [ ] Run `scripts/shap_agent.py` end to end and evaluate its output. It has
      never been executed against the API (no credentials on the build machine);
      this is recorded in the repository README to-do.
- [ ] Decide whether it belongs in the paper at all. It is engineering, not
      science, and may be better as a repository artifact than a manuscript claim.

---

## Venue-specific preparation

### ML4H 2026 Findings (deadline 2026-09-10)

- [ ] Condense to **4 pages**; appendices are unlimited and unpenalised.
- [ ] Lead with the resource and interpretability layer. Move the full
      benchmark tables (Tables 2–4) to the appendix.
- [ ] Keep the critical Discussion — at this track, candour reads as rigour.
- [ ] Reformat from IEEEtran to the ML4H template.
- [ ] Confirm the OpenReview submission portal opens 2026-08-10.
- [ ] Decide Proceedings (8pp, archival) vs Findings (4pp, non-archival).
      Proceedings auto-falls back to Findings, so it is close to a free option.

### NeurIPS 2027 Evaluations & Datasets (~May 2027, estimated)

- [ ] Close gaps 1–4 above.
- [ ] **Croissant metadata file with Responsible AI fields** — a hard track
      requirement for dataset submissions, and not currently present.
- [ ] Host the dataset somewhere citable and permanent (DOI via Zenodo or
      similar); a GitHub path is not sufficient.
- [ ] **Anonymise for double-blind review** — the repository, the Hugging Face
      dashboard, and the author names in the dashboard's landing text all
      currently identify the authors.
- [ ] Frame the paper around its *evaluative role*: what claims the dataset
      supports, under what assumptions, with what limitations. The track asks
      for this explicitly and the existing Discussion is most of the way there.
- [ ] Reformat to the NeurIPS template.

### Journal route (*Bioinformatics* Application Note, *Microbial Genomics*)

- [ ] Choose target and reformat; Application Note is ~2 pages and would need
      the paper cut to a tool announcement with the dashboard front and centre.
- [ ] Close gap 4 (statistical rigour) at minimum.
- [ ] Confirm data-availability and code-availability statements meet the
      journal's policy — the existing back matter is close.

---

## What is already done

Worth noting, since these are common reviewer complaints and they are covered:

- [x] All 24 references verified against PubMed, Crossref or arXiv, with PMIDs
      recorded per entry.
- [x] Every table and in-text number traceable to a source file
      (`manuscript/PROVENANCE.md`).
- [x] Code, dataset, trained models and dashboard publicly released.
- [x] Limitations discussed candidly and specifically, with citations.
- [x] Comparison to prior work present in the Discussion, including where this
      work loses.
- [x] No repository paths or internal notes left in the manuscript body.
