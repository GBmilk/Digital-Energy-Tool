# 数字能量工具

一款基于 **Python 3.12.3 + PyQt5 + qfluentwidgets** 的 Windows 桌面软件。
输入数字或英文字母，按数字能量对应表分析相邻两位数组合，识别四吉星与四凶星，
计算能量等级、综合评分，支持历史记录、详情图与 CSV 导出。

---

## 一、功能特性

- **数字分析**：输入数字 `0-9` 或英文字母 `A-Z / a-z`（不区分大小写），自动将字母转换为数字（A=1 … Z=26），逐个分析相邻两位数组合。
- **能量匹配**：四吉星（天医、延年、生气、伏位）与四凶星（绝命、祸害、五鬼、六煞），每星四个等级（一级～四级），共 64 条映射。
- **六级评价**：很好 / 好 / 一般 / 不好 / 凶 / 暂无评定；评分规则与评级区间在配置文件中可调整（设置界面保持精简，不暴露规则编辑）。
- **特殊规则**：含数字 5 的组合、未匹配组合均显示"暂无评定"，不参与评分；仅在无有效组合时才显示"暂无评定 --"，绝不误显示 0 分。
- **历史记录**：SQLite 本地持久化，保存每次计算的完整 JSON 快照，支持搜索、排序、查看详情、重新分析、删除与 CSV 导出。
- **详情图**：Pillow 生成高清 PNG，支持 720P / 1080P / 2K / 4K / 8K 五档清晰度，所有字体与布局按分辨率等比缩放，固定 600 DPI 保存；自动检测 Windows 中文字体，卡片布局，吉绿凶红未评定灰。
- **CSV 导出**：UTF-8-SIG 编码（Excel 打开中文不乱码），可导出当前分析、全部历史与筛选结果。
- **界面**：Windows 11 Fluent Design 风格，左侧导航栏顺序为"数字分析 → 数字能量表 → 历史记录 → 设置 → 关于"，支持浅色/深色/跟随系统主题、高 DPI 与窗口缩放；全局基础字体为微软雅黑 M 号（14px），「数字能量综合评价」与「数字组合分析」区域使用新宋体。
- **健壮性**：输入实时校验、非法字符过滤、数据库损坏自动重建、配置缺失/损坏自动恢复、路径兼容中文、统一日志与异常处理。

---

## 二、目录结构

```text
数字能量工具/
├── main.py                     # 程序入口
├── requirements.txt            # 依赖清单
├── README.md                   # 本文档
├── config/
│   ├── config.json             # 默认配置（评分规则、评级区间、路径等）
│   └── qfluent_config.json     # qfluentwidgets 独立配置（字体/主题，避免冲突）
├── core/
│   ├── energy_mapping.py       # 数字能量映射规则（唯一数据源）
│   ├── alphabet_converter.py   # 字母转数字
│   ├── energy_analyzer.py      # 组合拆分与匹配分析引擎
│   ├── score_engine.py         # 综合评分与评级
│   ├── csv_exporter.py         # CSV 导出
│   ├── image_generator.py      # 详情图生成
│   ├── app_icon.py             # 软件图标生成（Pillow / SVG）
│   └── utils.py                # 路径、配置、日志工具
├── database/
│   ├── database_manager.py     # SQLite 连接与初始化
│   └── history_repository.py   # 历史记录数据仓库
├── ui/
│   ├── main_window.py          # FluentWindow 主窗口
│   ├── analysis_page.py        # 数字分析页
│   ├── history_page.py         # 历史记录页
│   ├── detail_page.py          # 历史详情对话框
│   ├── mapping_page.py         # 数字能量表页
│   ├── settings_page.py        # 设置页
│   ├── about_page.py           # 关于页（独立导航项）
│   └── widgets/                # 评分卡、输入信息卡、组合卡、主题感知滚动区
├── resources/
│   └── icons/                  # app_icon.png / app_icon.ico / app_icon.svg
├── data/                       # 运行生成：history.db、app.log
├── exports/                    # 默认导出目录（CSV / 详情图）
└── tests/                      # 单元测试与 GUI 检查脚本
```

