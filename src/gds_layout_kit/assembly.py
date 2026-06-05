"""Top-level assembly helpers for the demo layout."""

from __future__ import annotations

from dataclasses import dataclass

import gdstk

from .primitives import (
    make_alignment_marker_cell,
    make_label_cell,
    make_metal_block_cell,
    make_pad_cell,
    make_ring_cell,
)


@dataclass(frozen=True)
class DemoLayoutCells:
    """Convenient bundle of the demo cells."""

    pad: gdstk.Cell
    metal: gdstk.Cell
    ring: gdstk.Cell
    marker: gdstk.Cell
    label: gdstk.Cell
    top: gdstk.Cell


def build_demo_layout() -> tuple[gdstk.Library, DemoLayoutCells]:
    """Build a minimal library containing a top-level demo layout."""

    library = gdstk.Library(unit=1e-6, precision=1e-11)

    pad = make_pad_cell("PAD", 120.0, 80.0)
    metal = make_metal_block_cell("METAL", 90.0, 50.0)
    ring = make_ring_cell("RING", outer_radius=35.0, inner_radius=22.0)
    marker = make_alignment_marker_cell("MARKER", arm_length=70.0, arm_width=8.0)
    label = make_label_cell("LABEL", "GDS Layout Kit", size=12.0)

    top = gdstk.Cell("TOP")
    top.add(gdstk.Reference(pad, origin=(0.0, 0.0)))
    top.add(gdstk.Reference(metal, origin=(180.0, 0.0)))
    top.add(gdstk.Reference(ring, origin=(0.0, 140.0)))
    top.add(gdstk.Reference(marker, origin=(180.0, 140.0)))
    top.add(gdstk.Reference(label, origin=(-40.0, -70.0)))

    library.add(pad, metal, ring, marker, label, top)
    return library, DemoLayoutCells(pad=pad, metal=metal, ring=ring, marker=marker, label=label, top=top)

