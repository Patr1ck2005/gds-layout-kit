# GDS Layout Kit

一个最小可运行的纯 Python GDS 版图生成项目，基于 `gdstk` 生成 `.gds`，基于 `matplotlib` 生成 `.png` 预览，使用 `pytest` 做基础测试。

## 特性

- 纯 Python 版图生成，不依赖 KLayout 或 GUI 工具
- 支持基础版图元素：
  - 矩形 pad / metal block
  - 通过布尔运算生成的 ring
  - 十字 alignment marker
  - 文字 label
  - 顶层 cell reference 组合
- 可读回 GDS 并打印基本信息
- 可生成 PNG 预览图，默认仅显示版图中心局部区域
- 采用 `src` layout，便于后续扩展

## 安装

建议使用虚拟环境，然后安装为可编辑模式：

```powershell
python -m pip install -e .[test]
```

如果你的环境里已经有依赖，也可以直接运行示例和测试。

## 运行示例

示例脚本会在 `outputs/` 目录下生成：

- `demo_layout.gds`
- `demo_layout.png`

运行方式：

```powershell
python -m gds_layout_kit.demo
```

或者：

```powershell
gds-layout-demo
```

示例脚本会：

1. 构建一个示例版图库
2. 写出 GDS 文件
3. 生成 PNG 预览图
4. 读回 GDS 文件
5. 打印 top cell 名称和 bounding box

### 梯度超表面示例

当前梯度超表面示例位于 `examples/gradient_metasurface.py`，默认参数面向约 `1 mm × 1 mm` 的布局尺寸，并且只输出中心区域的 PNG 预览，不裁剪 GDS 文件本身。

运行方式：

```powershell
python .\examples\gradient_metasurface.py
```

或者安装后直接运行：

```powershell
gds-layout-gradient
```

你也可以显式传入参数，例如：

```powershell
python .\examples\gradient_metasurface.py --layout-width-um 1000 --layout-height-um 1000 --preview-pixels-per-unit 20 --preview-max-total-pixels 4000000
```

预览图会根据：

- `--preview-crop-fraction`：只截取中心区域的比例
- `--preview-pixels-per-unit`：每个微米分配多少像素
- `--preview-max-total-pixels`：图片总像素上限

自动计算输出 PNG 的尺度与分辨率。

## 运行测试

```powershell
pytest
```

## 项目结构

- `src/gds_layout_kit/primitives.py`：基础图元
- `src/gds_layout_kit/assembly.py`：顶层组合
- `src/gds_layout_kit/io.py`：GDS 读写与信息提取
- `src/gds_layout_kit/preview.py`：PNG 预览（中心裁剪 + 自动缩放）
- `src/gds_layout_kit/metasurface.py`：梯度超表面专用构建器
- `src/gds_layout_kit/gradient_demo.py`：梯度超表面示例入口
- `tests/`：基础测试

## 后续扩展建议

后续添加新的参数化版图元素时，建议保持以下分层：

- `primitives` 只负责单个几何元素
- `assembly` 只负责组合与摆放
- `io` 只负责读写和检查
- `preview` 只负责展示

这样可以很自然地继续扩展成参数化版图生成工具。

