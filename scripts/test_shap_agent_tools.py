#!/usr/bin/env python3
"""
test_shap_agent_tools.py
========================
Offline tests for the shap_agent evidence layer.

Runs with no API key and makes no network calls — the four tools are plain
functions over local data. Run before trusting anything the agent says:

    python3 scripts/test_shap_agent_tools.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import shap_agent as sa

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO = REPO_ROOT / "results" / "predictions" / "ERR040120_predictions.json"

PASS, FAIL = [], []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    print(f"  {'PASS' if condition else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


print("\n=== Reading-frame validation ===")
frames_ok = sa._validate_reading_frames()
check("all 9 gene ORFs valid and 3 anchors reproduce", frames_ok)

print("\n=== lookup_position: known resistance mutations ===")
# rpoB S450L — the dominant rifampicin determinant. Forward strand; the
# isolate carries T (encoded 2) at 761155.
r = sa.lookup_position("pos_761155", "T")
check("rpoB codon 450", r.get("codon_number") == 450, f"got {r.get('codon_number')}")
check("rpoB reference residue is S", r.get("reference_aa") == "S", f"got {r.get('reference_aa')}")
check("rpoB S450L resolved", r.get("substitution") == "rpoB S450L", f"got {r.get('substitution')}")
check("rpoB S450L is non-synonymous", r.get("synonymous") is False)

# katG S315T — the dominant isoniazid determinant. Reverse strand; the isolate
# carries G (encoded 4) on the forward strand, which is C on the coding strand.
r = sa.lookup_position("pos_2155168", "G")
check("katG codon 315", r.get("codon_number") == 315, f"got {r.get('codon_number')}")
check("katG reference residue is S", r.get("reference_aa") == "S", f"got {r.get('reference_aa')}")
check("katG S315T resolved (reverse strand)", r.get("substitution") == "katG S315T",
      f"got {r.get('substitution')}")

# embB M306 — common ethambutol determinant.
r = sa.lookup_position("pos_4247429")
check("embB codon 306", r.get("codon_number") == 306, f"got {r.get('codon_number')}")
check("embB reference residue is M", r.get("reference_aa") == "M", f"got {r.get('reference_aa')}")

print("\n=== lookup_position: edge cases ===")
r = sa.lookup_position("pos_1")
check("position outside AMR genes returns gene=None", r.get("gene") is None)
r = sa.lookup_position("761155")
check("bare coordinate accepted", r.get("gene") == "rpoB")
r = sa.lookup_position("pos_761155")
check("missing nucleotide leaves residue unresolved",
      r.get("substitution", "").endswith("?"), f"got {r.get('substitution')}")

print("\n=== cohort_frequency ===")
r = sa.cohort_frequency("pos_761155", "RIFAMPICIN")
check("RIF cohort sizes match the manuscript (7144 R / 2486 S)",
      r.get("resistant_isolates") == 7144 and r.get("susceptible_isolates") == 2486,
      f"got {r.get('resistant_isolates')}/{r.get('susceptible_isolates')}")
check("rpoB 761155 enriched in resistant isolates",
      r.get("resistant_mutated_pct", 0) > r.get("susceptible_mutated_pct", 100),
      f"R {r.get('resistant_mutated_pct')}% vs S {r.get('susceptible_mutated_pct')}%")

r = sa.cohort_frequency("pos_2155168", "ISONIAZID")
check("INH cohort sizes match the manuscript (8238 R / 1342 S)",
      r.get("resistant_isolates") == 8238 and r.get("susceptible_isolates") == 1342,
      f"got {r.get('resistant_isolates')}/{r.get('susceptible_isolates')}")
check("katG 2155168 enriched in resistant isolates",
      r.get("resistant_mutated_pct", 0) > r.get("susceptible_mutated_pct", 100),
      f"R {r.get('resistant_mutated_pct')}% vs S {r.get('susceptible_mutated_pct')}%")

check("unknown drug rejected", "error" in sa.cohort_frequency("pos_761155", "ASPIRIN"))
check("non-feature position reported, not crashed",
      "note" in sa.cohort_frequency("pos_1", "RIFAMPICIN"))

print("\n=== cross_drug_context ===")
r = sa.cross_drug_context("pos_2155168")
pairs = {p["pair"] for p in r.get("pairs", [])}
check("katG 2155168 appears in cross-drug analyses", len(pairs) > 0, f"{len(pairs)} pairs")
check("RIF vs INH pair present", "RIF vs INH" in pairs, f"got {sorted(pairs)}")
rif_inh = next((p for p in r.get("pairs", []) if p["pair"] == "RIF vs INH"), {})
# Values hand-checked against results/shap_cross_drug_RIF_INH.csv
check("INH-only attribution matches the CSV (0.23869)",
      abs(rif_inh.get("INH_only", 0) - 0.23869) < 1e-4, f"got {rif_inh.get('INH_only')}")
check("INH co-resistant attribution matches the CSV (0.12239)",
      abs(rif_inh.get("INH_coresistant", 0) - 0.12239) < 1e-4,
      f"got {rif_inh.get('INH_coresistant')}")
check("absent position handled", "note" in sa.cross_drug_context("pos_1"))

print("\n=== get_shap_detail ===")
if DEMO.exists():
    active = sa.load_predictions(DEMO)
    token = sa._ACTIVE.set(active)
    try:
        check("sample id parsed", active["sample_id"] == "ERR040120",
              f"got {active['sample_id']}")
        r = sa.get_shap_detail("RIFAMPICIN", top_n=5)
        feats = r.get("features", [])
        check("returns 5 features", len(feats) == 5, f"got {len(feats)}")
        check("top RIF feature is pos_761155",
              feats and feats[0]["position"] == "pos_761155",
              f"got {feats[0]['position'] if feats else None}")
        check("top RIF SHAP matches the JSON (+0.280542)",
              feats and abs(feats[0]["shap_value"] - 0.280542) < 1e-5,
              f"got {feats[0]['shap_value'] if feats else None}")
        check("ranked by absolute SHAP value",
              all(abs(feats[i]["shap_value"]) >= abs(feats[i + 1]["shap_value"])
                  for i in range(len(feats) - 1)))
        check("nucleotide decoded", feats and feats[0].get("nucleotide") == "T",
              f"got {feats[0].get('nucleotide') if feats else None}")
        check("unknown drug rejected", "error" in sa.get_shap_detail("ASPIRIN"))
    finally:
        sa._ACTIVE.reset(token)
else:
    check("demo prediction file present", False, f"missing {DEMO}")

print("\n=== profile rendering ===")
if DEMO.exists():
    active = sa.load_predictions(DEMO)
    profile = sa.format_profile(active)
    check("all four drugs in profile",
          all(d in profile for d in sa.DRUGS))
    check("profile carries SHAP values", "SHAP=" in profile)

print(f"\n{'=' * 52}\n{len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
