"""Reusable GDS primitives for the minimal layout kit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import gdstk

Point = Tuple[float, float]


@dataclass(frozen=True)
class LayerSpec:
    """Simple layer/datatype pair used by the demo project."""

    layer: int
    datatype: int = 0


PAD_LAYER = LayerSpec(layer=1)
RING_LAYER = LayerSpec(layer=2)
MARKER_LAYER = LayerSpec(layer=3)
TEXT_LAYER = LayerSpec(layer=4)


def make_pad_cell(
    name: str,
    width: float,
    height: float,
    *,
    layer: int = PAD_LAYER.layer,
    datatype: int = PAD_LAYER.datatype,
) -> gdstk.Cell:
    """Create a rectangular pad or metal block centered at the origin."""

    cell = gdstk.Cell(name)
    half_w = width / 2.0
    half_h = height / 2.0
    cell.add(gdstk.rectangle((-half_w, -half_h), (half_w, half_h), layer=layer, datatype=datatype))
    return cell


def make_metal_block_cell(
    name: str,
    width: float,
    height: float,
    *,
    layer: int = PAD_LAYER.layer,
    datatype: int = PAD_LAYER.datatype,
) -> gdstk.Cell:
    """Alias for a rectangular metal block used in the demo layout."""

    return make_pad_cell(name, width, height, layer=layer, datatype=datatype)


def make_ring_cell(
    name: str,
    outer_radius: float,
    inner_radius: float,
    *,
    layer: int = RING_LAYER.layer,
    datatype: int = RING_LAYER.datatype,
    tolerance: float = 1e-11,
) -> gdstk.Cell:
    """Create an annulus by subtracting an inner circle from an outer circle."""

    if inner_radius <= 0:
        raise ValueError("inner_radius must be positive")
    if outer_radius <= inner_radius:
        raise ValueError("outer_radius must be larger than inner_radius")

    outer = gdstk.ellipse((0.0, 0.0), outer_radius, layer=layer, datatype=datatype)
    inner = gdstk.ellipse((0.0, 0.0), inner_radius, layer=layer, datatype=datatype)
    ring_polygons = gdstk.boolean([outer], [inner], "not", precision=tolerance, layer=layer, datatype=datatype)

    cell = gdstk.Cell(name)
    cell.add(*ring_polygons)
    return cell


def make_alignment_marker_cell(
    name: str,
    arm_length: float,
    arm_width: float,
    *,
    layer: int = MARKER_LAYER.layer,
    datatype: int = MARKER_LAYER.datatype,
) -> gdstk.Cell:
    """Create a simple cross-shaped alignment marker."""

    if arm_length <= 0 or arm_width <= 0:
        raise ValueError("arm_length and arm_width must be positive")

    cell = gdstk.Cell(name)
    half_len = arm_length / 2.0
    half_w = arm_width / 2.0
    horizontal = gdstk.rectangle((-half_len, -half_w), (half_len, half_w), layer=layer, datatype=datatype)
    vertical = gdstk.rectangle((-half_w, -half_len), (half_w, half_len), layer=layer, datatype=datatype)
    cell.add(horizontal, vertical)
    return cell


def make_label_cell(
    name: str,
    text: str,
    size: float,
    *,
    layer: int = TEXT_LAYER.layer,
    datatype: int = TEXT_LAYER.datatype,
) -> gdstk.Cell:
    """Create a label cell using polygonized text so it is visible in previews."""

    if size <= 0:
        raise ValueError("size must be positive")

    cell = gdstk.Cell(name)
    text_polygons = gdstk.text(text, size, (0.0, 0.0), layer=layer, datatype=datatype)
    cell.add(*text_polygons)
    return cell

