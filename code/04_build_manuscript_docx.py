from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "Green_Bonds_Physical_Transition_Credibility_G20.md"
OUTPUT_DIR = ROOT / "deliverables"
OUTPUT = OUTPUT_DIR / "Green_Bonds_Physical_Transition_Credibility_G20_QAREOS.docx"
FIGURES = ROOT / "figures"
RESULTS = ROOT / "results"

FONT = "Times New Roman"
INK = RGBColor(0, 0, 0)
LIGHT_GRAY = "E7E6E6"
VERY_LIGHT_GRAY = "F7F7F7"
CONTENT_DXA = 9648
TABLE_INDENT_DXA = 120


def set_run_font(run, size=11, bold=None, italic=None, color=INK):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.color.rgb = color
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def set_style_font(style, size, bold=False, italic=False):
    style.font.name = FONT
    style._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    style._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = italic
    style.font.color.rgb = INK


def add_field(paragraph, instruction: str, display: str):
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), instruction)
    field.set(qn("w:dirty"), "true")
    text_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), FONT)
    rfonts.set(qn("w:hAnsi"), FONT)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "18")
    rpr.extend([rfonts, sz])
    text = OxmlElement("w:t")
    text.text = display
    text_run.extend([rpr, text])
    field.append(text_run)
    paragraph._p.append(field)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths_dxa):
    if sum(widths_dxa) != CONTENT_DXA:
        raise ValueError(f"Table widths must total {CONTENT_DXA}: {widths_dxa}")
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(CONTENT_DXA))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(TABLE_INDENT_DXA))
    tbl_ind.set(qn("w:type"), "dxa")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for idx, (cell, width) in enumerate(zip(row.cells, widths_dxa)):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(width))
            tc_w.set(qn("w:type"), "dxa")
            cell.width = Inches(width / 1440)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)


def format_table(table, widths_dxa):
    set_table_geometry(table, widths_dxa)
    table.style = "Table Grid"
    set_repeat_table_header(table.rows[0])
    for row_idx, row in enumerate(table.rows):
        if row_idx == 0:
            set_cell_shading(row.cells[0], LIGHT_GRAY)
            for c in row.cells[1:]:
                set_cell_shading(c, LIGHT_GRAY)
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    set_run_font(run, size=8.5, bold=(row_idx == 0))


def width_pattern(ncols: int, headers: list[str]) -> list[int]:
    if ncols == 4 and headers and "Definition" in headers:
        return [1800, 3800, 1800, 2248]
    if ncols == 4:
        return [3200, 2100, 2100, 2248]
    if ncols == 5:
        return [3200, 1750, 1800, 1750, 1148]
    if ncols == 6:
        return [2550, 1500, 1350, 1700, 1300, 1248]
    if ncols == 7:
        return [1000, 1800, 700, 950, 1700, 1748, 1750]
    base = CONTENT_DXA // ncols
    widths = [base] * ncols
    widths[-1] += CONTENT_DXA - sum(widths)
    return widths


def add_rich_text(paragraph, text: str, size=11):
    inline_math = {
        r"\(I_{it}\)": "Iᵢₜ",
        r"\(GDP_{it}\)": "GDPᵢₜ",
        r"\(GB_{it}\)": "GBᵢₜ",
        r"\(R_{it}\)": "Rᵢₜ",
        r"\(C_{it}\)": "Cᵢₜ",
        r"\(G_{it}\)": "Gᵢₜ",
        r"\(O_{it}\)": "Oᵢₜ",
        r"\(F_{it}=C_{it}+G_{it}+O_{it}\)": "Fᵢₜ = Cᵢₜ + Gᵢₜ + Oᵢₜ",
        r"\(Y^{R}_{it}=\mathbb{1}(\Delta R_{it}>0)\)": "Yᴿᵢₜ = 1(ΔRᵢₜ > 0)",
        r"\(Y^{C}_{it}=\mathbb{1}(\Delta C_{it}<0)\)": "Yᶜᵢₜ = 1(ΔCᵢₜ < 0)",
        r"\(Y^{k}_{it}\)": "Yᵏᵢₜ",
        r"\(\alpha_i\)": "αᵢ",
        r"\(\lambda_t\)": "λₜ",
        r"\(\beta_k\)": "βₖ",
        r"\(t(G-1)\)": "t(G−1)",
        r"\(i\)": "i",
        r"\(t\)": "t",
    }
    for source, replacement in inline_math.items():
        text = text.replace(source, replacement)
    text = text.replace("`", "")
    pattern = re.compile(r"(\*\*.*?\*\*|\*.*?\*)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            set_run_font(run, size=size)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, size=size, bold=True)
        else:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, size=size, italic=True)
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run_font(run, size=size)


