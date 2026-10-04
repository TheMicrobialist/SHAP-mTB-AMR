# Submission planning

Gaps and per-venue prep: `readiness-checklist.md`. Collaboration decisions and
their dates: `decisions.md`.

Replanned 2026-09-26 after the ML4H 2026 window closed unused. The previous plan
led with ML4H Findings; that option no longer exists and the replacement is
different in kind, not just in date. See **What changed** below.

## Verdict

This is a **resource and interpretability contribution**, not a methods or
state-of-the-art paper: off-the-shelf models, performance below TB-Profiler,
GenTB and DeepAMR, and a dataset derived from public ENA/SRA runs.

Dataset and health-ML tracks are the right home. That verdict has not changed.
What changed is that a competing resource now occupies the same niche, so
establishing a citable date matters more than it did in August.

## What changed since 2026-08-05

1. **ML4H 2026 closed unused.** Paper deadline was 2026-09-10 and the demo
   deadline 2026-09-14; both passed with no submission. Verified 2026-09-26 on
   the CFP: no extension, no late-breaking track. The conference itself runs
   2026-12-06/07 in Sydney, so there is nothing left to enter.
2. **Nothing moved on the manuscript since 2026-08-11.** `main` last advanced
   2026-08-05. PR #15 has been open and unmerged since 2026-08-11.
3. **BIG-TB is still unaddressed.** `../reading/06-on-device-llm-decision.md`
   concluded on 2026-08-05 with "read it now, before any further work on the
   manuscript" and flagged that it independently reports our central finding at
   17,000 genomes against our 9,798. Seven weeks later it has not been read or
   cited. This is now the highest-priority scientific item, ahead of lineage
   validation, because it determines what the paper can still claim.

## The structural problem with the old plan

The old plan had one near-term entry point and one nine-month target, with
nothing in between. Missing the near-term entry point left an eight-month gap
in which the paper accrues no date, no citation and no external feedback, while
BIG-TB continues to define the niche. The fix is not to find another conference
deadline. It is to stop making the paper's existence contingent on one.

**Post a preprint.** It has no deadline, establishes priority, is citable
immediately, and is compatible with every venue below, including double-blind
ones if posted before anonymised submission. The manuscript is already written,
already has verified references, and already builds to PDF. The only blockers
are the author placeholders, which take minutes.

## Deadlines

Days from 2026-09-26. Verified this date unless marked *(est.)*.

| Venue | Deadline | Days | Verdict |
|---|---|---:|---|
| **[bioRxiv](https://www.biorxiv.org/)** | rolling | — | **Do first**: no deadline, establishes priority against BIG-TB, citable, forecloses nothing |
| **[*Bioinformatics*](https://academic.oup.com/bioinformatics) (Application Note)** | rolling | — | **Primary target**: ~2pp, dashboard and pipeline front and centre, judged on usefulness not novelty |
| [*Microbial Genomics*](https://www.microbiologyresearch.org/content/journal/mgen) | rolling | — | Strong alternative: domain fit, resource-friendly |
| [*Scientific Data*](https://www.nature.com/sdata/) | rolling | — | Alternative: pure dataset descriptor, needs the Croissant/DOI work anyway |
| [ML4H 2026](https://ml4h.ahli.cc/submit/call-for-papers/) | 2026-09-10 (demos 09-14) | **closed** | Missed: no extension, no late track; conference 2026-12-06/07 Sydney |
| [ICLR 2027](https://iclr.cc/Conferences/2027/CallForPapers) | 2026-09-25 | **closed** | Skip regardless: no new method, results below existing tools |
| [CHIL 2027](https://chil.ahli.cc/submit/call-for-papers/) | ~Feb 2027 *(est.)* | ~130 | Consider: health-focused, archival. CFP unpublished as of 2026-09-26; CHIL 2026 ran 06-28/30 in Seattle |
| **[NeurIPS 2027: Evaluations & Datasets](https://neurips.cc/)** | ~May 2027 *(est.)* | ~250 | Stretch target: only if gaps 1–4 close. CFP unpublished |
| [ISMB/ECCB 2027](https://www.iscb.org/ismbeccb2027/home) | TBA | n/a | Watch: natural domain fit. Note Testagrose et al. 2025 published TB+LLM here |
| [KDD 2027](https://kdd.org/) | ~Feb 2027 *(est.)* | ~130 | Skip: rewards scale/deployment impact |

Treat every *(est.)* date as rumour until the official CFP is published.

## Plan

Ordered so that each step is useful even if the next one never happens.

1. **This week.** Fill the author placeholders (`main.tex:30-31`), confirm
   authorship order with the co-author, rebuild `main.pdf`, **post to bioRxiv**.
   No new experiments. This converts an unpublished draft into a citable
   artifact and stops the clock running against us.
2. **Next.** Read BIG-TB and reposition: cite it, state the relationship
   honestly, make the distinct contribution explicit. Then evaluate FORUM-TB on
   the BIG-TB harness, both tasks. Per `../reading/06`, this converts gaps 2 and
   3 from "design an experiment" into "run someone else's code", and its
   attribution task is a ready-made faithfulness test for the SHAP layer.
3. **Then, cheaply.** Close gap 4 (statistical rigour: repeated splits or nested
   CV, confidence intervals, and either test the model ranking or drop the
   claim). The checklist already marks this as cheap and disproportionately
   valuable to reviewers.
4. **Then submit to a journal.** *Bioinformatics* Application Note with steps
   1–3 done is a realistic acceptance, and it is archival and citable, which is
   what a resource contribution actually needs.
5. **Optional, if the goal is an ML-venue credential.** Close gap 1
   (lineage-aware validation) and target CHIL 2027 or NeurIPS 2027 E&D. Gap 1
   decides whether the cross-drug result is biological or confounded, and
   BIG-TB's independent finding makes that question more pressing, not less.

A bioRxiv preprint does not foreclose any venue here, including double-blind
NeurIPS, provided the submitted version is anonymised.

## Why the journal route now leads

In August the reasoning was that journals win on expected value if the goal is
an archival, citable publication. Three things now push harder in that
direction:

- The ML-venue calendar has no entry point for seven months, and conference
  acceptance was never the binding constraint on this work's usefulness.
- BIG-TB occupies the benchmark niche with more genomes and a better-framed
  headline result. Competing for the same dataset-track slot is now a worse bet
  than publishing the pipeline, dashboard and interpretability layer as a
  documented resource.
- The remaining gaps that block NeurIPS (1–3) are experimental and expensive.
  The gaps that block a journal (author placeholders, gap 4) are cheap.

## Why NeurIPS E&D remains the stretch target

The track explicitly welcomes domain-specific datasets and benchmarks, and
requires submissions to state "what claims it supports, under what assumptions,
and what limitations apply", the register the Discussion is already written in.
It reviews to main-conference stringency, hence the long runway. Its hard
requirements (Croissant metadata with Responsible AI fields, permanent DOI,
full anonymisation) are listed in `readiness-checklist.md` and are mechanical;
do them early if this target is kept.