---

## 三、运行环境与安装

1. **Python 3.12.3**（推荐，Python 3.8+ 亦可运行）
2. 安装依赖：

```powershell
python -m pip install -r requirements.txt
```

依赖列表：

```text
PyQt5>=5.15.0
PyQt-Fluent-Widgets>=1.11.0   # 导入名 qfluentwidgets
Pillow>=10.0.0
matplotlib>=3.7.0             # 可选，用于扩展可视化
```

> 注意：qfluentwidgets 的 **PyPI 包名是 `PyQt-Fluent-Widgets`**，导入名是 `qfluentwidgets`。

---

## 四、启动方式

在命令行中进入项目目录并启动：

```powershell
cd /d 项目目录
python main.py
```

首次启动会自动创建：`config/config.json`（若缺失）、`data/history.db` 与各目录。

---

## 五、使用说明

### 1. 数字分析

- 在输入框输入数字或英文字母；非法字符（中文、空格、符号等）会被实时过滤。
- 点击 **计算** 或按 **回车** 执行分析；**清空** 按钮重置输入。
- 页面从上到下依次显示：综合评分卡（分数、评级、进度条、统计）、输入信息卡、数字组合分析卡片列表。
- 吉星卡片为绿色系、凶星为红色系、未评定为灰色系；等级越高视觉强调越强。
- **生成详情图**：先选择清晰度（720P / 1080P / 2K / 4K / 8K），再选择保存位置，导出高清 PNG。
- **导出当前分析 CSV**：选择保存位置，导出含完整字段的 CSV。

### 2. 历史记录

- 每次计算自动保存当时的完整分析结果（JSON 快照，不重新计算、不覆盖）。
- 支持按输入内容/数字/评级搜索、按日期或分数排序、查看详情、重新分析、删除单条/全部。
- 双击表格行可直接查看详细结果。
- 支持"导出全部历史记录"与"导出筛选后的记录"为 CSV。

### 3. 数字能量表

展示完整四吉星与四凶星的全部映射，每个星含数字组合、等级、属性、颜色与简要说明。
数据直接读取核心模块，与分析引擎完全一致。

### 4. 设置

- 外观主题：浅色 / 深色 / 跟随系统。
- 存储与导出位置：历史数据库、默认导出目录、详情图默认保存目录。
- 数据管理：清除历史记录、恢复默认设置。
- 配置同时保存到 `config/config.json` 与 SQLite 数据库。

### 5. 关于

独立导航页面，展示软件图标、软件名称、版本号、技术栈与简短简介。

---

## 六、软件图标设计

图标设计规范：**粉紫渐变背景（斜向 35°）+ 居中大写字母 E + Apple 风格 squircle 连续圆角**。
生成代码位于 [`core/app_icon.py`](core/app_icon.py)，提供 `generate_svg()`（矢量源码）与 Pillow 版 PNG/ICO 生成，产物在 `resources/icons/`。

### SVG 核心代码（等价于生成文件 `resources/icons/app_icon.svg`）

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <!-- 斜向粉紫渐变 -->
    <linearGradient id="pinkPurple" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF8FB2"/>
      <stop offset="50%" stop-color="#C17EEB"/>
      <stop offset="100%" stop-color="#7E76E2"/>
    </linearGradient>
    <!-- Apple squircle 圆角路径（三次贝塞尔近似超椭圆） -->
    <clipPath id="squircle">
      <path d="M 56 292 C 56 56 56 56 292 56 L 732 56 C 968 56 968 56 968 292
               L 968 732 C 968 968 968 968 732 968 L 292 968
               C 56 968 56 968 56 732 Z"/>
    </clipPath>
  </defs>
  <g clip-path="url(#squircle)">
    <rect width="1024" height="1024" fill="url(#pinkPurple)"/>
    <ellipse cx="358" cy="225" rx="563" ry="430" fill="#fff" opacity="0.10"/>
    <text x="50%" y="50%" dy="0.35em" text-anchor="middle"
          font-family="Segoe UI Bold, Microsoft YaHei, Arial Bold, sans-serif"
          font-weight="700" font-size="635" fill="#fff">E</text>
  </g>