def transform_equation(text: str) -> str:
    clean = " ".join(line.strip() for line in text.splitlines())
    replacements = {
        r"GB_{it}=10{,}000\times\frac{I_{it}}{GDP_{it}},": "GBᵢₜ = 10,000 × Iᵢₜ / GDPᵢₜ",
        r"Y^{F}_{it}=\mathbb{1}(\Delta F_{it}<0).": "Yᶠᵢₜ = 1(ΔFᵢₜ < 0)",
        r"Y^{U}_{it}=\mathbb{1}(\Delta C_{it}<0\;\land\;\Delta G_{it}+\Delta O_{it}\leq0).": "Yᵘᵢₜ = 1(ΔCᵢₜ < 0 and ΔGᵢₜ + ΔOᵢₜ ≤ 0)",
        r"Y^{k}_{it}=\beta_k GB_{it}+\alpha_i+\lambda_t+\varepsilon_{it},": "Yᵏᵢₜ = βₖGBᵢₜ + αᵢ + λₜ + εᵢₜ",
    }
    return replacements.get(clean, clean.replace("\\", ""))


def add_caption(doc, text: str, label: str):
    p = doc.add_paragraph(style="Manuscript Caption")
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, size=9.5, bold=True)
    return p


def add_note(doc, text: str):
    text = text.strip()
    if text.startswith("*") and text.endswith("*"):
        text = text[1:-1]
    p = doc.add_paragraph(style="Manuscript Note")
    add_rich_text(p, text, size=9)
    return p


def fixed(value, digits=2):
    return f"{float(value):.{digits}f}".replace("-", "−")


def p_value(value):
    value = float(value)
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def add_dataframe_table(doc, frame: pd.DataFrame, widths=None):
    display = frame.fillna("—").astype(str)
    table = doc.add_table(rows=1, cols=len(display.columns))
    for idx, col in enumerate(display.columns):
        table.rows[0].cells[idx].text = str(col)
    for values in display.itertuples(index=False, name=None):
        cells = table.add_row().cells
        for idx, value in enumerate(values):
            cells[idx].text = str(value)
    format_table(table, widths or width_pattern(len(display.columns), list(display.columns)))
    return table


