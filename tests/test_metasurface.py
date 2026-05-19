from __future__ import annotations

from pathlib import Path

from gds_layout_kit.io import load_gds, top_cell_summary, write_gds
from gds_layout_kit.metasurface import GradientMetasurfaceSpec, build_gradient_metasurface_layout
from gds_layout_kit.preview import save_cell_preview


def test_gradient_metasurface_roundtrip(tmp_path: Path) -> None:
    spec = GradientMetasurfaceSpec(rows=12, cols=18, trapezoid_top_scale=0.9)
    result = build_gradient_metasurface_layout(spec)

    gds_path = tmp_path / "gradient.gds"
    png_path = tmp_path / "gradient.png"

    write_gds(result.library, gds_path)
    save_cell_preview(result.top_cell, png_path)

    assert gds_path.exists()
    assert png_path.exists()

    loaded = load_gds(gds_path)
    summary = top_cell_summary(loaded)
    assert summary
    assert any(item["name"] == spec.top_name for item in summary)

    top_items = [item for item in summary if item["name"] == spec.top_name]
    assert len(top_items) == 1
    bbox = top_items[0]["bbox"]
    assert bbox is not None
    (xmin, ymin), (xmax, ymax) = bbox
    assert xmax > xmin
    assert ymax > ymin

    names = {cell.name for cell in loaded.cells}
    assert spec.top_name in names
    assert any(name.startswith("ROW_") for name in names)


def test_gradient_metasurface_invalid_fill_range() -> None:
    spec = GradientMetasurfaceSpec(fill_min=0.7, fill_max=0.6)
    try:
        build_gradient_metasurface_layout(spec)
    except ValueError as exc:
        assert "fill range" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid fill range")

