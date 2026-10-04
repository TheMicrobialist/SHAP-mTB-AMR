#!/usr/bin/env python3
"""
who_catalogue.py
================
Lookup of WHO mutation-catalogue grades for alleles in a VCF.

The workbook is the second-edition catalogue (WHO/UCN/TB/2023.7). Matching
follows the accompanying pipeline note:

1. Genomic_coordinates, first row as the header. A genomic allele is
   chromosome + position + reference nucleotide + alternate nucleotide.
   The chromosome is always NC_000962.3, so position, REF, and ALT are enough.
2. Catalogue_master_file, row 3 as the header. The coordinate row's
   ``variant`` value is matched to the ``variant`` column, and the row for
   the drug supplies FINAL CONFIDENCE GRADING.

One genomic allele can point at more than one graded variant (common for
indels). One graded variant can point at more than one genomic allele.
"""

from collections import defaultdict
from functools import lru_cache
import warnings

import pandas as pd

CHROMOSOME = "NC_000962.3"
SOURCE = (
    "WHO catalogue of mutations in Mycobacterium tuberculosis complex, "
    "second edition (WHO/UCN/TB/2023.7)"
)

# Model drug name -> catalogue "drug" column.
CATALOGUE_DRUG = {
    "RIFAMPICIN": "Rifampicin",
    "ISONIAZID": "Isoniazid",
    "ETHAMBUTOL": "Ethambutol",
    "PYRAZINAMIDE": "Pyrazinamide",
}
MODEL_CATALOGUE_DRUGS = set(CATALOGUE_DRUG.values())

NUC_DECODE = {0: "REF", 1: "A", 2: "T", 3: "C", 4: "G"}

_GRADE_PLAIN = (
    ("1)", "associated with resistance"),
    ("2)", "associated with resistance (interim)"),
    ("3)", "uncertain significance"),
    ("4)", "not associated with resistance (interim)"),
    ("5)", "not associated with resistance"),
)

_CATALOGUE_COLUMNS = [
    "drug",
    "gene",
    "mutation",
    "variant",
    "tier",
    "effect",
    "FINAL CONFIDENCE GRADING",
    "PPV",
    "PPV_SOLO",
    "Present_SOLO_R",
    "Present_SOLO_S",
    "Additional grading",
]


def grading_plain(grade):
    """Short phrase for a FINAL CONFIDENCE GRADING label."""
    if not isinstance(grade, str):
        return None
    text = grade.strip()
    for prefix, phrase in _GRADE_PLAIN:
        if text.startswith(prefix):
            return phrase
    return text


def associated_with_resistance(grade):
    """True for catalogue groups 1 and 2."""
    plain = grading_plain(grade) or ""
    return plain.startswith("associated with resistance")


def model_drug_name(drug):
    """Return the model's drug key (RIFAMPICIN, ...)."""
    key = str(drug).upper()
    if key in CATALOGUE_DRUG:
        return key
    for model, catalogue_name in CATALOGUE_DRUG.items():
        if catalogue_name.upper() == key:
            return model
    return key


def catalogue_drug_name(drug):
    """Return the drug label used in the workbook."""
    return CATALOGUE_DRUG.get(model_drug_name(drug), str(drug))


def _missing(value):
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _as_number(value, digits=None):
    if _missing(value):
        return None
    number = float(value)
    if digits is None and number.is_integer():
        return int(number)
    if digits is not None:
        return round(number, digits)
    return number


def _as_text(value):
    if _missing(value):
        return None
    text = str(value).strip()
    return text or None


def _dna(seq):
    return bool(seq) and all(base in "ACGT" for base in seq)