def supplement_table(doc, code: str):
    if code == "9.1":
        df = pd.read_csv(RESULTS / "country_summary.csv")
        out = pd.DataFrame({
            "ISO3": df.iso3,
            "Country": df.country,
            "Years": df.years.astype(int),
            "Issuance years": df.positive_issuance_years.astype(int),
            "Fossil contraction (%)": (100 * df.fossil_contraction_rate).round(1),
            "Renewable addition (%)": (100 * df.renewable_addition_rate).round(1),
            "Unoffset coal (%)": (100 * df.unoffset_coal_contraction_rate).round(1),
        })
        add_dataframe_table(doc, out, [850, 1650, 650, 1100, 1800, 1800, 1798])
        add_note(doc, "Note. Coal outcomes are blank where the coal-eligibility condition is not met.")
    elif code == "9.2":
        df = pd.read_csv(RESULTS / "loco_all_outcomes.csv")
        panels = [
            ("A", "Fossil contraction", "fossil_contraction"),
            ("B", "Renewable addition", "renewable_addition"),
            ("C", "Coal contraction", "coal_contraction"),
            ("D", "Unoffset coal contraction", "unoffset_coal_contraction"),
        ]
        for idx, (panel, label, outcome) in enumerate(panels):
            if idx:
                doc.add_page_break()
            p = doc.add_paragraph(style="Manuscript Caption")
            add_rich_text(p, f"Panel {panel}. {label}", size=9.5)
            part = df.loc[df.outcome.eq(outcome)]
            out = pd.DataFrame({
                "Omitted country": part.excluded_country,
                "N": part.n.astype(int),
                "Effect per 10 bp (pp)": (1000 * part.coefficient).map(fixed),
                "95% CI": (1000 * part.ci_low).map(fixed) + " to " + (1000 * part.ci_high).map(fixed),
            })
            add_dataframe_table(doc, out, [2200, 900, 2600, 3948])
        add_note(doc, "Note. Each row re-estimates the country- and year-fixed-effects model after omitting one country. Effects are percentage-point changes per 10 basis points of issuance/GDP.")
    elif code == "9.3":
        df = pd.read_csv(RESULTS / "descriptive_cluster_bootstrap.csv")
        out = pd.DataFrame({
            "Outcome": df.label,
            "Estimate (%)": (100 * df.point_estimate).round(2),
            "95% CI low": (100 * df.ci_low).round(2),
            "95% CI high": (100 * df.ci_high).round(2),
            "Countries": df.eligible_countries.astype(int),
        })
        add_dataframe_table(doc, out, [3600, 1600, 1600, 1600, 1248])
        add_note(doc, "Note. Percentile intervals use 20,000 country-cluster replications and the fixed project seed 20260904.")
    elif code == "9.4":
        df = pd.read_csv(RESULTS / "physical_magnitudes_by_issuance.csv")
        out = pd.DataFrame({
            "Issuance status": df.issuance_status,
            "Generation change": df.label,
            "N": df.n.astype(int),
            "Mean TWh": df.mean_twh.round(2),
            "Median TWh": df.median_twh.round(2),
            "IQR TWh": df.q25_twh.round(2).astype(str) + " to " + df.q75_twh.round(2).astype(str),
        })
        add_dataframe_table(doc, out, [2100, 2700, 600, 1100, 1300, 1848])
        add_note(doc, "Note. Positive values indicate generation increases; negative values indicate contractions.")
    elif code == "9.5":
        main = pd.read_csv(RESULTS / "main_models.csv")
        thr = pd.read_csv(RESULTS / "threshold_models_all_outcomes.csv")
        frames = []
        for label, df in [("Strict sign", main), ("0.10%", thr[thr.specification.eq("0.10% materiality")]), ("0.25%", thr[thr.specification.eq("0.25% materiality")])]:
            temp = pd.DataFrame({
                "Rule": label,
                "Outcome": df.outcome.str.replace("_m010", "", regex=False).str.replace("_m025", "", regex=False).map({
                    "fossil_contraction": "Fossil contraction",
                    "renewable_addition": "Renewable addition",
                    "coal_contraction": "Coal contraction",
                    "unoffset_coal_contraction": "Unoffset coal contraction",
                }),
                "N": df.n.astype(int),
                "Effect per 10 bp (pp)": (1000 * df.coefficient).map(fixed),
                "95% CI": (1000 * df.ci_low).map(fixed) + " to " + (1000 * df.ci_high).map(fixed),
                "p-value": df.p_value_t_g_minus_1.map(p_value),
            })
            frames.append(temp)
        add_dataframe_table(doc, pd.concat(frames, ignore_index=True), [1250, 2600, 650, 1900, 2000, 1248])
        add_note(doc, "Note. Models include country and year fixed effects with CRV3 country-clustered inference.")


