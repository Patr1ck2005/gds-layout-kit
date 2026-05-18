from __future__ import annotations

import gdstk
import pytest

from gds_layout_kit.primitives import (
    make_alignment_marker_cell,
    make_label_cell,
    make_metal_block_cell,
    make_pad_cell,
    make_ring_cell,
)


def test_pad_cell_geometry() -> None:
    cell = make_pad_cell("PAD", 10.0, 6.0)
    assert cell.name == "PAD"
    bbox = cell.bounding_box()
    assert bbox == ((-5.0, -3.0), (5.0, 3.0))


def test_ring_cell_uses_boolean_subtraction() -> None:
    cell = make_ring_cell("RING", outer_radius=10.0, inner_radius=6.0)
    assert cell.name == "RING"
    bbox = cell.bounding_box()
    assert bbox is not None
    assert bbox[0][0] < 0 < bbox[1][0]
    assert bbox[0][1] < 0 < bbox[1][1]
    assert len(cell.polygons) >= 1


def test_alignment_marker_and_label_exist() -> None:
    marker = make_alignment_marker_cell("MARKER", arm_length=20.0, arm_width=4.0)
    label = make_label_cell("LABEL", "Test", size=8.0)
    metal = make_metal_block_cell("METAL", 12.0, 8.0)

    assert marker.bounding_box() is not None
    assert label.bounding_box() is not None
    assert metal.bounding_box() == ((-6.0, -4.0), (6.0, 4.0))


def test_ring_cell_invalid_dimensions() -> None:
    with pytest.raises(ValueError):
        make_ring_cell("BAD", outer_radius=5.0, inner_radius=5.0)

