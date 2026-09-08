from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from engine.template_visual_fingerprint import (
    evaluate_rendered_layout_rhythm,
    fingerprint_distance,
    image_layout_fingerprint,
)


def _render(path: Path, *, hero: str, dark: bool = False) -> None:
    background = (24, 29, 38) if dark else (255, 255, 255)
    foreground = (225, 225, 225) if dark else (30, 30, 30)
    image = Image.new("RGB", (640, 360), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((35, 25, 600, 55), fill=foreground)
    if hero == "left":
        draw.rectangle((45, 100, 360, 310), fill=foreground)
        draw.rectangle((400, 100, 600, 180), fill=foreground)
        draw.rectangle((400, 205, 600, 285), fill=foreground)
    elif hero == "right":
        draw.rectangle((280, 100, 595, 310), fill=foreground)
        draw.rectangle((40, 100, 240, 180), fill=foreground)
        draw.rectangle((40, 205, 240, 285), fill=foreground)
    elif hero == "top":
        draw.rectangle((45, 90, 595, 205), fill=foreground)
        draw.rectangle((45, 235, 280, 310), fill=foreground)
        draw.rectangle((320, 235, 595, 310), fill=foreground)
    image.save(path)


def test_visual_fingerprint_groups_left_right_mirrors_across_template_colours(tmp_path: Path) -> None:
    left = tmp_path / "light-left.png"
    right = tmp_path / "dark-right.png"
    _render(left, hero="left")
    _render(right, hero="right", dark=True)

    distance = fingerprint_distance(
        image_layout_fingerprint(left), image_layout_fingerprint(right),
    )

    assert distance <= 0.14


def test_rendered_rhythm_rejects_same_visual_skeleton_despite_different_variant_names(tmp_path: Path) -> None:
    slides = []
    pages = []
    for index in range(8):
        path = tmp_path / f"slide-{index + 1}.png"
        _render(path, hero="left" if index % 2 == 0 else "right")
        slides.append({"slide_index": index + 1, "image": str(path)})
        pages.append({
            "slide_id": f"S{index + 1:02d}", "page_role": "body",
            "recipe": f"declared-{index}", "variant": "left" if index % 2 == 0 else "right",
        })

    report = evaluate_rendered_layout_rhythm(
        {"slides": slides}, page_composition={"pages": pages},
    )

    assert report["status"] == "fail"
    assert report["unique_rendered_layout_count"] == 1
    assert "TEMPLATE_RENDERED_LAYOUT_OVERUSED" in {
        issue["code"] for issue in report["issues"]
    }


def test_comparison_series_may_share_a_rendered_grid_when_scale_is_declared(tmp_path: Path) -> None:
    slides = []
    pages = []
    for index in range(5):
        path = tmp_path / f"country-{index + 1}.png"
        _render(path, hero="left")
        slides.append({"slide_index": index + 1, "image": str(path)})
        pages.append({
            "slide_id": f"C{index + 1}", "page_role": "body",
            "series_context": {
                "group_id": "country-comparison", "purpose": "comparison",
                "shared_scale": True,
            },
        })

    report = evaluate_rendered_layout_rhythm(
        {"slides": slides}, page_composition={"pages": pages},
    )

    assert report["status"] == "pass"
