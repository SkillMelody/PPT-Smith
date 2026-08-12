"""Style pack loader: Style Contract v4 data pack -> resolved values.

The pack is validated data (schemas/v4/style-contract-v4.schema.json);
this module resolves token references and layout knobs into the concrete
numbers the layout engine and builders consume. No policy decisions here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

EMU_PER_PT = 12700
EMU_PER_IN = 914400

DEFAULT_PACK = Path(__file__).resolve().parents[1] / "styles/editorial-knowledge.json"

_DENSITY_GAP_PT = {"airy": 16, "regular": 12, "compact": 8}


@dataclass
class ResolvedStyle:
    pack_id: str
    version: str
    colors: dict
    typography: dict
    shape: dict
    skins: dict
    chart: dict
    density: str = "regular"
    margin_scale: float = 1.0
    alignment: str = "left"
    raw: dict = field(default_factory=dict)

    def color(self, token: str, fallback: str = "#000000") -> str:
        return self.colors.get(token, fallback)

    def skin_color(self, skin: str, key: str, default_token: str) -> str:
        token = (self.skins.get(skin) or {}).get(key, default_token)
        return self.color(token, self.color(default_token))

    def font(self, kind: str = "primary") -> str:
        stack = self.typography.get(f"font_{kind}") or self.typography.get("font_primary") or ["Calibri"]
        return stack[0]

    def size_cpt(self, group: str, level: str) -> int:
        table = self.typography.get(f"{group}_sizes_pt") or {}
        value = table.get(level)
        if value is None:
            value = {"title": 22, "body": 13, "metric": 22}.get(group.split("_")[0], 13)
        return int(round(float(value) * 100))

    def body_levels_cpt(self) -> list[int]:
        """Descending body sizes for deterministic step-down (D9)."""
        table = self.typography.get("body_sizes_pt") or {}
        levels = [table.get(k) for k in ("large", "normal", "small") if table.get(k)]
        return [int(round(float(v) * 100)) for v in levels] or [1300]

    def gap_emu(self) -> int:
        return _DENSITY_GAP_PT[self.density] * EMU_PER_PT

    def margin_emu(self) -> int:
        return int(round(0.92 * EMU_PER_IN * self.margin_scale))

    def weight(self, name: str, default: int = 400) -> int:
        return int((self.typography.get("weights") or {}).get(name, default))


def load_style_pack(path: str | Path | None = None) -> ResolvedStyle:
    pack = json.loads(Path(path or DEFAULT_PACK).read_text(encoding="utf-8"))
    tokens = pack.get("tokens", {})
    knobs = pack.get("layout_knobs", {})
    return ResolvedStyle(
        pack_id=pack["pack"]["pack_id"],
        version=pack["pack"]["version"],
        colors=tokens.get("colors", {}),
        typography=tokens.get("typography", {}),
        shape=tokens.get("shape", {}),
        skins=pack.get("skins", {}),
        chart=tokens.get("chart", {}),
        density=knobs.get("density", "regular"),
        margin_scale=float(knobs.get("margin_scale", 1.0)),
        alignment=knobs.get("alignment", "left"),
        raw=pack,
    )
