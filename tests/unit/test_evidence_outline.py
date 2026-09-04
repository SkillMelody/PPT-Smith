from __future__ import annotations

from engine.evidence_outline import build_evidence_outline
from engine.structural_parser import parse_markdown, parse_plain_text


def test_evidence_outline_preserves_section_anchors_and_numbers() -> None:
    doc = parse_markdown(
        "# Report\n\nPreamble 10%.\n\n## Growth\n\nRevenue reached $450 billion.\n",
        "src",
    )

    outline = build_evidence_outline(doc)

    assert outline["section_count"] == 2
    assert outline["sections"][0]["id"] == "h1_1"
    assert outline["sections"][0]["evidence"][0] == {
        "anchor": "para_1", "type": "para", "text": "Preamble 10%.", "numbers": ["10%"],
    }
    assert outline["sections"][1]["title"] == "Growth"
    assert outline["sections"][1]["evidence"][0]["anchor"] == "para_2"
    assert "450" in outline["sections"][1]["evidence"][0]["numbers"]


def test_evidence_outline_skips_an_empty_contents_section() -> None:
    doc = parse_plain_text("CONTENTS\n\nCHAPTER 1\n\nRevenue reached 450.", "src")

    outline = build_evidence_outline(doc)

    assert [section["title"] for section in outline["sections"]] == ["CHAPTER 1"]
    assert outline["sections"][0]["evidence"][0]["text"] == "Revenue reached 450."


def test_evidence_outline_creates_preamble_for_unheaded_plain_text() -> None:
    outline = build_evidence_outline(parse_plain_text("Evidence 57%.", "src"))

    assert outline["sections"] == [{
        "id": "preamble", "title": "Preamble", "level": 0,
        "evidence": [{"anchor": "para_1", "type": "para", "text": "Evidence 57%.", "numbers": ["57%"]}],
    }]
