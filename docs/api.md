# API 参考

## primitives.py

### `LayerSpec`
```python
@dataclass(frozen=True)
class LayerSpec:
    layer: int
    datatype: int
```
预定义常量：`PAD_LAYER=(1,0)`, `RING_LAYER=(2,0)`, `MARKER_LAYER=(3,0)`, `TEXT_LAYER=(4,0)`。

### `make_pad_cell`
```python
def make_pad_cell(
    name: str,
    width: float,
    height: float,
    *,
    layer: int = 1,
    datatype: int = 0,
) -> gdstk.Cell
```
创建居中的矩形 pad。`make_metal_block_cell` 是其别名。

### `make_ring_cell`
```python
def make_ring_cell(
    name: str,
    outer_radius: float,
    inner_radius: float,
    *,
    layer: int = 2,
    datatype: int = 0,
    tolerance: float = 1e-11,
) -> gdstk.Cell
```
通过 `gdstk.boolean` 外圆减去内圆生成环形。`inner_radius` 必须小于 `outer_radius`，否则抛出 `ValueError`。

### `make_alignment_marker_cell`
```python
def make_alignment_marker_cell(
    name: str,
    arm_length: float,
    arm_width: float,
    *,
    layer: int = 3,
    datatype: int = 0,
) -> gdstk.Cell
```
十字对准标记（两个正交矩形）。

### `make_label_cell`
```python
def make_label_cell(
    name: str,
    text: str,
    size: float,
    *,
    layer: int = 4,
    datatype: int = 0,
) -> gdstk.Cell
```
多边形化文字标签。

---

## assembly.py

### `DemoLayoutCells`
```python
@dataclass(frozen=True)
class DemoLayoutCells:
    pad: gdstk.Cell
    metal: gdstk.Cell
    ring: gdstk.Cell
    marker: gdstk.Cell
    label: gdstk.Cell
    top: gdstk.Cell
```

### `build_demo_layout`
```python
def build_demo_layout() -> tuple[gdstk.Library, DemoLayoutCells]
```
构建预定义的 demo 版图库。GDS 精度 1e-11 (0.01 nm)。

---

## io.py

### `write_gds`
```python
def write_gds(library: gdstk.Library, path: str | Path) -> Path
```
写入 GDS 文件，自动创建父目录。返回解析后的绝对路径。

### `load_gds`
```python
def load_gds(path: str | Path) -> gdstk.Library
```
从磁盘读取 GDS 文件。

### `top_cell_summary`
```python
def top_cell_summary(library: gdstk.Library) -> list[dict[str, object]]
```
返回顶层 cell 摘要列表，每项包含 `name`, `bbox`, `reference_count`, `polygon_count`。

---

## preview.py

### `save_cell_preview`
```python
def save_cell_preview(
    cell: gdstk.Cell,
    path: str | Path,
    *,
    crop_fraction: float = 0.2,
    pixels_per_unit: float = 12.0,
    max_total_pixels: int = 4_000_000,
    dpi: int = 100,
    facecolor: str = "white",
    edgecolor: str = "black",
) -> Path
```
渲染 cell 的 PNG 预览。只渲染 `crop_fraction` 比例的中心区域。自动缩放使总像素不超过 `max_total_pixels`。

---

## transform.py

### `CoordinateTransform`
```python
class CoordinateTransform(Protocol):
    def transform_point(self, x: float, y: float) -> tuple[float, float]: ...
```
坐标变换协议。任何实现 `transform_point` 的类都可传给 `apply_transform_to_polygons`。

### `TrapezoidalGradientTransform`
```python
@dataclass(frozen=True)
class TrapezoidalGradientTransform:
    pitch_min_um: float
    pitch_max_um: float
    base_period_um: float
    num_cols: int
    num_rows: int
    center_aligned: bool = True
```
光滑非线性坐标变换。将均匀矩形网格映射为梯形渐变网格。

- `transform_point(x, y) -> (x', y')` — X 方向二次扭曲，Y 方向随 X 缩放
- 验证：`pitch_max >= pitch_min > 0`, `num_cols >= 2`, `num_rows >= 2`

### `apply_transform_to_polygons`
```python
def apply_transform_to_polygons(
    polygons: list[list[tuple[float, float]]],
    transform: CoordinateTransform,
) -> list[list[tuple[float, float]]]
```
对多边形列表中每个顶点应用变换，返回新列表。不修改输入。

### `compute_trapezoid_extents`
```python
def compute_trapezoid_extents(
    *,
    pitch_min_um: float,
    pitch_max_um: float,
    num_cols: int,
    num_rows: int,
    center_aligned: bool = True,
) -> tuple[float, float]
```
返回梯形布局的解析边界 `(x_extent_um, y_extent_um)`。

---

## metasurface.py

