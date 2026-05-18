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
- 可生成 PNG 预览图
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

## 运行测试

```powershell
pytest
```

## 项目结构

- `src/gds_layout_kit/primitives.py`：基础图元
- `src/gds_layout_kit/assembly.py`：顶层组合
- `src/gds_layout_kit/io.py`：GDS 读写与信息提取
- `src/gds_layout_kit/preview.py`：PNG 预览
- `src/gds_layout_kit/demo.py`：示例入口
- `tests/`：基础测试

## 后续扩展建议

后续添加新的参数化版图元素时，建议保持以下分层：

- `primitives` 只负责单个几何元素
- `assembly` 只负责组合与摆放
- `io` 只负责读写和检查
- `preview` 只负责展示

这样可以很自然地继续扩展成参数化版图生成工具。

