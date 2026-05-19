from __future__ import annotations

from pathlib import Path

from matplotlib import image as mpimg

from gds_layout_kit.io import load_gds, top_cell_summary, write_gds
from gds_layout_kit.gradient_demo import _derive_grid_dimension, run_gradient_demo
from gds_layout_kit.metasurface import GradientMetasurfaceSpec, TrapezoidalGradientMetasurfaceSpec, build_gradient_metasurface_layout
from gds_layout_kit.preview import save_cell_preview


def test_gradient_metasurface_roundtrip(tmp_path: Path) -> None:
    assert issubclass(GradientMetasurfaceSpec, TrapezoidalGradientMetasurfaceSpec)

    spec = TrapezoidalGradientMetasurfaceSpec(rows=12, cols=18)
    result = build_gradient_metasurface_layout(spec)

    gds_path = tmp_path / "gradient.gds"
    png_path = tmp_path / "gradient.png"

    write_gds(result.library, gds_path)
    save_cell_preview(result.top_cell, png_path, crop_fraction=0.25, pixels_per_unit=28.0, max_total_pixels=60_000)

    assert gds_path.exists()
    assert png_path.exists()

    image = mpimg.imread(png_path)
    assert image.shape[0] > 20
    assert image.shape[1] > 20
    assert image.shape[0] * image.shape[1] <= 80_000

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
    assert "LAYOUT" in names  # Direct layout cell now instead of ROW_ cells


def test_gradient_demo_default_grid_is_mm_scale(tmp_path: Path) -> None:
    rows = _derive_grid_dimension(1000.0, 0.84, 0.93)
    cols = _derive_grid_dimension(1000.0, 0.84, 0.93)
    assert rows >= 1000
    assert cols >= 1000

    result = run_gradient_demo(
        rows=12,
        cols=16,
        output_dir=tmp_path / "demo",
        preview_pixels_per_unit=20.0,
        preview_max_total_pixels=25_000,
    )
    assert result.gds_path.exists()
    assert result.png_path.exists()
    assert result.x_extent_um > 0
    assert result.y_extent_um > 0


def test_gradient_metasurface_invalid_fill_range() -> None:
    spec = TrapezoidalGradientMetasurfaceSpec(fill_min=0.7, fill_max=0.6)
    try:
        build_gradient_metasurface_layout(spec)
    except ValueError as exc:
        assert "fill range" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid fill range")

