# CLI 参考

所有输出路径均为项目根目录下 `outputs/` 子目录（不受 CWD 影响）。

## `gds-layout-demo`

无参数。生成基础版图 demo。

```
输出: outputs/demo_layout.gds + demo_layout.png
```

```bash
gds-layout-demo
```

---

## `gds-layout-gradient`

梯度超表面生成。

```bash
gds-layout-gradient [选项]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--layout-width-um` | float | 10.0 | 目标布局宽度 (um) |
| `--layout-height-um` | float | 10.0 | 目标布局高度 (um) |
| `--rows` | int | — | 行数（覆盖自动推算） |
| `--cols` | int | — | 列数（覆盖自动推算） |
| `--pitch-min-um` | float | 0.42 | 最小周期 (um) |
| `--pitch-max-um` | float | 0.93 | 最大周期 (um) |
| `--fill-min` | float | 0.54 | 最小填充率 |
| `--fill-max` | float | 0.62 | 最大填充率 |
| `--tri-factor` | float | 0.05 | 三角形变形因子 |
| `--output-dir` | path | outputs/gradient_metasurface | 输出目录 |
| `--no-center-aligned` | flag | off | 使用直角梯形（默认等腰） |
| `--preview-crop-fraction` | float | 0.1 | 预览中心裁剪比例 |
| `--preview-pixels-per-unit` | float | 12.0 | 每微米像素数 |
| `--preview-max-total-pixels` | int | 4000000 | 预览总像素上限 |

输出: `gradient_metasurface.gds` + `.png` + `_grid.gds`（如果 grid 开启）。

### 示例

```bash
# 100um 方形布局
gds-layout-gradient --layout-width-um 100 --layout-height-um 100

# 指定行列 + 直角梯形
gds-layout-gradient --rows 200 --cols 300 --no-center-aligned

# 高分辨率预览
gds-layout-gradient --preview-pixels-per-unit 64 --preview-crop-fraction 0.5
```

---

## `gds-layout-grating`

光栅梯度生成。

```bash
gds-layout-grating [选项]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--layout-width-um` | float | 2000.0 | 目标布局宽度 (um) |
| `--layout-height-um` | float | 400.0 | 目标布局高度 (um) |
| `--rows` | int | — | 行数（覆盖自动推算） |
| `--cols` | int | — | 列数（覆盖自动推算） |
| `--pitch-min-um` | float | 0.4 | 最小周期 (um)，左侧 |
| `--pitch-max-um` | float | 0.7 | 最大周期 (um)，右侧 |
| `--dc-min` | float | 0.3 | 最小占空比，底部 |
| `--dc-max` | float | 0.7 | 最大占空比，顶部 |
| `--tone` | str | positive | 正胶 `positive` / 负胶 `negative` |
| `--output-dir` | path | outputs/grating_gradient | 输出目录 |
| `--no-rectangular` | flag | off | 启用梯形包络（默认矩形） |
| `--no-center-aligned` | flag | off | 直角梯形（需配合 `--no-rectangular`） |
| `--show-grid` | flag | off | 显示网格参考线 |
| `--preview-crop-fraction` | float | 0.1 | 预览中心裁剪比例 |
| `--preview-pixels-per-unit` | float | 128.0 | 每微米像素数 |
| `--preview-max-total-pixels` | int | 4000000 | 预览总像素上限 |
| `--preview-edgecolor` | str | none | 多边形边框颜色 (`none`=无边框) |

输出: `grating_gradient.gds` + `.png` + `_grid.gds`（`--show-grid` 时）。

### 示例

```bash
# 默认矩形正胶
gds-layout-grating

# 负胶 + 梯形包络 + 网格线
gds-layout-grating --tone negative --no-rectangular --show-grid

# 自定义 DC 和周期范围
gds-layout-grating --dc-min 0.4 --dc-max 0.6 --pitch-min-um 0.5 --pitch-max-um 0.6

# 高精度渲染
gds-layout-grating --preview-pixels-per-unit 256 --preview-crop-fraction 0.05
```