class WhoCatalogue:
    """Indexed Genomic_coordinates and Catalogue_master_file sheets."""

    def __init__(self, path, allele_to_variants, identity, records, sites, associations):
        self.path = str(path)
        self.allele_to_variants = allele_to_variants
        self.identity = identity
        self.records = records
        self.sites = sites
        self.associations = associations

    def match(self, pos, ref, alt, drug):
        """
        Exact (position, REF, ALT) match for one drug.

        ``entries`` are grading rows for that drug. ``coordinate_hits`` name
        the graded variant even when this drug has no row. ``other_drug_associations``
        lists group 1 and 2 grades of the same variant for other drugs.
        """
        pos = int(pos)
        ref = str(ref).upper()
        alt = str(alt).upper()
        variant_ids = self.allele_to_variants.get((pos, ref, alt), [])
        cat_drug = catalogue_drug_name(drug)
        entries = []
        others = []
        seen_others = set()
        for variant_id in variant_ids:
            record = self.records.get((cat_drug, variant_id))
            if record is not None:
                entries.append(record)
            for other in self._associations_for(variant_id):
                if other["drug"] == cat_drug:
                    continue
                key = (other["drug"], other["variant"])
                if key in seen_others:
                    continue
                seen_others.add(key)
                others.append(other)
        return {
            "matched": bool(variant_ids),
            "chromosome": CHROMOSOME,
            "position": pos,
            "reference_nucleotide": ref,
            "alternative_nucleotide": alt,
            "entries": entries,
            "coordinate_hits": [self.identity[v] for v in variant_ids if v in self.identity],
            "other_drug_associations": others,
        }

    def resistance_site_names(self, pos, drug):
        """Group 1/2 mutation names at this coordinate for the drug."""
        return list(self.sites.get((catalogue_drug_name(drug), int(pos)), []))

    def _associations_for(self, variant_id):
        return self.associations.get(variant_id, [])

    def known_resistance_variants(self, alleles, drug, shap_by_pos, encoded_by_pos):
        """
        Group 1 and 2 alleles for ``drug`` present in the sample.

        SNP alleles that the model encodes get that position's SHAP value.
        Indels and alleles outside the feature matrix are returned with
        ``in_model`` false.
        """
        cat_drug = catalogue_drug_name(drug)
        found = []
        seen = set()
        for pos, ref, alt in alleles:
            match = self.match(pos, ref, alt, drug)
            for entry in match["entries"]:
                if not entry["associated_with_resistance"]:
                    continue
                key = (entry["variant"], int(pos), ref, alt)
                if key in seen:
                    continue
                seen.add(key)
                shap_value = None
                in_model = False
                if len(ref) == 1 and len(alt) == 1 and int(pos) in encoded_by_pos:
                    encoded_alt = NUC_DECODE.get(encoded_by_pos[int(pos)])
                    if encoded_alt == alt:
                        in_model = True
                        if int(pos) in shap_by_pos:
                            shap_value = round(float(shap_by_pos[int(pos)]), 6)
                found.append({
                    "gene": entry["gene"],
                    "mutation": entry["mutation"],
                    "variant": entry["variant"],
                    "effect": entry["effect"],
                    "tier": entry["tier"],
                    "position": int(pos),
                    "reference_nucleotide": ref,
                    "alternative_nucleotide": alt,
                    "final_confidence_grading": entry["final_confidence_grading"],
                    "grading_plain": entry["grading_plain"],
                    "ppv": entry["ppv"],
                    "ppv_solo": entry["ppv_solo"],
                    "present_solo_r": entry["present_solo_r"],
                    "present_solo_s": entry["present_solo_s"],
                    "additional_grading": entry["additional_grading"],
                    "drug": cat_drug,
                    "in_model": in_model,
                    "shap_value": shap_value,
                    "other_drug_associations": [
                        {
                            "drug": other["drug"],
                            "gene": other["gene"],
                            "mutation": other["mutation"],
                            "variant": other["variant"],
                            "final_confidence_grading": other["final_confidence_grading"],
                            "grading_plain": other["grading_plain"],
                        }
                        for other in match["other_drug_associations"]
                    ],
                })

        def sort_key(row):
            grade_rank = 0 if str(row["final_confidence_grading"]).startswith("1)") else 1
            if row["shap_value"] is None:
                return (grade_rank, 1, 0)
            return (grade_rank, 0, -abs(row["shap_value"]))

        found.sort(key=sort_key)
        return found


