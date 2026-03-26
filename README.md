# 🚀 PatentsDown — 专利对比文件自动下载工具 v2.1

一款**零门槛即用**的 Windows 桌面工具，帮助专利代理人 / 审查员从**审查意见通知书 PDF** 中自动提取对比文件专利号，并从 [Google Patents](https://patents.google.com/) 批量下载全文 PDF。

> 本工具不上传任何 PDF 内容或调用云端 AI 接口，所有操作均在本地完成，保护商业隐私。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📄 **智能解析** | 自动识别审查意见通知书首页中的申请号与全部对比文件专利号 |
| 🌐 **全球覆盖** | 支持 CN、US、WO、EP、JP、KR、DE、FR、GB、TW、AU 等主流国家/地区 |
| ⚡ **双模式下载** | 优先使用 `requests` 直连（免浏览器极速），失败后自动回退到 `Selenium` 浏览器模式 |
| ⏭️ **增量下载** | 自动跳过本地已存在且完整的 PDF，避免重复下载 |
| 🔍 **文件校验** | 下载完成后自动检查文件大小，< 50KB 则警告可能损坏或被拦截 |
| 🛡️ **反爬对抗** | 集成 `undetected-chromedriver`，显著降低被 Google 验证码拦截的概率 |
| 📋 **失败清单** | 任务结束后自动汇总失败专利号，方便一键复制手动处理 |

---

## 🖥️ 界面预览

工具采用 `customtkinter` 构建现代化 GUI，支持**拖拽上传** PDF 与**手动输入**公开号两种方式：

- **左侧** — 输入申请文件公开号（可选）
- **右侧** — 拖入或点击选择审查意见通知书 PDF（可选）
- **底部** — 实时日志输出与进度条

---

## 📦 快速开始

### 前置条件

- **Python 3.8+**
- **Google Chrome 浏览器**（Selenium 回退模式需要）
- 能正常访问 `patents.google.com`

### 方式一：使用 uv（推荐）

如果你已安装 [uv](https://github.com/astral-sh/uv)，只需两步：

```bash
# 1. 克隆仓库
git clone https://github.com/vvangpc/PatentsDown.git
cd PatentsDown

# 2. 直接运行（uv 会自动处理依赖）
uv run python main.py
```

### 方式二：使用 pip

```bash
git clone https://github.com/vvangpc/PatentsDown.git
cd PatentsDown

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate       # Windows
# source venv/bin/activate    # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

### 方式三：下载 EXE（免安装）

前往 [Releases](https://github.com/vvangpc/PatentsDown/releases) 页面下载最新的 `PatentsDownv2.1.exe`，双击即可运行。

---

## 📝 使用说明

1. **只有审查意见通知书** — 拖入 PDF 或点击选择文件，点击「开始下载」→ 自动提取并下载所有对比文件。
2. **只知道公开号** — 在左侧输入框填入公开号（如 `CN116123456A`），选择保存目录后点击下载。
3. **两者都有** — 同时填入公开号并拖入 PDF，工具会合并下载申请文件与所有对比文件。
4. **已下载部分文件** — 再次运行同一任务时，工具会自动跳过已存在且完整的 PDF。
5. **下载失败处理** — 任务结束后，从日志底部复制失败的专利号，前往 [Google Patents](https://patents.google.com/) 手动搜索下载。

---

## 🏗️ 项目结构

```
PatentsDown/
├── main.py           # 程序入口 + GUI 界面（customtkinter + tkinterdnd2）
├── downloader.py     # 下载引擎（requests 直连 + Selenium 回退）
├── extractor.py      # PDF 解析（PyMuPDF 提取文本 + 正则匹配专利号）
├── pack.py           # PyInstaller 打包脚本
├── requirements.txt  # 依赖清单
└── README.md         # 本文件
```

---

## 🛠️ 技术栈

| 组件 | 版本要求 | 用途 |
|------|----------|------|
| `customtkinter` | — | 现代化桌面 GUI |
| `tkinterdnd2` | — | 文件拖拽支持 |
| `PyMuPDF` (fitz) | — | PDF 文本提取 |
| `requests` | — | HTTP 直连下载（极速模式） |
| `undetected-chromedriver` | — | 反爬浏览器驱动（回退模式） |
| `setuptools` | — | 支持 Python 3.12+ 运行 |
| `pyinstaller` | — | 打包为独立 EXE |

---

## 🔧 打包为 EXE

```bash
# 使用内置打包脚本
python pack.py
# 或使用 uv
uv run python pack.py
```

生成的 EXE 位于 `dist/` 目录下。

---

## ⚠️ 注意事项

- **网络要求** — 需能正常访问 Google Patents（部分网络环境可能需要代理）。
- **Chrome 浏览器** — Selenium 回退模式需要本地安装 Chrome；首次使用时会自动下载 ChromeDriver。
- **频繁访问限制** — 大批量下载时 Google 可能触发验证码，建议适当间隔或分批处理。
- **扫描件 PDF** — 工具仅支持文字型 PDF，扫描件（图片型）无法提取文本。

---

## 📄 许可证

[MIT License](LICENSE)