def create_document():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)

    settings = doc.settings._element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")

    styles = doc.styles
    normal = styles["Normal"]
    set_style_font(normal, 11)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name in ["Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption", "Table Grid"]:
        if name in styles:
            set_style_font(styles[name], 11)

    title_style = styles.add_style("Manuscript Title", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(title_style, 18, bold=True)
    title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_style.paragraph_format.space_before = Pt(0)
    title_style.paragraph_format.space_after = Pt(12)
    title_style.paragraph_format.keep_with_next = True

    heading_style = styles.add_style("Manuscript Section", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(heading_style, 11.5, bold=True)
    heading_style.paragraph_format.space_before = Pt(10)
    heading_style.paragraph_format.space_after = Pt(5)
    heading_style.paragraph_format.keep_with_next = True
    heading_style.paragraph_format.keep_together = True

    caption_style = styles.add_style("Manuscript Caption", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(caption_style, 9.5, bold=True)
    caption_style.paragraph_format.space_before = Pt(5)
    caption_style.paragraph_format.space_after = Pt(2)
    caption_style.paragraph_format.keep_with_next = True

    note_style = styles.add_style("Manuscript Note", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(note_style, 9, italic=True)
    note_style.paragraph_format.space_before = Pt(2)
    note_style.paragraph_format.space_after = Pt(6)
    note_style.paragraph_format.line_spacing = 1.0
    note_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    equation_style = styles.add_style("Manuscript Equation", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(equation_style, 11, italic=True)
    equation_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    equation_style.paragraph_format.space_before = Pt(4)
    equation_style.paragraph_format.space_after = Pt(4)

    reference_style = styles.add_style("Manuscript Reference", WD_STYLE_TYPE.PARAGRAPH)
    set_style_font(reference_style, 9.5)
    reference_style.paragraph_format.left_indent = Inches(0.3)
    reference_style.paragraph_format.first_line_indent = Inches(-0.3)
    reference_style.paragraph_format.space_after = Pt(4)
    reference_style.paragraph_format.line_spacing = 1.0
    reference_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = header.add_run("Green Bonds and Physical Transition Credibility")
    set_run_font(hr, size=8.5, italic=True, color=RGBColor(89, 89, 89))
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run("Page ")
    set_run_font(fr, size=9)
    add_field(footer, "PAGE", "1")

    doc.core_properties.title = "Green Bonds without Fossil Exit? Physical Transition Credibility in G20 Electricity Systems"
    doc.core_properties.subject = "Jurisdiction-level financial-physical alignment in G20 electricity systems"
    doc.core_properties.author = ""
    doc.core_properties.keywords = "green bonds; transition finance; fossil electricity; G20"

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    i = 0
    in_references = False
    skip_placeholder = False
    pending_table_caption = None
    fig_map = {
        "1": FIGURES / "figure_1_annual_alignment.png",
        "2": FIGURES / "figure_2_outcomes_by_issuance.png",
        "3": FIGURES / "figure_3_fixed_effects_estimates.png",
    }

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue

        if skip_placeholder and not line.startswith("###"):
            skip_placeholder = False
            i += 1
            continue

        if line.startswith("# "):
            p = doc.add_paragraph(style="Manuscript Title")
            add_rich_text(p, line[2:], size=18)
            i += 1
            continue

        if line.startswith("## ") or line.startswith("### "):
            text = re.sub(r"^#{2,3}\s+", "", line)
            if text.startswith("9. Supplementary Material"):
                doc.add_page_break()
            if text.startswith("9.2. Table S2"):
                doc.add_page_break()
            p = doc.add_paragraph(style="Manuscript Section")
            add_rich_text(p, text, size=11.5)
            in_references = text.startswith("8. References")
            code_match = re.match(r"(9\.[1-5])\.", text)
            if code_match:
                supplement_table(doc, code_match.group(1))
                skip_placeholder = True
            i += 1
            continue

        if line == r"\[":
            eq_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != r"\]":
                eq_lines.append(lines[i])
                i += 1
            p = doc.add_paragraph(style="Manuscript Equation")
            run = p.add_run(transform_equation("\n".join(eq_lines)))
            set_run_font(run, size=11, italic=True)
            i += 1
            continue

        table_caption_match = re.match(r"\*\*Table\s+([^.]*)\.\s*(.*?)\*\*$", line)
        if table_caption_match:
            pending_table_caption = f"Table {table_caption_match.group(1)}. {table_caption_match.group(2)}"
            i += 1
            continue

        figure_caption_match = re.match(r"\*\*Figure\s+(\d+)\.\s*(.*?)\*\*$", line)
        if figure_caption_match:
            num, title = figure_caption_match.groups()
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.keep_with_next = True
            p_img.paragraph_format.space_after = Pt(2)
            p_img.add_run().add_picture(str(fig_map[num]), width=Inches(6.25))
            add_caption(doc, f"Figure {num}. {title}", "Figure")
            i += 1
            continue

        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in rows if not all(re.fullmatch(r":?-{3,}:?", c or "---") for c in r)]
            if pending_table_caption:
                add_caption(doc, pending_table_caption, "Table")
                pending_table_caption = None
            frame = pd.DataFrame(rows[1:], columns=rows[0])
            add_dataframe_table(doc, frame)
            continue

        if line.startswith("*Note.") or line.startswith("*Note "):
            add_note(doc, line)
            i += 1
            continue

        if in_references:
            p = doc.add_paragraph(style="Manuscript Reference")
            add_rich_text(p, line, size=9.5)
            i += 1
            continue

        p = doc.add_paragraph(style="Normal")
        if line.startswith("**Keywords:**"):
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_rich_text(p, line, size=11)
        i += 1

    # Mark all tables against row splitting only for their header; body rows may split if required.
    for table in doc.tables:
        tr_pr = table.rows[0]._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)

    # Enforce Times New Roman for every visible run, including tables and footer fields.
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            size = run.font.size.pt if run.font.size else 11
            set_run_font(run, size=size, bold=run.bold, italic=run.italic, color=run.font.color.rgb or INK)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        set_run_font(run, size=run.font.size.pt if run.font.size else 8.5, bold=run.bold, italic=run.italic)

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    create_document()