def _record_from_row(row):
    grade = _as_text(row["FINAL CONFIDENCE GRADING"])
    return {
        "drug": _as_text(row["drug"]),
        "gene": _as_text(row["gene"]),
        "mutation": _as_text(row["mutation"]),
        "variant": _as_text(row["variant"]),
        "tier": _as_number(row["tier"]),
        "effect": _as_text(row["effect"]),
        "final_confidence_grading": grade,
        "grading_plain": grading_plain(grade),
        "associated_with_resistance": associated_with_resistance(grade),
        "ppv": _as_number(row["PPV"], 4),
        "ppv_solo": _as_number(row["PPV_SOLO"], 4),
        "present_solo_r": _as_number(row["Present_SOLO_R"]),
        "present_solo_s": _as_number(row["Present_SOLO_S"]),
        "additional_grading": _as_text(row["Additional grading"]),
    }


@lru_cache(maxsize=2)
def load_catalogue(path):
    """Load and index the WHO workbook. ``path`` is cached as a string."""
    print(f"  Loading WHO mutation catalogue: {path}")
    warnings.filterwarnings(
        "ignore",
        message="Conditional Formatting extension is not supported",
    )
    coordinates = pd.read_excel(path, sheet_name="Genomic_coordinates")
    master = pd.read_excel(
        path,
        sheet_name="Catalogue_master_file",
        header=2,
        usecols=_CATALOGUE_COLUMNS,
    )
    # usecols keeps workbook order, which is not the list order above.
    master = master.loc[:, _CATALOGUE_COLUMNS]

    allele_to_variants = {}
    for row in coordinates.itertuples(index=False):
        variant_id = _as_text(row.variant)
        if variant_id is None or _missing(row.position):
            continue
        ref = _as_text(row.reference_nucleotide)
        alt = _as_text(row.alternative_nucleotide)
        if ref is None or alt is None:
            continue
        ref = ref.upper()
        alt = alt.upper()
        if not _dna(ref) or not _dna(alt):
            continue
        key = (int(row.position), ref, alt)
        bucket = allele_to_variants.get(key)
        if bucket is None:
            allele_to_variants[key] = [variant_id]
        elif variant_id not in bucket:
            bucket.append(variant_id)

    identity = {}
    records = {}
    assoc_lists = defaultdict(list)
    sites = defaultdict(list)
    graded_rows = 0
    for row in master.itertuples(index=False):
        record = _record_from_series(row)
        if record["drug"] is None or record["variant"] is None:
            continue
        graded_rows += 1
        identity.setdefault(record["variant"], {
            "variant": record["variant"],
            "gene": record["gene"],
            "mutation": record["mutation"],
            "effect": record["effect"],
        })
        keep = (
            record["drug"] in MODEL_CATALOGUE_DRUGS
            or record["associated_with_resistance"]
        )
        if not keep:
            continue
        records.setdefault((record["drug"], record["variant"]), record)
        if record["associated_with_resistance"]:
            assoc_lists[record["variant"]].append(record)

    # Resistance-site names for the four model drugs, used when a SHAP
    # feature is the reference base at a coordinate that has graded alleles.
    site_seen = set()
    for (pos, ref, alt), variant_ids in allele_to_variants.items():
        if len(ref) != 1 or len(alt) != 1:
            continue
        for variant_id in variant_ids:
            for drug_name in MODEL_CATALOGUE_DRUGS:
                record = records.get((drug_name, variant_id))
                if record is None or not record["associated_with_resistance"]:
                    continue
                label = f"{record['gene']} {record['mutation']}"
                marker = (drug_name, pos, label)
                if marker in site_seen:
                    continue
                site_seen.add(marker)
                sites[(drug_name, pos)].append(label)

    catalogue = WhoCatalogue(
        path, allele_to_variants, identity, records, sites, assoc_lists
    )

    print(
        f"  Indexed {len(allele_to_variants)} genomic alleles and "
        f"{graded_rows} catalogue rows"
    )
    return catalogue


def _record_from_series(row):
    """Build a grading record from a Catalogue_master_file itertuple.

    Column order matches ``_CATALOGUE_COLUMNS``.
    """
    values = list(row)
    mapped = {name: values[i] for i, name in enumerate(_CATALOGUE_COLUMNS)}
    return _record_from_row(mapped)