</svg>
```

等价 CSS（网页中使用时）：

```css
.app-icon {
  width: 128px; height: 128px;
  border-radius: 26%;                 /* 近似 squircle 的连续圆角 */
  background: linear-gradient(135deg, #FF8FB2 0%, #C17EEB 50%, #7E76E2 100%);
  display: grid; place-items: center;
  color: #fff; font: 700 72px "Microsoft YaHei", "Segoe UI", sans-serif;
}
```

### Pillow 生成与应用方式

```bash
python core/app_icon.py          # 生成 resources/icons/app_icon.png/.ico/.svg
```

```python
# main.py 中已在启动时自动应用图标：
from core.app_icon import get_app_icon
app.setWindowIcon(get_app_icon())      # QApplication / 主窗口均使用
```

图标同时用于窗口标题栏、任务栏与「关于」页面展示。

---

## 七、分析规则摘要

### 四吉星

| 星名 | 一级 | 二级 | 三级 | 四级 |
|---|---|---|---|---|
| 天医 | 13、31 | 68、86 | 49、94 | 27、72 |
| 延年 | 19、91 | 78、87 | 34、43 | 26、62 |
| 生气 | 14、41 | 67、76 | 39、93 | 28、82 |
| 伏位 | 11、22 | 88、99 | 66、77 | 33、44 |

### 四凶星

| 星名 | 一级 | 二级 | 三级 | 四级 |
|---|---|---|---|---|
| 绝命 | 12、21 | 69、96 | 48、84 | 37、73 |
| 祸害 | 17、71 | 89、98 | 46、64 | 23、32 |
| 五鬼 | 18、81 | 79、97 | 36、63 | 24、42 |
| 六煞 | 16、61 | 47、74 | 38、83 | 29、92 |

### 字母转换

A=1, B=2, …, Z=26（不区分大小写）。例如：`ABC→123`、`GTA→7201`、`MILK→1391211`。

### 评分机制

- 每个有效匹配组合按规则计分（默认：一级吉星 +10、二级 +8、三级 +6、四级 +4；凶星对应负值）。
- 综合分 = 有效组合平均分线性映射到 0–100。
- 评级区间：90–100 很好 / 75–89 好 / 60–74 一般 / 40–59 不好 / 0–39 凶。
- 单个数字、全为含 5 组合、全未匹配、无有效组合时显示"暂无评定 --"。

---

## 八、测试

```powershell
# 单元测试（33 项）
python -m unittest discover -s tests -v

# GUI 布局与交互检查（离屏运行，输出到 exports/gui_check/）
set QT_QPA_PLATFORM=offscreen
python tests/gui_check.py
```

单元测试覆盖：映射表完整性、字母转换、组合拆分顺序、吉凶匹配、数字 5 规则、
评分算法与评级区间、CSV 导出内容、详情图生成、数据库 CRUD、快照不重算、
搜索排序、损坏数据库恢复等。

---

## 九、常见问题

- **提示缺少 qfluentwidgets**：PyPI 包名是 `PyQt-Fluent-Widgets`，请执行 `pip install PyQt-Fluent-Widgets`。
- **详情图中文显示为方块**：程序会自动检测 `C:/Windows/Fonts/msyh.ttc` 等中文字体；请确保 Windows 字体目录完整。
- **CSV 中文乱码**：导出使用 UTF-8-SIG，Excel 直接打开即可正常显示；其他软件请按 UTF-8 打开。
- **中文路径读写问题**：程序全程使用 `pathlib` 与 UTF-8 编码，支持含中文的目录。
- **数据库异常**：`DatabaseManager` 会自动备份损坏文件为 `.db.bak` 并重建空库，程序不会退出。

---

版本：v1.0.0