### `GradientMetasurfaceSpecBase`
```python
@dataclass(frozen=True)
class GradientMetasurfaceSpecBase:
    rows: int = 160
    cols: int = 220
    outline_points: int = 240
    top_name: str = "GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-11
    layer: int = 11
    datatype: int = 0
    show_grid: bool = True
    grid_layer: int = 12
    grid_datatype: int = 0
    grid_line_width_um: float = 0.01
```

### `TrapezoidalGradientMetasurfaceSpec`
```python
@dataclass(frozen=True)
class TrapezoidalGradientMetasurfaceSpec(GradientMetasurfaceSpecBase):
    pitch_min_um: float = 0.84
    pitch_max_um: float = 0.93
    fill_min: float = 0.54
    fill_max: float = 0.62
    tri_factor: float = 0.05
    center_aligned: bool = True
```
`GradientMetasurfaceSpec` 是其向后兼容别名。

### `GradientMetasurfaceResult`
```python
@dataclass(frozen=True)
class GradientMetasurfaceResult:
    library: gdstk.Library
    top_cell: gdstk.Cell
    row_pitch_um: float
    x_extent_um: float
    y_extent_um: float
    show_grid: bool = False
    grid_layer: int = 12
    grid_datatype: int = 0
```

### `build_trapezoidal_gradient_metasurface_layout`
```python
def build_trapezoidal_gradient_metasurface_layout(
    spec: TrapezoidalGradientMetasurfaceSpec,
) -> GradientMetasurfaceResult
```
两阶段构建：均匀网格生成 → 梯形变换。`build_gradient_metasurface_layout` 是兼容别名。

### `save_trapezoidal_gradient_layout_files`
```python
def save_trapezoidal_gradient_layout_files(
    result: GradientMetasurfaceResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> tuple[Path, Path, Path | None]
```
写 GDS + PNG。若 `result.show_grid=True` 还写独立 grid GDS。`save_gradient_layout_files` 是兼容别名。

---

## grating.py

### `GratingGradientSpec`
```python
@dataclass(frozen=True)
class GratingGradientSpec:
    rows: int = 160
    cols: int = 220
    pitch_min_um: float = 0.5
    pitch_max_um: float = 0.6
    dc_min: float = 0.4
    dc_max: float = 0.6
    rectangular: bool = True
    center_aligned: bool = True
    tone: str = "positive"
    top_name: str = "GRATING_GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-11
    layer: int = 11
    datatype: int = 0
    show_grid: bool = False
    grid_layer: int = 12
    grid_datatype: int = 0
    grid_line_width_um: float = 0.01
```

### `GratingGradientResult`
```python
@dataclass(frozen=True)
class GratingGradientResult:
    library: gdstk.Library
    top_cell: gdstk.Cell
    x_extent_um: float
    y_extent_um: float
    show_grid: bool = False
    grid_layer: int = 12
    grid_datatype: int = 0
```

### `build_grating_gradient_layout`
```python
def build_grating_gradient_layout(
    spec: GratingGradientSpec,
) -> GratingGradientResult
```
构建光栅梯度布局。`rectangular=True` 时直接生成变周期变 DC 的梯形线条；`rectangular=False` 时走均匀网格→梯形变换管线。`tone="negative"` 时用 `gdstk.boolean` 做图案反转。

### `save_grating_gradient_layout_files`
```python
def save_grating_gradient_layout_files(
    result: GratingGradientResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
    preview_edgecolor: str = "none",
) -> tuple[Path, Path, Path | None]
```
写 GDS + PNG。预览默认无多边形边框。若 `result.show_grid=True` 还写独立 grid GDS。

## grating_demo.py

### `run_grating_demo`
```python
def run_grating_demo(
    *,
    layout_width_um: float = 2000.0,
    layout_height_um: float = 400.0,
    rows: int | None = None,
    cols: int | None = None,
    pitch_min_um: float = 0.4,
    pitch_max_um: float = 0.7,
    dc_min: float = 0.3,
    dc_max: float = 0.7,
    tone: str = "positive",
    output_dir: Path = ...,
    rectangular: bool = True,
    center_aligned: bool = True,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 128.0,
    preview_max_total_pixels: int = 4_000_000,
    preview_edgecolor: str = "none",
    show_grid: bool = False,
) -> GratingDemoResult
```

### `GratingDemoResult`
```python
@dataclass(frozen=True)
class GratingDemoResult:
    spec: GratingGradientSpec
    x_extent_um: float
    y_extent_um: float
    gds_path: Path
    png_path: Path
    grid_gds_path: Path | None
    summary: list[dict[str, object]]
```

## gradient_demo.py

### `run_gradient_demo`
```python
def run_gradient_demo(
    *,
    layout_width_um: float = 1000.0,
    layout_height_um: float = 1000.0,
    rows: int | None = None,
    cols: int | None = None,
    pitch_min_um: float = 0.84,
    pitch_max_um: float = 0.93,
    fill_min: float = 0.54,
    fill_max: float = 0.62,
    tri_factor: float = 0.05,
    output_dir: Path = ...,
    center_aligned: bool = True,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> GradientDemoResult
```