def iter_alleles(variants):
    """Yield (pos, ref, alt) from parse_vcf output or a plain dict."""
    if variants is None:
        return []
    alleles = getattr(variants, "alleles", None)
    if alleles is not None:
        return list(alleles)
    found = []
    for pos, call in variants.items():
        if isinstance(call, dict) and call.get("ref") and call.get("alt"):
            found.append((int(pos), str(call["ref"]).upper(), str(call["alt"]).upper()))
    return found


def annotate_feature(feature_name, gene, encoded_value, shap_value, variants, catalogue, drug):
    """One SHAP feature, with a WHO match when the isolate carries an alt allele."""
    pos = int(str(feature_name).replace("pos_", ""))
    encoded_value = int(encoded_value)
    ref = None
    alt = None
    if encoded_value != 0 and variants is not None:
        call = variants.get(pos)
        if isinstance(call, dict):
            ref = call.get("ref")
            alt = call.get("alt")
        elif isinstance(call, str):
            alt = call
        if isinstance(ref, str):
            ref = ref.upper()
        if isinstance(alt, str):
            alt = alt.upper()

    feature = {
        "position": feature_name if str(feature_name).startswith("pos_") else f"pos_{pos}",
        "gene": gene,
        "encoded_value": encoded_value,
        "nucleotide": NUC_DECODE.get(encoded_value, str(encoded_value)),
        "reference_nucleotide": ref,
        "alternate_nucleotide": alt,
        "shap_value": round(float(shap_value), 6),
        "who_catalogue": None,
        "who_other_drug_associations": [],
        "catalogue_site_alleles": [],
    }
    if catalogue is None:
        return feature
    if encoded_value == 0:
        feature["catalogue_site_alleles"] = catalogue.resistance_site_names(pos, drug)
        return feature
    if ref and alt:
        match = catalogue.match(pos, ref, alt, drug)
        feature["who_catalogue"] = {
            "matched": match["matched"],
            "chromosome": CHROMOSOME,
            "position": pos,
            "reference_nucleotide": ref,
            "alternative_nucleotide": alt,
            "entries": match["entries"],
            "coordinate_hits": [] if match["entries"] else match["coordinate_hits"],
        }
        feature["who_other_drug_associations"] = match["other_drug_associations"]
    return feature


def who_table_fields(feature):
    """Flat WHO columns for the SHAP CSV."""
    catalogue = feature.get("who_catalogue") or {}
    entries = catalogue.get("entries") or []
    return {
        "who_variant": " | ".join(entry["variant"] for entry in entries if entry.get("variant")),
        "who_mutation": " | ".join(entry["mutation"] for entry in entries if entry.get("mutation")),
        "who_effect": " | ".join(entry["effect"] for entry in entries if entry.get("effect")),
        "who_grading": " | ".join(
            entry["final_confidence_grading"]
            for entry in entries
            if entry.get("final_confidence_grading")
        ),
    }


def _fmt_shap(value):
    number = float(value)
    if number > 0:
        return f"+{number:.4f}"
    return f"{number:.4f}"


def _direction(value):
    if value > 0:
        return "toward resistance"
    if value < 0:
        return "toward susceptibility"
    return "neither way"


def _push_clause(value):
    if value > 0:
        return "which pushes the prediction toward resistance"
    if value < 0:
        return "which pushes the prediction toward susceptibility"
    return "which does not move the prediction"


def _effect_phrase(effect):
    if not effect:
        return None
    return str(effect).replace("_", " ")


def _allele_phrase(feature):
    if feature.get("encoded_value") == 0 or feature.get("nucleotide") == "REF":
        return "reference allele"
    ref = feature.get("reference_nucleotide")
    alt = feature.get("alternate_nucleotide") or feature.get("nucleotide")
    if ref and alt:
        return f"{ref}>{alt}"
    if alt:
        return f"allele {alt}"
    return f"encoded value {feature.get('encoded_value')}"


