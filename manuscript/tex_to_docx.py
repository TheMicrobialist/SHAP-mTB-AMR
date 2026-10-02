#!/usr/bin/env python3
"""Convert manuscript/main.tex into an editable Word document."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "main.docx"

TABLE_ORDER = [
    "tab:dataset",
    "tab:perdrug",
    "tab:modelcomparison",
    "tab:crossdrug",
    "tab:multilabel",
    "tab:casestudy",
    "tab:tools",
]
FIGURE_ORDER = ["fig:pipeline", "fig:shap_summary", "fig:benchmark"]
TABLE_NUM = {k: i + 1 for i, k in enumerate(TABLE_ORDER)}
FIGURE_NUM = {k: i + 1 for i, k in enumerate(FIGURE_ORDER)}

ACCENTS = {
    "{\\'i}": "í",
    "{\\'e}": "é",
    "{\\'a}": "á",
    "{\\'o}": "ó",
    "{\\'u}": "ú",
    "{\\`a}": "à",
    "{\\'I}": "Í",
    '{\\"o}': "ö",
    '{\\"u}': "ü",
    "{\\o}": "ø",
    "{\\~n}": "ñ",
    "{\\~N}": "Ñ",
    "{\\'n}": "ń",
    "{\\c{c}}": "ç",
    "{\\c c}": "ç",
    "\\'i": "í",
    "\\'e": "é",
    "\\'a": "á",
    "\\'o": "ó",
    "\\'u": "ú",
    "\\`a": "à",
    '\\"o': "ö",
    '\\"u': "ü",
    "\\~n": "ñ",
}


def grab_braced(text: str, start: int) -> tuple[str, int]:
    """Return the {...} group starting at text[start] == '{' and the index after it."""
    assert text[start] == "{"
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    return text[start + 1 :], len(text)


def command_arg(text: str, cmd: str):
    m = re.search(rf"\\{cmd}\s*\{{", text)
    if not m:
        return None
    inner, _ = grab_braced(text, m.end() - 1)
    return inner


def decode_latex_chars(text: str) -> str:
    text = text.replace("{,}", ",")
    text = text.replace("``", "“").replace("''", "”")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\&", "&")
    text = text.replace(r"\#", "#")
    for src, dst in ACCENTS.items():
        text = text.replace(src, dst)

    text = re.sub(
        r"(Tables?)~?\\ref\{([a-zA-Z0-9:_-]+)\}--\\ref\{([a-zA-Z0-9:_-]+)\}",
        lambda m: f"{m.group(1)} {TABLE_NUM.get(m.group(2), '?')}–{TABLE_NUM.get(m.group(3), '?')}",
        text,
    )
    text = text.replace("---", "—").replace("--", "–")

    def ref_repl(m):
        kind, key = m.group(1), m.group(2)
        if kind.lower().startswith("fig"):
            return f"Figure {FIGURE_NUM.get(key, '?')}"
        if kind.lower().startswith("tables"):
            return f"Tables {TABLE_NUM.get(key, '?')}"
        return f"Table {TABLE_NUM.get(key, '?')}"

    text = re.sub(
        r"(Figures?|Figs?\.|Tables?|Tab\.)~?\\ref\{([a-zA-Z0-9:_-]+)\}",
        ref_repl,
        text,
    )
    text = re.sub(
        r"\\cite\{([a-zA-Z0-9_:,.-]+)\}",
        r"CITE{\1}",
        text,
    )

    math = {
        r"$|\mathrm{SHAP}|$": "|SHAP|",
        r"$\mathrm{SHAP}$": "SHAP",
        r"$\pm$": "±",
        r"\pm": "±",
        r"$\geq$": "≥",
        r"\geq": "≥",
        r"$\approx$": "≈",
        r"$\downarrow$": "↓",
        r"$\uparrow$": "↑",
        r"$\Delta$": "Δ",
        r"$P$": "P",
        r"$K$": "K",
    }
    for src, dst in math.items():
        text = text.replace(src, dst)
    text = re.sub(r"\$P=", "P=", text)
    text = re.sub(r"\$([^$]{1,40})\$", lambda m: _simplify_math(m.group(1)), text)
    text = re.sub(r"\\url\{([^}]+)\}", r"URL{\1}", text)
    text = text.replace("~", " ")
    return text


def _simplify_math(expr: str) -> str:
    expr = expr.replace(r"\mathrm{SHAP}", "SHAP")
    expr = expr.replace(r"\geq", "≥").replace(r"\pm", "±")
    expr = expr.replace(r"\approx", "≈").replace(r"\Delta", "Δ")
    expr = expr.replace(r"\downarrow", "↓").replace(r"\uparrow", "↑")
    return expr


def parse_bib(path: Path) -> dict[str, dict]:
    raw = path.read_text()
    entries: dict[str, dict] = {}
    for match in re.finditer(r"@(\w+)\s*\{", raw):
        kind = match.group(1)
        inner, end = grab_braced(raw, match.end() - 1)
        comma = inner.find(",")
        if comma < 0:
            continue
        key, body = inner[:comma].strip(), inner[comma + 1 :]
        fields: dict[str, str] = {"_type": kind.lower()}
        i = 0
        while i < len(body):
            fm = re.match(r"\s*(\w+)\s*=\s*", body[i:])
            if not fm:
                i += 1
                continue
            i += fm.end()
            name = fm.group(1).lower()
            if i < len(body) and body[i] == "{":
                val, nxt = grab_braced(body, i)
                i = nxt
            elif i < len(body) and body[i] == '"':
                nxt = body.find('"', i + 1)
                val = body[i + 1 : nxt]
                i = nxt + 1
            else:
                continue
            fields[name] = decode_latex_chars(val)
        entries[key] = fields
    return entries


def author_short(fields: dict) -> str:
    author = fields.get("author", "Unknown")
    author = author.replace(" and others", "")
    parts = [p.strip() for p in re.split(r"\s+and\s+", author) if p.strip()]
    if not parts:
        return "Unknown"
    first = parts[0]
    if first.startswith("{") and first.endswith("}"):
        name = first[1:-1]
        return name if len(parts) == 1 else f"{name} et al."
    last = first.split(",")[0].strip()
    return last if len(parts) == 1 else f"{last} et al."


def format_reference(fields: dict) -> str:
    author = decode_latex_chars(fields.get("author", "Unknown"))
    author = re.sub(r"\s+and\s+", ", ", author)
    author = author.replace("{", "").replace("}", "")
    title = fields.get("title", "").replace("{", "").replace("}", "")
    year = fields.get("year", "")
    venue = (
        fields.get("journal")
        or fields.get("booktitle")
        or fields.get("institution")
        or ""
    )
    extra = []
    if fields.get("volume"):
        extra.append(f"vol. {fields['volume']}")
    if fields.get("number"):
        extra.append(f"no. {fields['number']}")
    if fields.get("pages"):
        extra.append(f"pp. {fields['pages']}")
    bits = [author, f"“{title}”"]
    if venue:
        bits.append(venue)
    if extra:
        bits.append(", ".join(extra))
    if year:
        bits.append(f"({year})")
    if fields.get("doi"):
        bits.append(f"doi:{fields['doi']}")
    elif fields.get("url"):
        bits.append(fields["url"])
    return ". ".join(b for b in bits if b) + "."


def collect_cites(text: str, seen: list[str]) -> None:
    for keys in re.findall(r"CITE\{([a-zA-Z0-9_:,.-]+)\}", text):
        for key in [k.strip() for k in keys.split(",")]:
            if key and key not in seen:
                seen.append(key)


def replace_cites(text: str, cite_num: dict[str, int]) -> str:
    def repl(m):
        nums = []
        for key in [k.strip() for k in m.group(1).split(",")]:
            if key in cite_num:
                nums.append(str(cite_num[key]))
        return "[" + ",".join(nums) + "]" if nums else m.group(0)

    return re.sub(r"CITE\{([^}]+)\}", repl, text)


def add_runs(paragraph, text: str, italic=False, bold=False, size=11):
    """Add runs for a string that may contain \\emph, \\textit, \\textbf, \\texttt, URL{}."""
    token_re = re.compile(
        r"\\(emph|textit|textbf|texttt)\{([^{}]*)\}|URL\{([^}]*)\}"
    )
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            _run(paragraph, text[pos:m.start()], italic=italic, bold=bold, size=size)
        if m.group(3):
            run = paragraph.add_run(m.group(3))
            run.font.color.rgb = RGBColor(0x05, 0x63, 0xC1)
            run.font.underline = True
            run.font.size = Pt(size)
        else:
            cmd, inner = m.group(1), m.group(2)
            _run(
                paragraph,
                inner,
                italic=italic or cmd in ("emph", "textit"),
                bold=bold or cmd == "textbf",
                mono=cmd == "texttt",
                size=size,
            )
        pos = m.end()
    if pos < len(text):
        _run(paragraph, text[pos:], italic=italic, bold=bold, size=size)


def _run(paragraph, text, italic=False, bold=False, mono=False, size=11):
    if not text:
        return
    text = text.replace("{", "").replace("}", "")
    run = paragraph.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.size = Pt(size)
    if mono:
        run.font.name = "Consolas"
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:ascii"), "Consolas")
        rfonts.set(qn("w:hAnsi"), "Consolas")


def set_normal(paragraph, size=11, space_after=8):
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for run in paragraph.runs:
        if run.font.size is None:
            run.font.size = Pt(size)


def shade_header(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "1F4E79")
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)
    for p in cell.paragraphs:
        for run in p.runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.bold = True
            run.font.size = Pt(9)


def add_table(doc, caption: str, headers: list[str], rows: list[list[str]], note: str = ""):
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(12)
    cap.paragraph_format.space_after = Pt(4)
    add_runs(cap, caption, italic=True, size=10)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        add_runs(p, h, bold=True, size=9)
        shade_header(cell)
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            cell = table.rows[r_i + 1].cells[c_i]
            cell.text = ""
            add_runs(cell.paragraphs[0], val, size=9)
    if note:
        n = doc.add_paragraph()
        n.paragraph_format.space_after = Pt(10)
        add_runs(n, note, italic=True, size=9)


def parse_tabular(block: str) -> tuple[list[str], list[list[str]]]:
    m = re.search(r"\\begin\{tabular\}\{[^}]+\}(.*)\\end\{tabular\}", block, re.S)
    if not m:
        return [], []
    body = m.group(1)
    body = re.sub(r"\\(toprule|midrule|bottomrule)", "", body)
    body = re.sub(r"\\textbf\{([^}]*)\}", r"\1", body)
    rows = []
    for line in body.split(r"\\"):
        line = line.strip()
        if not line:
            continue
        cells = [decode_latex_chars(c.strip()) for c in line.split("&")]
        rows.append(cells)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def table_meta(path: Path) -> tuple[str, str, list[str], list[list[str]], str]:
    raw = path.read_text()
    cap = command_arg(raw, "caption") or ""
    lab = command_arg(raw, "label") or ""
    note_m = re.search(r"\\footnotesize\s*(.*?)\\end\{table\}", raw, re.S)
    caption = decode_latex_chars(cap)
    note = decode_latex_chars(note_m.group(1).strip()) if note_m else ""
    headers, rows = parse_tabular(raw)
    return lab, caption, headers, rows, note


def add_body_paragraphs(doc, text: str, cite_num: dict[str, int]):
    text = decode_latex_chars(text)
    text = replace_cites(text, cite_num)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    p = doc.add_paragraph()
    add_runs(p, text, size=11)
    set_normal(p)


def split_sections(tex: str) -> list[tuple[str, str, str]]:
    """Return list of (kind, title, body) where kind is section|subsection|body."""
    pieces = []
    pattern = re.compile(r"\\(sub)?section\*\{([^}]+)\}")
    last = 0
    last_kind, last_title = "body", ""
    for m in pattern.finditer(tex):
        chunk = tex[last:m.start()]
        pieces.append((last_kind, last_title, chunk))
        last_kind = "subsection" if m.group(1) else "section"
        last_title = m.group(2)
        last = m.end()
    pieces.append((last_kind, last_title, tex[last:]))
    return pieces


def expand_inputs(tex: str, base: Path) -> str:
    def repl(m):
        rel = m.group(1)
        path = (base / rel).resolve()
        if not path.exists() and not path.suffix:
            path = path.with_suffix(".tex")
        if path.exists():
            return path.read_text()
        return m.group(0)

    prev = None
    while prev != tex:
        prev = tex
        tex = re.sub(r"\\input\{([^}]+)\}", repl, tex)
    return tex


def strip_comments(tex: str) -> str:
    lines = []
    for line in tex.splitlines():
        if line.lstrip().startswith("%"):
            continue
        lines.append(re.sub(r"(?<!\\)%.*", "", line))
    return "\n".join(lines)


def extract_blocks(body: str):
    """Yield ('text'|'table'|'figure'|'enum', payload)."""
    body = strip_comments(body)
    pattern = re.compile(
        r"(\\begin\{table\*?\}.*?\\end\{table\*?\})"
        r"|(\\begin\{figure\*?\}.*?\\end\{figure\*?\})"
        r"|(\\begin\{enumerate\}.*?\\end\{enumerate\})",
        re.S,
    )
    pos = 0
    for m in pattern.finditer(body):
        before = body[pos:m.start()]
        if before.strip():
            yield "text", before
        block = m.group(0)
        if block.startswith(r"\begin{table"):
            yield "table", block
        elif block.startswith(r"\begin{figure"):
            yield "figure", block
        else:
            yield "enum", block
        pos = m.end()
    if body[pos:].strip():
        yield "text", body[pos:]


def add_enumerate(doc, block: str, cite_num: dict[str, int]):
    inner = re.search(r"\\begin\{enumerate\}(.*)\\end\{enumerate\}", block, re.S)
    if not inner:
        return
    items = re.split(r"\\item\s+", inner.group(1))
    n = 0
    for item in items:
        item = item.strip()
        if not item:
            continue
        n += 1
        item = decode_latex_chars(item)
        item = replace_cites(item, cite_num)
        item = re.sub(r"\s+", " ", item).strip()
        p = doc.add_paragraph(style="List Number")
        add_runs(p, item, size=11)


def add_figure(doc, block: str):
    caption = decode_latex_chars(command_arg(block, "caption") or "")
    label = command_arg(block, "label") or ""
    num = FIGURE_NUM.get(label, "?")
    images = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", block)
    panel_caps = re.findall(r"\\caption\*\{([^}]*)\}", block)

    for i, rel in enumerate(images):
        img = ROOT / rel
        if not img.exists():
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        width = Inches(5.8) if len(images) <= 2 else Inches(3.2)
        if label == "fig:benchmark":
            width = Inches(5.8)
        run.add_picture(str(img), width=width)
        if i < len(panel_caps):
            pc = doc.add_paragraph()
            pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(pc, decode_latex_chars(panel_caps[i]), italic=True, size=10)

    if label == "fig:pipeline":
        note = doc.add_paragraph()
        add_runs(
            note,
            "Figure 1 is a TikZ schematic in figures/fig1_pipeline.tex and was not "
            "rasterized in this Word export. The five stages are: (1) Data, "
            "(2) Processing, (3) Features, (4) Models, (5) Interpretation.",
            italic=True,
            size=10,
        )

    cap_p = doc.add_paragraph()
    cap_p.paragraph_format.space_after = Pt(12)
    add_runs(cap_p, f"Figure {num}. {caption}", italic=True, size=10)


def add_inline_table(doc, block: str, cite_num: dict[str, int]):
    note_m = re.search(r"\\footnotesize\s*(.*?)\\end\{table", block, re.S)
    label = command_arg(block, "label") or ""
    caption = decode_latex_chars(command_arg(block, "caption") or "")
    caption = replace_cites(caption, cite_num)
    note = decode_latex_chars(note_m.group(1).strip()) if note_m else ""
    note = replace_cites(note, cite_num)
    headers, rows = parse_tabular(block)
    num = TABLE_NUM.get(label, "?")
    add_table(doc, f"Table {num}. {caption}", headers, rows, note)


def process_body(doc, body: str, cite_num: dict[str, int]):
    for kind, payload in extract_blocks(body):
        if kind == "text":
            # drop leftover figure/table inputs already expanded
            payload = re.sub(r"\\(vspace|hfill|centering)\{?[^}]*\}?", " ", payload)
            payload = re.sub(r"\\noindent", "", payload)
            for para in re.split(r"\n\s*\n", payload):
                para = para.strip()
                if para:
                    add_body_paragraphs(doc, para, cite_num)
        elif kind == "table":
            add_inline_table(doc, payload, cite_num)
        elif kind == "figure":
            add_figure(doc, payload)
        elif kind == "enum":
            add_enumerate(doc, payload, cite_num)


def configure_styles(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    for name, size, bold in (("Heading 1", 16, True), ("Heading 2", 13, True)):
        h = doc.styles[name]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.bold = bold
        h.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)


def main():
    bib = parse_bib(ROOT / "references.bib")
    main_tex = strip_comments((ROOT / "main.tex").read_text())
    expanded = expand_inputs(main_tex, ROOT)
    expanded = strip_comments(expanded)

    # Collect citations in reading order from the body only.
    body_for_cites = decode_latex_chars(expanded)
    seen: list[str] = []
    collect_cites(body_for_cites, seen)
    cite_num = {k: i + 1 for i, k in enumerate(seen)}

    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(
        tp,
        "FORUM-TB: An Interpretable Machine Learning Framework for Multi-Drug "
        r"Resistance Prediction in \textit{Mycobacterium tuberculosis} from "
        "Whole-Genome Sequencing",
        size=18,
    )
    for run in tp.runs:
        run.bold = True
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(authors, "Nanzhen (Aspen) Qiao and Noah LeGall", bold=True, size=12)

    affil = doc.add_paragraph()
    affil.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(
        affil,
        "N. Qiao is with [INSERT AFFILIATION — INSTITUTION, DEPARTMENT], "
        "Kingston, ON, Canada. N. LeGall is with [INSERT AFFILIATION — "
        "INSTITUTION, DEPARTMENT], San Diego, CA, USA. "
        "E-mail: [INSERT EMAIL] (Corresponding author).",
        italic=True,
        size=10,
    )

    abs_h = doc.add_paragraph()
    add_runs(abs_h, "Abstract", bold=True, size=13)
    abstract = decode_latex_chars((ROOT / "sections" / "abstract.tex").read_text())
    abstract = replace_cites(abstract, cite_num)
    ap = doc.add_paragraph()
    add_runs(ap, abstract.strip(), size=11)
    set_normal(ap)

    kw = doc.add_paragraph()
    add_runs(kw, "Key words: ", bold=True, size=11)
    add_runs(
        kw,
        "Tuberculosis, antimicrobial resistance, whole-genome sequencing, "
        "machine learning, explainable AI, SHAP.",
        size=11,
    )

    section_files = [
        "sections/introduction.tex",
        "sections/results.tex",
        "sections/methods.tex",
        "sections/discussion.tex",
        "sections/backmatter.tex",
    ]
    for rel in section_files:
        tex = expand_inputs((ROOT / rel).read_text(), ROOT)
        for kind, title_s, body in split_sections(tex):
            if kind == "section" and title_s:
                doc.add_heading(title_s, level=1)
            elif kind == "subsection" and title_s:
                doc.add_heading(title_s, level=2)
            process_body(doc, body, cite_num)

    doc.add_heading("References", level=1)
    for key in seen:
        fields = bib.get(key, {"author": key, "title": "(missing bibliography entry)"})
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(6)
        add_runs(p, f"[{cite_num[key]}] {format_reference(fields)}", size=10)

    unused = [k for k in bib if k not in cite_num]
    if unused:
        # keep unused entries out of the numbered list
        pass

    doc.save(OUT)
    print(f"Wrote {OUT}")
    print(f"Citations: {len(seen)}   Bibliography entries: {len(bib)}")


if __name__ == "__main__":
    main()
