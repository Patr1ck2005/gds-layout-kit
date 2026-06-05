from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib import image as mpimg

from gds_layout_kit.grating import (
    GratingGradientResult,
    GratingGradientSpec,
    build_grating_gradient_layout,
    save_grating_gradient_layout_files,
)
from gds_layout_kit.grating_demo import run_grating_demo
from gds_layout_kit.io import load_gds, top_cell_summary, write_gds
from gds_layout_kit.preview import save_cell_preview


def test_grating_gradient_roundtrip(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=12, cols=18)
    result = build_grating_gradient_layout(spec)

    gds_path = tmp_path / "grating.gds"
    png_path = tmp_path / "grating.png"

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
    assert "LAYOUT" in names


def test_grating_gradient_negative_tone(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=12, cols=18, tone="negative")
    result = build_grating_gradient_layout(spec)

    gds_path = tmp_path / "grating_neg.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()

    loaded = load_gds(gds_path)
    names = {cell.name for cell in loaded.cells}
    assert "LAYOUT" in names


def test_grating_gradient_positive_tone(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=12, cols=18, tone="positive")
    result = build_grating_gradient_layout(spec)

    gds_path = tmp_path / "grating_pos.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()

    loaded = load_gds(gds_path)
    names = {cell.name for cell in loaded.cells}
    assert "LAYOUT" in names


def test_grating_spec_invalid_dc_range() -> None:
    spec = GratingGradientSpec(dc_min=0.6, dc_max=0.4)
    with pytest.raises(ValueError, match="dc range"):
        build_grating_gradient_layout(spec)


def test_grating_spec_invalid_dc_bound() -> None:
    spec = GratingGradientSpec(dc_min=0.8, dc_max=1.0)
    with pytest.raises(ValueError, match="dc range"):
        build_grating_gradient_layout(spec)


def test_grating_spec_invalid_dc_lower_bound() -> None:
    spec = GratingGradientSpec(dc_min=-0.1, dc_max=0.5)
    with pytest.raises(ValueError, match="dc range"):
        build_grating_gradient_layout(spec)


def test_grating_spec_invalid_tone() -> None:
    spec = GratingGradientSpec(tone="inverted")
    with pytest.raises(ValueError, match="tone"):
        build_grating_gradient_layout(spec)


def test_grating_spec_invalid_pitch() -> None:
    spec = GratingGradientSpec(pitch_min_um=0.7, pitch_max_um=0.5)
    with pytest.raises(ValueError):
        build_grating_gradient_layout(spec)


def test_grating_spec_too_few_rows() -> None:
    spec = GratingGradientSpec(rows=1, cols=10)
    with pytest.raises(ValueError):
        build_grating_gradient_layout(spec)


def test_grating_spec_too_few_cols() -> None:
    spec = GratingGradientSpec(rows=10, cols=1)
    with pytest.raises(ValueError):
        build_grating_gradient_layout(spec)


def test_grating_dc_edge_cases(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=8, cols=10, dc_min=0.0, dc_max=0.99)
    result = build_grating_gradient_layout(spec)
    assert result.x_extent_um > 0
    assert result.y_extent_um > 0

    gds_path = tmp_path / "grating_edge.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()


def test_grating_save_with_grid(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=8, cols=10, show_grid=True)
    result = build_grating_gradient_layout(spec)
    gds_path = tmp_path / "grating.gds"
    png_path = tmp_path / "grating.png"
    gds_out, png_out, grid_out = save_grating_gradient_layout_files(
        result, gds_path, png_path, preview_max_total_pixels=25_000,
    )
    assert grid_out is not None
    assert grid_out.exists()
    assert png_out.exists()


def test_grating_demo_run(tmp_path: Path) -> None:
    result = run_grating_demo(
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


def test_grating_demo_negative_tone(tmp_path: Path) -> None:
    result = run_grating_demo(
        rows=8,
        cols=10,
        tone="negative",
        output_dir=tmp_path / "demo_neg",
        preview_max_total_pixels=25_000,
    )
    assert result.gds_path.exists()
    assert result.png_path.exists()


def test_grating_right_trapezoid(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=12, cols=18, rectangular=False, center_aligned=False)
    result = build_grating_gradient_layout(spec)
    assert result.x_extent_um > 0
    assert result.y_extent_um > 0

    gds_path = tmp_path / "grating_right.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()


def test_grating_trapezoidal_mode(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=12, cols=18, rectangular=False, center_aligned=True)
    result = build_grating_gradient_layout(spec)
    assert result.x_extent_um > 0
    assert result.y_extent_um > 0

    gds_path = tmp_path / "grating_trap.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()

    loaded = load_gds(gds_path)
    names = {cell.name for cell in loaded.cells}
    assert "LAYOUT" in names


def test_grating_rectangular_is_default(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=8, cols=10)
    assert spec.rectangular is True
    result = build_grating_gradient_layout(spec)
    # Rectangular: y_extent uses mean_period, not pitch_max * rows
    mean_period = (spec.pitch_min_um + spec.pitch_max_um) / 2.0
    assert result.y_extent_um == pytest.approx(spec.rows * mean_period)


def test_grating_rectangular_negative_tone(tmp_path: Path) -> None:
    spec = GratingGradientSpec(rows=8, cols=10, rectangular=True, tone="negative")
    result = build_grating_gradient_layout(spec)
    assert result.x_extent_um > 0

    gds_path = tmp_path / "grating_rect_neg.gds"
    write_gds(result.library, gds_path)
    assert gds_path.exists()