def _evidence_clause(entry):
    bits = []
    if entry.get("ppv") is not None:
        bits.append(f"PPV {entry['ppv']:.3f}")
    elif entry.get("ppv_solo") is not None:
        bits.append(f"solo PPV {entry['ppv_solo']:.3f}")
    if entry.get("present_solo_r") is not None and entry.get("present_solo_s") is not None:
        bits.append(
            f"solo counts {entry['present_solo_r']} resistant and "
            f"{entry['present_solo_s']} susceptible"
        )
    if not bits:
        return ""
    return " Catalogue figures: " + ", ".join(bits) + "."


def _grading_sentence(entry, drug_name, with_evidence):
    effect = _effect_phrase(entry.get("effect"))
    sentence = (
        f"In the WHO mutation catalogue this allele is {entry['gene']} "
        f"{entry['mutation']} ({entry['variant']})"
    )
    if effect:
        sentence += f", a {effect}"
    grade = entry.get("final_confidence_grading")
    plain = entry.get("grading_plain")
    sentence += (
        f". The final confidence grading for {drug_name} is {grade} ({plain})."
    )
    if with_evidence:
        sentence += _evidence_clause(entry)
    if entry.get("additional_grading"):
        sentence += f" Additional grading note: {entry['additional_grading']}."
    return sentence


def _other_drug_sentence(associations, current_is_associated):
    if not associations:
        return ""
    shown = associations[:3]
    bits = [
        f"{item['drug']} ({item['gene']} {item['mutation']}, "
        f"{item['final_confidence_grading']})"
        for item in shown
    ]
    verb = "also grades" if current_is_associated else "grades"
    sentence = (
        f"The catalogue {verb} this allele as associated with resistance for "
        + "; ".join(bits)
    )
    extra = len(associations) - len(shown)
    if extra:
        sentence += f"; and {extra} more"
    return sentence + "."


def _feature_sentences(feature, drug_name, with_evidence):
    """Sentences describing one SHAP feature and any catalogue hit."""
    sentences = [
        (
            f"{feature['position']} in {feature['gene']} "
            f"({_allele_phrase(feature)}, SHAP {_fmt_shap(feature['shap_value'])}), "
            f"{_push_clause(feature['shap_value'])}."
        )
    ]
    catalogue = feature.get("who_catalogue") or {}
    entries = catalogue.get("entries") or []
    current_is_associated = any(entry.get("associated_with_resistance") for entry in entries)
    if entries:
        shown = entries[:4]
        for entry in shown:
            sentences.append(_grading_sentence(entry, drug_name, with_evidence))
        extra = len(entries) - len(shown)
        if extra:
            sentences.append(
                f"{extra} further graded variants at this allele are listed "
                "on the feature."
            )
    elif catalogue.get("matched"):
        hits = catalogue.get("coordinate_hits") or []
        names = ", ".join(hit["variant"] for hit in hits[:3] if hit.get("variant"))
        if names:
            sentences.append(
                f"The allele matches WHO catalogue variant {names}, which has "
                f"no grading row for {drug_name}."
            )
    elif feature.get("encoded_value") not in (0, None) and feature.get("reference_nucleotide"):
        sentences.append(
            "This alternate allele has no exact match in the catalogue "
            "Genomic_coordinates sheet."
        )
    elif feature.get("encoded_value") == 0 and feature.get("catalogue_site_alleles"):
        names = feature["catalogue_site_alleles"]
        shown = ", ".join(names[:4])
        extra = len(names) - min(len(names), 4)
        more = f" and {extra} more" if extra else ""
        sentences.append(
            f"This coordinate is the site of WHO alleles graded associated with "
            f"{drug_name} resistance ({shown}{more}). The isolate carries the "
            "reference base."
        )
    other = _other_drug_sentence(
        feature.get("who_other_drug_associations") or [],
        current_is_associated,
    )
    if other:
        sentences.append(other)
    return sentences


def _mentioned_keys(feature):
    """Group 1/2 variant keys already described for a feature."""
    keys = set()
    catalogue = feature.get("who_catalogue") or {}
    pos = None
    ref = feature.get("reference_nucleotide")
    alt = feature.get("alternate_nucleotide")
    if catalogue:
        pos = catalogue.get("position")
    for entry in catalogue.get("entries") or []:
        if entry.get("associated_with_resistance") and pos is not None and ref and alt:
            keys.add((entry["variant"], int(pos), ref, alt))
    return keys


