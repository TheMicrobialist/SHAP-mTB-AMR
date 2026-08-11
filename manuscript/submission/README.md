# Submission planning

Gaps and per-venue prep: `readiness-checklist.md`.

## Verdict

This is a **resource and interpretability contribution**, not a methods or
state-of-the-art paper: off-the-shelf models, performance below TB-Profiler,
GenTB and DeepAMR, and a dataset derived from public ENA/SRA runs.

Dataset and health-ML tracks are the right home.

## Deadlines

Days from 2026-08-05.

| Venue | Deadline | Days | Verdict |
|---|---|---:|---|
| **[ML4H 2026: Findings](https://ml4h.ahli.cc/submit/call-for-papers/)** | 2026-09-10 | 36 | **Submit**: solicits datasets/resources, no novelty bar, 4pp, non-archival |
| [ML4H 2026: Proceedings](https://ml4h.ahli.cc/submit/call-for-papers/) | 2026-09-10 | 36 | Optional: 8pp archival; auto-falls back to Findings if rejected, so near-free |
| [ICLR 2027](https://iclr.cc/Conferences/2027/CallForPapers) | 2026-09-25 (abs 09-18) | 51 | Skip: no new method, results below existing tools |
| [ICML 2027](https://icml.cc/Conferences/FutureMeetings) | *no CFP published* | n/a | Skip: same bar as ICLR |
| [CHIL 2027](https://chil.ahli.cc/submit/call-for-papers/) | ~Feb 2027 *(est.)* | ~180 | Consider: health-focused, archival, if gaps partly closed |
| [KDD 2027](https://kdd.org/) | ~Feb 2027 *(est.)* | ~190 | Skip: rewards scale/deployment impact |
| **[NeurIPS 2027: Evaluations & Datasets](https://neurips.cc/)** | ~May 2027 *(est.)* | ~270 | **Target**: built for dataset/benchmark work; main-track review stringency |
| [ISMB/ECCB 2027](https://www.iscb.org/ismbeccb2027/home) | TBA | n/a | Watch: natural domain fit, Copenhagen |
| [AAAI 2027](https://aaai.org/conference/aaai/aaai-27/) | 2026-07-28 | **closed** | Missed: deadline passed; conference Feb 16–23, 2027, Montréal |

[NeurIPS 2026 E&D](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
closed 2026-05-06; the track was
[renamed](https://blog.neurips.cc/2026/03/23/introducing-the-evaluations-datasets-track-at-neurips-2026/)
from "Datasets & Benchmarks" this year, and the 2027 CFP is not out yet.
ICML 2027 dates are likewise unpublished. Treat any circulating date as rumour.

## Plan

1. **By 2026-09-10**: condense to 4 pages for ML4H Findings. Lead with the
   resource and interpretability layer; benchmark tables to the appendix. No
   new experiments needed. Fill the author placeholders first.
2. **Sept 2026 → May 2027**: work `readiness-checklist.md` in order. Lineage-aware
   validation matters most: it decides whether the cross-drug result is
   biological or confounded, and that is the paper's only novelty claim.
3. **~May 2027**: submit the strengthened paper to NeurIPS Evaluations & Datasets.

ML4H Findings is non-archival, so step 1 does not foreclose step 3.

## Why NeurIPS E&D is the top-tier fit

The track explicitly welcomes domain-specific datasets and benchmarks, and
requires submissions to state "what claims it supports, under what assumptions,
and what limitations apply", the register the Discussion is already written in.
It reviews to main-conference stringency, hence the nine-month runway.

## Journal alternative

If the goal is an archival, citable publication rather than an ML-venue
credential, journals beat every conference here on expected value: they judge
a resource on whether it is correct, documented and useful:
[*Bioinformatics*](https://academic.oup.com/bioinformatics) (Application Note,
~2pp, dashboard front and centre),
[*Microbial Genomics*](https://www.microbiologyresearch.org/content/journal/mgen),
[*BMC Bioinformatics*](https://bmcbioinformatics.biomedcentral.com/),
[*Scientific Data*](https://www.nature.com/sdata/).
