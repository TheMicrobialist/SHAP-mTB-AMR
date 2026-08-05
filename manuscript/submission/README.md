# Submission planning

Assessed 2026-08-05. Estimated dates are marked; verify every date on the
official CFP before relying on it. Gaps and per-venue prep: `readiness-checklist.md`.

## Verdict

This is a **resource and interpretability contribution**, not a methods or
state-of-the-art paper: off-the-shelf models, performance below TB-Profiler,
GenTB and DeepAMR, and a dataset derived from public ENA/SRA runs — all of
which the Discussion states itself. Main ML tracks review on the novelty this
work deliberately does not claim, so ICLR / ICML / AAAI / NeurIPS-main are
near-certain rejects. Dataset and health-ML tracks are the right home, and the
candid Discussion is an asset there rather than a liability.

## Deadlines

Days from 2026-08-05.

| Venue | Deadline | Days | Verdict |
|---|---|---:|---|
| **ML4H 2026 — Findings** | 2026-09-10 | 36 | **Submit** — solicits datasets/resources, no novelty bar, 4pp, non-archival |
| ML4H 2026 — Proceedings | 2026-09-10 | 36 | Optional — 8pp archival; auto-falls back to Findings if rejected, so near-free |
| AAAI 2027 | 2026-09-16 | 42 | Skip — main track wants a technical contribution; no runway to build one |
| ICLR 2027 | 2026-09-25 | 51 | Skip — no new method, results below existing tools |
| ICML 2027 | 2027-01-22 (abs 01-16) | 170 | Skip — same bar as ICLR |
| CHIL 2027 | ~Feb 2027 *(est.)* | ~180 | Consider — health-focused, archival, if gaps partly closed |
| KDD 2027 | ~Feb 2027 *(est., unverified)* | ~190 | Skip — rewards scale/deployment impact |
| **NeurIPS 2027 — Evaluations & Datasets** | ~May 2027 *(est.)* | ~270 | **Target** — built for dataset/benchmark work; main-track review stringency |
| ISMB/ECCB 2027 | TBA | — | Watch — natural domain fit, Copenhagen |

NeurIPS 2026 Evaluations & Datasets closed 2026-05-06. The track was renamed
from "Datasets & Benchmarks" this year.

## Plan

1. **By 2026-09-10** — condense to 4 pages for ML4H Findings. Lead with the
   resource and interpretability layer; benchmark tables to the appendix. No
   new experiments needed. Fill the author placeholders first.
2. **Sept 2026 → May 2027** — work `readiness-checklist.md` in order. Lineage-aware
   validation matters most: it decides whether the cross-drug result is
   biological or confounded, and that is the paper's only novelty claim.
3. **~May 2027** — submit the strengthened paper to NeurIPS Evaluations & Datasets.

ML4H Findings is non-archival, so step 1 does not foreclose step 3.

## Why NeurIPS E&D is the top-tier fit

The track explicitly welcomes domain-specific datasets and benchmarks, and
requires submissions to state "what claims it supports, under what assumptions,
and what limitations apply" — the register the Discussion is already written in.
It reviews to main-conference stringency, hence the nine-month runway.

## Journal alternative

If the goal is an archival, citable publication rather than an ML-venue
credential, journals beat every conference here on expected value — they judge
a resource on whether it is correct, documented and useful:
*Bioinformatics* (Application Note, ~2pp, dashboard front and centre),
*Microbial Genomics*, *BMC Bioinformatics*, *Scientific Data*.

## Sources

[NeurIPS 2026 E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets) ·
[track rename](https://blog.neurips.cc/2026/03/23/introducing-the-evaluations-datasets-track-at-neurips-2026/) ·
[ICLR 2027](https://iclr.cc/Conferences/2027/CallForPapers) ·
[ML4H 2026](https://ml4h.ahli.cc/submit/call-for-papers/) ·
[CHIL](https://chil.ahli.cc/submit/call-for-papers/) ·
[AAAI 2027](https://aaai.org/conference/aaai/aaai-27/) ·
[ICML 2027](https://icml.cc/) ·
[ISMB/ECCB 2027](https://www.iscb.org/ismbeccb2027/home)