def _known_sentence(item):
    change = f"{item['reference_nucleotide']}>{item['alternative_nucleotide']}"
    sentence = (
        f"{item['gene']} {item['mutation']} at position {item['position']} "
        f"({change}) is graded {item['final_confidence_grading']} "
        f"({item['grading_plain']}) for {item['drug']}."
    )
    if item.get("shap_value") is not None:
        sentence += (
            f" Its SHAP value is {_fmt_shap(item['shap_value'])}, which pushes "
            f"the prediction {_direction(item['shap_value'])}."
        )
    elif not item.get("in_model"):
        sentence += (
            " This allele is outside the model's single-nucleotide feature "
            "matrix, so it has no SHAP value."
        )
    other = _other_drug_sentence(item.get("other_drug_associations") or [], True)
    if other:
        sentence += " " + other
    return sentence


def build_explanation(sample_id, drug, label, probability, features, known_variants,
                      catalogue_loaded):
    """
    Prose explanation for one drug.

    Leads with the prediction and the largest SHAP contribution, then the
    WHO grade of that allele when the catalogue has one, then any other
    group 1 or 2 alleles in the isolate.
    """
    drug_name = catalogue_drug_name(drug)
    paragraphs = [
        (
            f"{sample_id} is predicted {label} to {drug} "
            f"(probability of resistance {float(probability):.4f})."
        )
    ]
    mentioned = set()
    if features:
        lead_sentences = _feature_sentences(features[0], drug_name, with_evidence=True)
        lead_sentences[0] = "The largest SHAP contribution is " + lead_sentences[0]
        paragraphs.append(" ".join(lead_sentences))
        mentioned |= _mentioned_keys(features[0])

        extras = []
        for feature in features[1:10]:
            catalogue = feature.get("who_catalogue") or {}
            has_grade = bool(catalogue.get("entries"))
            has_other = bool(feature.get("who_other_drug_associations"))
            has_site = bool(feature.get("catalogue_site_alleles")) and feature.get("encoded_value") == 0
            if has_grade or has_other or has_site:
                extras.append(" ".join(_feature_sentences(feature, drug_name, with_evidence=False)))
                mentioned |= _mentioned_keys(feature)
            if len(extras) == 3:
                break
        paragraphs.extend(extras)

    if catalogue_loaded:
        remaining = [
            item for item in known_variants
            if (item["variant"], item["position"], item["reference_nucleotide"],
                item["alternative_nucleotide"]) not in mentioned
        ]
        if not known_variants:
            paragraphs.append(
                f"No allele in this VCF is graded 1) Assoc w R or "
                f"2) Assoc w R - Interim for {drug_name}."
            )
        elif not remaining:
            if len(known_variants) == 1:
                paragraphs.append(
                    f"That is the only WHO group 1 or 2 {drug_name} allele in this isolate."
                )
            else:
                paragraphs.append(
                    f"The WHO group 1 and 2 {drug_name} alleles in this isolate "
                    "are the ones named above."
                )
        else:
            shown = remaining[:6]
            text = " ".join(_known_sentence(item) for item in shown)
            extra = len(remaining) - len(shown)
            if extra:
                text += (
                    f" {extra} further graded alleles are listed in "
                    "known_resistance_variants."
                )
            paragraphs.append(text)
        if any(not item.get("in_model") for item in known_variants):
            paragraphs.append(
                "The model scores single-nucleotide features only. Catalogue "
                "alleles that are indels, multi-nucleotide changes, or outside "
                "the nine-gene feature matrix are reported with their grade and "
                "without a SHAP value."
            )
        paragraphs.append(
            "SHAP values are the contributions of each feature to this model's "
            "resistant-class score for the isolate. WHO grades come from the "
            "second-edition mutation catalogue (WHO/UCN/TB/2023.7): an exact "
            "match on NC_000962.3 position, reference nucleotide, and alternate "
            "nucleotide, then the final confidence grading for the drug."
        )
    else:
        paragraphs.append(
            "The WHO mutation catalogue was not loaded, so this explanation "
            "uses SHAP values only."
        )
    return "\n\n".join(paragraphs)
