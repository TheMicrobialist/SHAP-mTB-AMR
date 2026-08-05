#!/usr/bin/env python3
"""
shap_agent.py
=============
A tool-using agent that interprets FORUM-TB SHAP attributions.

Consumes the prediction JSON produced by `vcf_to_prediction.py` and turns the
raw attribution table into a written interpretation, looking up the supporting
evidence (amino-acid change, cohort prevalence, co-resistance context) rather
than recalling it.

Usage:
    # Full report on all four drugs
    python3 scripts/shap_agent.py \\
        --predictions results/predictions/ERR040120_predictions.json

    # A specific question
    python3 scripts/shap_agent.py \\
        --predictions results/predictions/ERR040120_predictions.json \\
        --question "Why is this isolate predicted pyrazinamide-resistant?"

    # Show which tools the agent called (verify claims against evidence)
    python3 scripts/shap_agent.py --predictions ... --trace

Requires ANTHROPIC_API_KEY, or an `ant auth login` profile, to run the agent.
The four tools below are plain functions over local data and need no
credentials — they can be imported and tested offline.
"""

import os
import sys
import json
import gzip
import argparse
import contextvars
from functools import lru_cache
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    # Single source of truth for the AMR gene coordinates.
    from vcf_to_prediction import AMR_GENES
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError(
        "Could not import AMR_GENES from vcf_to_prediction.py. That module "
        "requires numpy/pandas/joblib/shap — install the project dependencies "
        "(pip install -r dashboard/requirements.txt)."
    ) from exc

from shap_agent_prompts import SYSTEM_PROMPT, REPORT_REQUEST, QUESTION_REQUEST

REPO_ROOT = Path(__file__).resolve().parent.parent
GENOME_FASTA = REPO_ROOT / "reference" / "H37Rv.fasta"
ML_MATRIX = REPO_ROOT / "resistance_dataset" / "ml_matrix.csv.gz"
CROSS_DRUG_DIR = REPO_ROOT / "results"

DRUGS = ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]
MODEL = "claude-opus-5"

# Strand for each AMR gene on H37Rv (NC_000962.3). Validated at import time by
# _validate_reading_frames(): every gene must have a length divisible by 3, a
# terminal stop codon, and no internal stop on the strand recorded here.
GENE_STRAND = {
    "rpoB": "+", "katG": "-", "inhA": "+", "fabG1": "+", "embB": "+",
    "embA": "+", "embC": "+", "pncA": "-", "rpsA": "+",
}

# Independently established resistance mutations, used to verify that the
# codon arithmetic reproduces known biology before any residue is reported.
FRAME_ANCHORS = [
    (761155, "rpoB", 450, "S"),
    (2155168, "katG", 315, "S"),
    (4247429, "embB", 306, "M"),
]

NUC_DECODE = {0: "REF", 1: "A", 2: "T", 3: "C", 4: "G"}
COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}

_BASES = "TCAG"
_AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
CODON_TABLE = {
    b1 + b2 + b3: _AAS[i]
    for i, (b1, b2, b3) in enumerate(
        (x, y, z) for x in _BASES for y in _BASES for z in _BASES
    )
}

# Set per-call by interpret(); a ContextVar rather than a module global so
# concurrent Streamlit sessions don't clobber each other.
_ACTIVE = contextvars.ContextVar("active_predictions", default=None)


# ============================================================
# Data loading (cached)
# ============================================================

@lru_cache(maxsize=1)
def _genome() -> str:
    """Load the H37Rv reference sequence as one uppercase string."""
    if not GENOME_FASTA.exists():
        return ""
    parts = []
    with open(GENOME_FASTA) as fh:
        for line in fh:
            if not line.startswith(">"):
                parts.append(line.strip())
    return "".join(parts).upper()


@lru_cache(maxsize=1)
def _matrix() -> pd.DataFrame:
    """Load the ML feature matrix (9,798 isolates x 2,693 positions + labels)."""
    if not ML_MATRIX.exists():
        return pd.DataFrame()
    return pd.read_csv(ML_MATRIX)


def _reverse_complement(seq: str) -> str:
    return "".join(COMPLEMENT.get(b, "N") for b in reversed(seq))


def _gene_orf(gene: str) -> str:
    """Return the coding sequence for a gene, 5'->3' on its own strand."""
    start, end = AMR_GENES[gene]
    sub = _genome()[start - 1:end]
    return sub if GENE_STRAND[gene] == "+" else _reverse_complement(sub)


def _translate(codon: str) -> str:
    return CODON_TABLE.get(codon, "?")


