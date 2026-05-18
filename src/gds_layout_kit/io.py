"""I/O helpers for GDS read/write and summary information."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import gdstk


def write_gds(library: gdstk.Library, path: str | Path) -> Path:
    """Write a GDS library to disk and return the resolved path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    library.write_gds(str(output))
    return output


def load_gds(path: str | Path) -> gdstk.Library:
    """Load a GDS file from disk."""

    return gdstk.read_gds(str(path))


def top_cell_summary(library: gdstk.Library) -> list[dict[str, object]]:
    """Return a small summary for all top-level cells in the library."""

    summary: list[dict[str, object]] = []
    for cell in library.top_level():
        summary.append(
            {
                "name": cell.name,
                "bbox": cell.bounding_box(),
                "reference_count": len(cell.references),
                "polygon_count": len(cell.polygons),
            }
        )
    return summary

