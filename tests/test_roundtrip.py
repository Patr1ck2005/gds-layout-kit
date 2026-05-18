from __future__ import annotations

from pathlib import Path

from gds_layout_kit.assembly import build_demo_layout
from gds_layout_kit.io import load_gds, top_cell_summary, write_gds
from gds_layout_kit.preview import save_cell_preview


def test_demo_library_roundtrip(tmp_path: Path) -> None:
    library, cells = build_demo_layout()

    gds_path = tmp_path / "demo.gds"
    png_path = tmp_path / "demo.png"

    write_gds(library, gds_path)
    save_cell_preview(cells.top, png_path)

    assert gds_path.exists()
    assert png_path.exists()

    loaded = load_gds(gds_path)
    summary = top_cell_summary(loaded)

    assert summary
    assert any(item["name"] == "TOP" for item in summary)
    top_items = [item for item in summary if item["name"] == "TOP"]
    assert len(top_items) == 1
    bbox = top_items[0]["bbox"]
    assert bbox is not None
    (xmin, ymin), (xmax, ymax) = bbox
    assert xmax > xmin
    assert ymax > ymin

    names = {cell.name for cell in loaded.cells}
    for expected in {"PAD", "METAL", "RING", "MARKER", "LABEL", "TOP"}:
        assert expected in names