@lru_cache(maxsize=1)
def _validate_reading_frames() -> bool:
    """
    Verify the strand/frame table before any residue is reported.

    Two independent checks:
      1. Every gene ORF is divisible by 3, ends in a stop codon, and has no
         internal stop -- this confirms strand and frame.
      2. The three FRAME_ANCHORS reproduce their known codon and residue.

    Returns False if either fails, in which case lookup_position degrades to
    reporting gene and coordinate only.
    """
    if not _genome():
        return False

    for gene in AMR_GENES:
        if gene not in GENE_STRAND:
            return False
        orf = _gene_orf(gene)
        if len(orf) == 0 or len(orf) % 3 != 0:
            return False
        protein = "".join(_translate(orf[i:i + 3]) for i in range(0, len(orf), 3))
        if not protein.endswith("*") or "*" in protein[:-1]:
            return False

    for pos, gene, exp_codon, exp_aa in FRAME_ANCHORS:
        codon_num, _ = _codon_index(pos, gene)
        if codon_num != exp_codon:
            return False
        orf = _gene_orf(gene)
        codon = orf[(codon_num - 1) * 3:(codon_num - 1) * 3 + 3]
        if _translate(codon) != exp_aa:
            return False

    return True


def _codon_index(pos: int, gene: str):
    """Return (1-based codon number, 0-based offset within the codon)."""
    start, end = AMR_GENES[gene]
    offset = (pos - start) if GENE_STRAND[gene] == "+" else (end - pos)
    return offset // 3 + 1, offset % 3


def _parse_position(position) -> int:
    """Accept 'pos_761155', '761155', or 761155."""
    return int(str(position).replace("pos_", "").strip())


def _gene_for(pos: int):
    for gene, (start, end) in AMR_GENES.items():
        if start <= pos <= end:
            return gene
    return None


# ============================================================
# Tools
# ============================================================

def lookup_position(position: str, observed_nucleotide: str = "") -> dict:
    """Identify the gene, codon, and amino-acid change at a genomic position.

    Args:
        position: Genomic coordinate, e.g. "pos_761155" or "761155".
        observed_nucleotide: Optional observed base (A/T/C/G) so the resulting
            amino-acid substitution can be resolved. Omit if unknown.
    """
    pos = _parse_position(position)
    gene = _gene_for(pos)
    if gene is None:
        return {"position": pos, "gene": None,
                "note": "Position is outside the nine AMR genes in the feature set."}

    start, end = AMR_GENES[gene]
    result = {
        "position": pos, "gene": gene, "strand": GENE_STRAND[gene],
        "gene_span": f"{start}-{end}",
    }

    if not _validate_reading_frames():
        result["residue"] = None
        result["note"] = (
            "Reading-frame validation failed, so no amino-acid call is made. "
            "Gene and coordinate are reliable; the residue is unresolved."
        )
        return result

    codon_num, offset = _codon_index(pos, gene)
    orf = _gene_orf(gene)
    ref_codon = orf[(codon_num - 1) * 3:(codon_num - 1) * 3 + 3]
    ref_aa = _translate(ref_codon)

    result.update({
        "codon_number": codon_num, "reference_codon": ref_codon,
        "reference_aa": ref_aa,
    })

    obs = str(observed_nucleotide or "").strip().upper()
    if obs in ("A", "T", "C", "G"):
        # The feature encodes the base on the forward strand; complement it
        # for a gene transcribed from the reverse strand.
        coding_base = obs if GENE_STRAND[gene] == "+" else COMPLEMENT[obs]
        alt_codon = ref_codon[:offset] + coding_base + ref_codon[offset + 1:]
        alt_aa = _translate(alt_codon)
        result.update({
            "observed_nucleotide": obs, "alternate_codon": alt_codon,
            "alternate_aa": alt_aa, "synonymous": alt_aa == ref_aa,
            "substitution": f"{gene} {ref_aa}{codon_num}{alt_aa}",
        })
    else:
        result["substitution"] = f"{gene} {ref_aa}{codon_num}?"
        result["note"] = ("No observed nucleotide supplied, so only the reference "
                          "residue is resolved.")
    return result


