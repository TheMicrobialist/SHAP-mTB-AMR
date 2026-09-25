# Decision log

Joint decisions between the two authors: what was decided, when, and why.
Scientific gaps live in `readiness-checklist.md`; venue timing in `README.md`.
Engineering tasks live in GitHub issues. This file is only for questions that
needed both authors to agree, because those otherwise get settled twice or not
at all.

Each entry is **Open** or **Decided YYYY-MM-DD**. An open entry carries a
recommendation so the conversation starts from a position rather than a blank.

Opened 2026-09-26, ahead of the first sync since 2026-08-11.

---

## 1. Venue strategy after ML4H closed

**Status: Open.** Recommendation in `README.md`.

**Question.** The August plan's near-term target (ML4H 2026 Findings) closed
unused on 2026-09-10, and the next ML venue is ~May 2027. What replaces it?

**Recommendation.** Post to bioRxiv this week, then target *Bioinformatics* as
an Application Note, keeping NeurIPS 2027 E&D as a stretch goal. Reasoning in
`README.md` under "Why the journal route now leads". The short version: the
binding constraint is that BIG-TB is defining this niche while our paper has no
date on it, and a preprint fixes that in days rather than months.

**Needs from co-author.** Agreement on the journal-first framing, since it
trades ML-venue prestige for a near-certain archival record.

---

## 2. Dashboard: Streamlit or Electron

**Status: Open.** Raised by @noahaus on issue #8, 2026-09-20.

**Question.** Issue #11 ships a Streamlit dashboard, already deployed to
Hugging Face Spaces. Noah proposes an Electron desktop app in HTML/CSS/JS
instead, arguing Streamlit will not handle the data volume.

**What is known.** The Streamlit demo mode works and serves pre-computed results
for ERR040120. Live mode (user-uploaded VCF) crashes during SHAP computation,
which is an unfixed known bug, not a hypothetical. So the volume concern has
already shown up once in practice.

**Recommendation.** Diagnose the live-mode crash before choosing a framework.
If it is SHAP compute cost or memory, Electron does not fix it: the bottleneck
is the explainer, not the presentation layer, and rewriting the front end would
move the same problem to a new codebase. If it is a Streamlit
execution-model or timeout issue, Noah's argument holds.

Worth weighing against `readiness-checklist.md` item 7, which already asks
whether the agent tooling "belongs in the paper at all; it is engineering, not
science". The same question applies to a desktop rewrite: it is a substantial
build that adds nothing a reviewer scores.

**Needs from co-author.** Agreement on sequencing: diagnose first, then decide.

---

## 3. LLM provider configuration and API keys

**Status: Open.** Raised by @noahaus on issue #18, 2026-09-20.

**Question.** `scripts/shap_agent.py` supports Anthropic only. Noah proposes a
config file for OpenAI and Gemini, and offers to share an OpenAI key from his
existing credits.

**Recommendation.** Cheap to do and worth doing, but note that per
`readiness-checklist.md` item 7 the agent has never been run end to end against
any API. Running it once on the current provider is the prerequisite; adding
providers to an unexercised script multiplies untested paths.

On the key: do not commit a shared key or paste it into an issue. Use per-author
keys from environment variables, with the config file selecting provider only,
never carrying credentials.

**Needs from co-author.** Agreement to run the agent once before generalising
it, and to keep keys out of the repository.

---

## 4. AMR position validation

**Status: Open.** Raised by @noahaus on issue #17, 2026-09-19.

**Question.** Noah's reading of `vcf_to_prediction.py` is correct: a position
counts as an AMR site if and only if a `pos_<coordinate>` column exists in
`ml_matrix.csv.gz`. `AMR_GENES` is used only to label SHAP rows afterwards, not
to gate matching. He asks for a real cross-check against a TB AMR catalogue.

**Recommendation.** Two separable things, and they should not be conflated.
The current behaviour is *correct by construction*, because the nine-gene
restriction was applied when the matrix was built, so the column list is the
intended allowlist. That deserves documenting, not changing.

The genuinely useful addition is different: cross-reference matched positions
against the WHO mutation catalogue to report whether each is a *known*
resistance determinant. That is a reporting improvement, it strengthens the
biological-validation claim in the paper, and it does not alter any prediction.

**Needs from co-author.** Agreement on that split, so the code change is scoped
to reporting rather than to the feature pipeline.

---

## 5. Authorship order and contributions

**Status: Open.** Listed as blocking in `readiness-checklist.md`.

**Question.** Author order, contribution statement, and who is corresponding
author. `main.tex:30-31` currently lists N. Qiao then N. LeGall, with
`[INSERT AFFILIATION]` for both and `[INSERT EMAIL]` against N. LeGall as
corresponding.

**Recommendation.** Settle verbally and fill the placeholders in the same
session; it blocks every venue and is the cheapest blocking item on the list.

---

## Decided

Nothing yet. Entries move here with their date and the reasoning that settled
them, so that a question does not get reopened without new information.
