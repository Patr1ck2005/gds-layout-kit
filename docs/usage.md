# Python API 使用指南

## 基础图元

所有图元函数返回 `gdstk.Cell`。每个 cell 包含一个几何图形，可以通过 `gdstk.Reference` 被其他 cell 引用。

```python
from gds_layout_kit import (
    make_pad_cell,
    make_metal_block_cell,
    make_ring_cell,
    make_alignment_marker_cell,
    make_label_cell,
)

# 矩形 pad，默认层 (1, 0)
pad = make_pad_cell("PAD", width=120.0, height=80.0)

# 金属块（make_pad_cell 的别名）
metal = make_metal_block_cell("METAL", width=90.0, height=50.0)

# 环形（通过布尔减法生成）
ring = make_ring_cell("RING", outer_radius=35.0, inner_radius=22.0)

# 十字对准标记
marker = make_alignment_marker_cell("MARKER", arm_length=70.0, arm_width=8.0)

# 文字标签（多边形化文本）
label = make_label_cell("LABEL", text="GDS Layout Kit", size=12.0)
```

所有函数的默认层为：
- pad/metal: `(1, 0)`
- ring: `(2, 0)`
- marker: `(3, 0)`
- label: `(4, 0)`

可通过 `layer=` 和 `datatype=` 参数覆盖。

## 版图组装

```python
from gds_layout_kit import build_demo_layout

library, cells = build_demo_layout()
# cells: DemoLayoutCells(pad, metal, ring, marker, label, top)
# cells.top 是包含所有子 cell 引用的顶层 cell
```

`build_demo_layout` 创建预定义的 demo 布局。实际使用时建议参考其实现，自行创建 `gdstk.Library` 和 `gdstk.Cell`，通过 `gdstk.Reference` 组合子 cell。

## 梯度超表面

超表面系统生成梯形包络的渐变阵列，meta-atom 为 tri-factor 变形的圆形。

```python
from gds_layout_kit import (
    TrapezoidalGradientMetasurfaceSpec,
    build_trapezoidal_gradient_metasurface_layout,
    save_trapezoidal_gradient_layout_files,
)

spec = TrapezoidalGradientMetasurfaceSpec(
    rows=160, cols=220,
    pitch_min_um=0.84,    # 左侧最小周期 (um)
    pitch_max_um=0.93,    # 右侧最大周期 (um)
    fill_min=0.54,        # 底部最小填充率
    fill_max=0.62,        # 顶部最大填充率
    tri_factor=0.05,      # 三角形变形因子 (0=正圆)
    center_aligned=True,  # 等腰梯形 (False=直角梯形)
)

result = build_trapezoidal_gradient_metasurface_layout(spec)

save_trapezoidal_gradient_layout_files(
    result,
    "outputs/metasurface.gds",
    "outputs/metasurface.png",
    preview_crop_fraction=0.2,
    preview_pixels_per_unit=12.0,
)
```

### 参数说明

| 参数 | 含义 |
|------|------|
| `rows`, `cols` | 阵列行列数 |
| `pitch_min_um`, `pitch_max_um` | X 方向周期范围，从左到右 |
| `fill_min`, `fill_max` | Y 方向填充率范围，从下到上 |
| `tri_factor` | 三角形变形强度；0 为正圆，值越大越接近三角形 |
| `center_aligned` | True=等腰梯形，False=直角梯形（底部对齐） |

## 光栅梯度

光栅系统生成梯形竖直线阵列。周期沿 X 渐变，占空比 (DC) 沿 Y 渐变，每根线条是光滑的梯形。默认生成矩形阵列（无梯形包络）。

```python
from gds_layout_kit import (
    GratingGradientSpec,
    build_grating_gradient_layout,
    save_grating_gradient_layout_files,
)

spec = GratingGradientSpec(
    rows=400, cols=720,
    pitch_min_um=0.5,      # 500nm, 左侧周期
    pitch_max_um=0.6,      # 600nm, 右侧周期
    dc_min=0.4,            # 底部占空比
    dc_max=0.6,            # 顶部占空比
    tone="positive",       # 正胶 (线条=实心)
    rectangular=True,      # 矩形阵列 (默认)
)

result = build_grating_gradient_layout(spec)

save_grating_gradient_layout_files(
    result,
    "outputs/grating.gds",
    "outputs/grating.png",
    preview_edgecolor="none",  # 无边框
)
```

### 矩形模式 vs 梯形模式

```python
# 矩形阵列（默认）：周期和 DC 直接线性插值，无坐标变换
spec_rect = GratingGradientSpec(rectangular=True)

# 梯形模式：应用 TrapezoidalGradientTransform
spec_trap = GratingGradientSpec(rectangular=False, center_aligned=True)
```

光栅不需要梯形边界（线条是连续的），所以默认 `rectangular=True`。

### 正胶 / 负胶

```python
# 正胶：线条为实心多边形
pos = GratingGradientSpec(tone="positive")

# 负胶：从背景矩形中减去线条，图案反转
neg = GratingGradientSpec(tone="negative")
```

负胶通过 `gdstk.boolean(background, gratings, "not")` 实现。

### 参数说明

| 参数 | 含义 |
|------|------|
| `rows`, `cols` | 阵列行列数 |
| `pitch_min_um`, `pitch_max_um` | X 方向周期范围，从左到右 |
| `dc_min`, `dc_max` | Y 方向占空比范围，从下到上；DC = 线宽 / 周期 |
| `rectangular` | True=矩形阵列，False=梯形包络 |
| `center_aligned` | 仅 `rectangular=False` 时生效 |
| `tone` | `"positive"` 正胶 / `"negative"` 负胶 |

## 坐标变换

`TrapezoidalGradientTransform` 可以独立使用，将均匀网格映射到梯形渐变网格。

```python
from gds_layout_kit import TrapezoidalGradientTransform, apply_transform_to_polygons

transform = TrapezoidalGradientTransform(
    pitch_min_um=0.5,
    pitch_max_um=0.6,
    base_period_um=0.5,
    num_cols=100,
    num_rows=80,
    center_aligned=True,
)

# 变换单个点
x_prime, y_prime = transform.transform_point(10.0, 5.0)

# 变换多边形列表
transformed = apply_transform_to_polygons(my_polygons, transform)
```

## I/O 与预览

```python
from gds_layout_kit import write_gds, load_gds, top_cell_summary, save_cell_preview

# 写入 GDS
gds_path = write_gds(library, "outputs/layout.gds")

# 读回并检查
loaded = load_gds(gds_path)
for item in top_cell_summary(loaded):
    print(f"{item['name']}: bbox={item['bbox']}, polygons={item['polygon_count']}")

# 生成 PNG 预览
png_path = save_cell_preview(
    top_cell,
    "outputs/preview.png",
    crop_fraction=0.2,          # 只渲染中心 20% 区域
    pixels_per_unit=32.0,       # 每微米像素数
    max_total_pixels=4_000_000, # 总像素上限
    edgecolor="none",           # 多边形边框颜色 ("none"=无边框)
)
```