def cohort_frequency(position: str, drug: str) -> dict:
    """How often a position is mutated in resistant vs susceptible isolates.

    Computed over the 9,798-isolate training cohort. Use this to tell a common
    resistance driver from an isolate-specific variant.

    Args:
        position: Genomic coordinate, e.g. "pos_761155".
        drug: One of RIFAMPICIN, ISONIAZID, ETHAMBUTOL, PYRAZINAMIDE.
    """
    drug = drug.strip().upper()
    if drug not in DRUGS:
        return {"error": f"Unknown drug {drug!r}. Expected one of {DRUGS}."}

    df = _matrix()
    if df.empty:
        return {"error": "Feature matrix not available locally."}

    col = f"pos_{_parse_position(position)}"
    if col not in df.columns:
        return {"position": col, "drug": drug,
                "note": "Position is not one of the 2,693 features in the matrix."}

    sub = df[[col, drug]].dropna(subset=[drug])
    resistant = sub[sub[drug] == 1]
    susceptible = sub[sub[drug] == 0]
    if len(resistant) == 0 or len(susceptible) == 0:
        return {"error": f"No labelled isolates for {drug}."}

    r_mut = int((resistant[col] != 0).sum())
    s_mut = int((susceptible[col] != 0).sum())
    return {
        "position": col, "drug": drug,
        "resistant_isolates": len(resistant),
        "resistant_mutated": r_mut,
        "resistant_mutated_pct": round(100 * r_mut / len(resistant), 1),
        "susceptible_isolates": len(susceptible),
        "susceptible_mutated": s_mut,
        "susceptible_mutated_pct": round(100 * s_mut / len(susceptible), 1),
    }


def cross_drug_context(position: str) -> dict:
    """Whether a position's SHAP attribution shifts under co-resistance.

    Returns rows from the six pairwise drug analyses. A large shift means the
    model weighted this position differently in co-resistant isolates than in
    isolates resistant to one drug only.

    Args:
        position: Genomic coordinate, e.g. "pos_2155168".
    """
    col = f"pos_{_parse_position(position)}"
    rows = []
    for path in sorted(CROSS_DRUG_DIR.glob("shap_cross_drug_*.csv")):
        pair = path.stem.replace("shap_cross_drug_", "")
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        hit = df[df["position"] == col]
        if hit.empty:
            continue
        r = hit.iloc[0]
        a, b = pair.split("_")
        rows.append({
            "pair": f"{a} vs {b}", "gene": r.get("gene"),
            f"{a}_only": round(float(r[f"shap_{a}_only"]), 5),
            f"{b}_only": round(float(r[f"shap_{b}_only"]), 5),
            f"{a}_coresistant": round(float(r[f"shap_{a}_in_coresist"]), 5),
            f"{b}_coresistant": round(float(r[f"shap_{b}_in_coresist"]), 5),
            "max_abs_shift": round(float(r["max_abs_delta"]), 5),
        })

    if not rows:
        return {"position": col,
                "note": "Position does not appear in any cross-drug analysis."}
    return {"position": col, "pairs": rows,
            "reminder": ("A shift reflects how the model weighted this feature in "
                         "co-resistant isolates. Co-occurrence in MDR strains is the "
                         "usual explanation, not a shared mechanism.")}


def get_shap_detail(drug: str, top_n: int = 40) -> dict:
    """Full SHAP attribution table for one drug, beyond the top 20 in the summary.

    Args:
        drug: One of RIFAMPICIN, ISONIAZID, ETHAMBUTOL, PYRAZINAMIDE.
        top_n: How many features to return, ranked by absolute SHAP value.
    """
    drug = drug.strip().upper()
    active = _ACTIVE.get()
    if active is None:
        return {"error": "No prediction file is loaded."}
    if drug not in DRUGS:
        return {"error": f"Unknown drug {drug!r}. Expected one of {DRUGS}."}

    csv_path = active["dir"] / f"{active['sample_id']}_{drug}_shap_values.csv"
    if not csv_path.exists():
        entry = active["data"].get(drug, {})
        feats = entry.get("top_shap_features", [])[:top_n]
        return {"drug": drug, "source": "summary JSON (top 20 only)",
                "features": feats}

    df = pd.read_csv(csv_path)
    df = df.reindex(df["shap_value"].abs().sort_values(ascending=False).index)
    out = df.head(int(top_n)).to_dict(orient="records")
    for row in out:
        row["nucleotide"] = NUC_DECODE.get(int(row.get("encoded_value", 0)), "?")
        row["shap_value"] = round(float(row["shap_value"]), 6)
    return {"drug": drug, "source": str(csv_path.name),
            "total_features": len(df), "returned": len(out), "features": out}


TOOL_FUNCTIONS = [lookup_position, cohort_frequency, cross_drug_context, get_shap_detail]


# ============================================================
# Prediction file handling
# ============================================================

def load_predictions(path) -> dict:
    """Load a *_predictions.json produced by vcf_to_prediction.py."""
    path = Path(path)
    with open(path) as fh:
        data = json.load(fh)
    sample_id = next(
        (v.get("sample") for v in data.values() if isinstance(v, dict) and v.get("sample")),
        path.stem.replace("_predictions", ""),
    )
    return {"data": data, "sample_id": sample_id, "dir": path.parent, "path": path}


