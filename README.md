# GDS Layout Kit

纯 Python GDS 版图生成工具包，基于 `gdstk` + `matplotlib` + `pytest`。

## 特性

- **基础版图元素**：矩形 pad、环形 ring、十字 marker、文字 label
- **梯度超表面**：周期渐变 + 填充率渐变 + 梯形包络，tri-factor 变形圆形 meta-atom
- **光栅梯度**：周期沿 X 渐变（500-600nm）+ 占空比 DC 沿 Y 渐变（0.4-0.6），线条自然呈梯形，支持正胶/负胶颠倒映射
- **坐标变换框架**：可复用的 `TrapezoidalGradientTransform`，统一网格 → 连续变换两阶段流水线
- **GDS 精度 0.01nm**：全局 `library_precision=1e-11`，确保纳米级渐变连续可分辨
- **PNG 预览**：matplotlib 渲染，支持中心裁剪和自适应分辨率
- **零 GUI 依赖**：不依赖 KLayout 或其他图形界面

## 安装

```bash
pip install -e ".[test]"
```

## 快速开始

### 基础版图

```bash
gds-layout-demo
# → outputs/demo_layout.gds + demo_layout.png
```

### 梯度超表面

```bash
gds-layout-gradient --layout-width-um 100 --layout-height-um 100
# → outputs/gradient_metasurface/gradient_metasurface.gds + .png
```

### 光栅梯度

```bash
# 矩形模式（默认）
gds-layout-grating

# 负胶 + 梯形包络
gds-layout-grating --tone negative --no-rectangular
# → outputs/grating_gradient/grating_gradient.gds + .png
```

也可从 `examples/` 直接运行：

```bash
python examples/demo.py
python examples/gradient_metasurface.py
python examples/grating_gradient.py
```

## Python API 示例

```python
from gds_layout_kit import GratingGradientSpec, build_grating_gradient_layout

spec = GratingGradientSpec(
    rows=400, cols=720,
    pitch_min_um=0.5, pitch_max_um=0.6,  # 500-600nm
    dc_min=0.4, dc_max=0.6,
    tone="positive",
)
result = build_grating_gradient_layout(spec)
```

详细用法见 [使用指南](docs/usage.md)，完整 API 见 [API 参考](docs/api.md)，CLI 参数见 [CLI 参考](docs/cli.md)。

## 项目结构

```
gds-layout-kit/
├── src/gds_layout_kit/
│   ├── primitives.py      # 基础图元 (pad, ring, marker, label)
│   ├── assembly.py        # 顶层组装
│   ├── io.py              # GDS 读写
│   ├── preview.py         # PNG 预览
│   ├── transform.py       # 坐标变换框架
│   ├── metasurface.py     # 梯度超表面构建器
│   ├── grating.py         # 光栅梯度构建器
│   ├── demo.py            # 基础 demo 入口
│   ├── gradient_demo.py   # 超表面 demo 入口
│   └── grating_demo.py    # 光栅 demo 入口
├── tests/
│   ├── test_primitives.py
│   ├── test_roundtrip.py
│   ├── test_transform.py
│   ├── test_metasurface.py
│   └── test_grating.py
├── examples/
│   ├── demo.py
│   ├── gradient_metasurface.py
│   └── grating_gradient.py
├── docs/
│   ├── usage.md           # Python API 使用指南
│   ├── api.md             # API 参考
│   └── cli.md             # CLI 参考
├── outputs/               # 生成文件 (.gds, .png)
└── pyproject.toml
```

## 运行测试

```bash
pytest
```
