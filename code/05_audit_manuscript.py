from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "Green_Bonds_Physical_Transition_Credibility_G20.md"
DOCX = ROOT / "deliverables" / "Green_Bonds_Physical_Transition_Credibility_G20_QAREOS.docx"
OUTPUT = ROOT / "verification" / "manuscript_audit.json"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    body, tail = text.split("## 8. References", 1)
    references, _ = tail.split("## 9. Supplementary Material", 1)
    entries = [line.strip() for line in references.splitlines() if line.strip()]

    reference_keys: set[tuple[str, str]] = set()
    for entry in entries:
        year_match = re.search(r"\((\d{4}[a-z]?)\)", entry)
        if not year_match:
            raise ValueError(f"Reference without year: {entry}")
        first = entry.split(",", 1)[0].split(".", 1)[0]
        if entry.startswith("International Capital Market Association"):
            first = "International Capital Market Association"
        elif entry.startswith("International Monetary Fund"):
            first = "International Monetary Fund"
        elif entry.startswith("Organisation for Economic Co-operation and Development"):
            first = "Organisation for Economic Co-operation and Development"
        elif entry.startswith("Our World in Data"):
            first = "Our World in Data"
        elif entry.startswith("World Bank"):
            first = "World Bank"
        reference_keys.add((normalize(first), year_match.group(1)))

    aliases = {
        normalize("ICMA"): normalize("International Capital Market Association"),
        normalize("IMF"): normalize("International Monetary Fund"),
        normalize("OECD"): normalize("Organisation for Economic Co-operation and Development"),
    }
    compact_body = re.sub(r"\s+", " ", body)
    uncited = []
    for author, year in sorted(reference_keys):
        names = [author]
        names.extend(alias for alias, canonical in aliases.items() if canonical == author)
        if not any(
            re.search(re.escape(name), normalize(compact_body[:match.end()]))
            for match in re.finditer(re.escape(year), compact_body)
            for name in names
            if len(normalize(compact_body[max(0, match.start() - 140):match.end()]))
            and name in normalize(compact_body[max(0, match.start() - 140):match.end()])
        ):
            uncited.append((author, year))
    unmatched_citations = []

    main_body = body.split("## Abstract", 1)[1]
    figure_checks = {f"Figure {n}": main_body.count(f"Figure {n}") >= 2 for n in range(1, 4)}
    table_checks = {f"Table {n}": main_body.count(f"Table {n}") >= 2 for n in range(1, 5)}

    with zipfile.ZipFile(DOCX) as archive:
        visible_parts = [
            name for name in archive.namelist()
            if (name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer"))
            and name.endswith(".xml")
        ]
        xml_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in visible_parts
        )
    rfont_tags = re.findall(r"<w:rFonts\b[^>]*/>", xml_text)
    fonts = sorted({font for tag in rfont_tags for font in re.findall(r'w:(?:ascii|hAnsi|eastAsia)="([^"]+)"', tag)})

    report = {
        "reference_entries": len(entries),
        "uncited_reference_keys": uncited,
        "unmatched_in_text_citation_keys": unmatched_citations,
        "figures_cited_in_flow": figure_checks,
        "tables_cited_in_flow": table_checks,
        "docx_fonts": fonts,
        "abstract_unnumbered": "## Abstract" in text and "## 0. Abstract" not in text,
        "numbered_main_sections": all(f"## {n}." in text for n in range(1, 10)),
        "pass": (
            len(entries) == 35
            and not uncited
            and not unmatched_citations
            and all(figure_checks.values())
            and all(table_checks.values())
            and fonts == ["Times New Roman"]
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("MANUSCRIPT AUDIT PASS" if report["pass"] else "MANUSCRIPT AUDIT FAIL")
    print(OUTPUT)
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