def format_profile(active: dict, drug: str = None) -> str:
    """Render the resistance profile and top attributions as prompt text."""
    lines = []
    drugs = [drug.upper()] if drug else [d for d in DRUGS if d in active["data"]]
    for d in drugs:
        entry = active["data"].get(d)
        if not entry:
            continue
        lines.append(
            f"\n{d}: {entry.get('prediction')} "
            f"(P(resistant) = {entry.get('probability_resistant')})"
        )
        for feat in entry.get("top_shap_features", [])[:8]:
            enc = feat.get("encoded_value", 0)
            lines.append(
                f"  {feat.get('position')}  {feat.get('gene')}  "
                f"base={NUC_DECODE.get(int(enc), '?')}  "
                f"SHAP={feat.get('shap_value'):+.5f}"
            )
    return "\n".join(lines) if lines else "(no drug entries found)"


# ============================================================
# Agent
# ============================================================

def interpret(predictions_path, **kwargs):
    """Run the interpretation agent over a prediction JSON file.

    Args:
        predictions_path: Path to a *_predictions.json file.
        drug: Restrict the profile to one drug. None covers all four.
        question: Free-text question. None produces a full report.
        trace: Print each tool call as it happens.
        model: Claude model id.
        effort: Reasoning effort (low | medium | high | xhigh | max).

    Returns:
        The agent's written interpretation as a string.
    """
    return _run_agent(load_predictions(predictions_path), **kwargs)


def interpret_results(results, sample_id, output_dir=None, **kwargs):
    """Run the agent over an in-memory results dict.

    Same shape as the prediction JSON — {DRUG: {prediction, probability_resistant,
    top_shap_features}}. Lets the dashboard call the agent without writing a
    temp file. Accepts the same keyword arguments as interpret().
    """
    active = {"data": results, "sample_id": sample_id,
              "dir": Path(output_dir) if output_dir else Path("."), "path": None}
    return _run_agent(active, **kwargs)


def _run_agent(active, drug=None, question=None, trace=False,
               model=MODEL, effort="high"):
    """Shared agent loop for interpret() and interpret_results()."""
    try:
        import anthropic
        from anthropic import beta_tool
    except ImportError as exc:
        raise ImportError(
            "The anthropic package is required to run the agent:\n"
            "    pip install anthropic"
        ) from exc

    token = _ACTIVE.set(active)
    try:
        tools = [beta_tool(fn) for fn in TOOL_FUNCTIONS]
        profile = format_profile(active, drug)
        prompt = (
            QUESTION_REQUEST.format(sample_id=active["sample_id"],
                                    profile=profile, question=question)
            if question else
            REPORT_REQUEST.format(sample_id=active["sample_id"], profile=profile)
        )

        client = anthropic.Anthropic()
        runner = client.beta.messages.tool_runner(
            model=model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=[{"role": "user", "content": prompt}],
        )

        final_text = []
        for message in runner:
            for block in message.content:
                if block.type == "tool_use" and trace:
                    print(f"  [tool] {block.name}({json.dumps(block.input)})",
                          file=sys.stderr)
                elif block.type == "text":
                    final_text = [block.text]
        return "\n".join(final_text).strip()
    finally:
        _ACTIVE.reset(token)


def credentials_available() -> bool:
    """True if the Anthropic SDK is installed and some credential is resolvable."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    cfg = Path(os.environ.get("ANTHROPIC_CONFIG_DIR",
                              Path.home() / ".config" / "anthropic"))
    return (cfg / "credentials").exists()


# ============================================================
# CLI
# ============================================================

def main():
    ap = argparse.ArgumentParser(
        description="Interpret FORUM-TB SHAP attributions with a tool-using agent.")
    ap.add_argument("--predictions", required=True,
                    help="Path to a *_predictions.json file.")
    ap.add_argument("--drug", choices=DRUGS, help="Restrict to one drug.")
    ap.add_argument("--question", help="Ask a specific question instead of a full report.")
    ap.add_argument("--trace", action="store_true", help="Print tool calls to stderr.")
    ap.add_argument("--effort", default="high",
                    choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--output", help="Write the report to a file as well as stdout.")
    args = ap.parse_args()

    if not credentials_available():
        sys.exit(
            "No Anthropic credentials found.\n"
            "  export ANTHROPIC_API_KEY=...   (or run: ant auth login)\n"
            "The tools in this module work offline; only the agent needs a key."
        )

    report = interpret(args.predictions, drug=args.drug, question=args.question,
                       trace=args.trace, effort=args.effort)
    print(report)
    if args.output:
        Path(args.output).write_text(report)
        print(f"\n[saved to {args.output}]", file=sys.stderr)


if __name__ == "__main__":
    main()
