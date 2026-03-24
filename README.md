# 🚀 专利对比文件自动下载工具 (PatentsDown)

一款零基础即用的 Windows 桌面工具，帮助专利代理人从**审查意见通知书** PDF 中自动提取对比文件专利号，并从 Google Patents 批量下载全文 PDF。

---

## ✨ 功能特性

- **免浏览器极速下载** — 优先使用 `requests` 直连，无需启动浏览器即可秒速获取 PDF
- **智能提取** — 正则匹配 CN、US、WO、EP、JP, KR 等主流专利号格式
- **有序标注** — 按出现顺序标记为 D1、D2、D3…，下载文件命名为 `D1-CN115640636A.pdf`
- **申请文件下载** — 支持手动输入公开号，一并下载申请文件本身
- **高稳定性 Fallback** — 若直连受阻，自动回退到加固后的 Selenium 浏览器模式重试
- **网络重试机制** — 针对下载过程中的超时或连接错误，自动进行多轮重试
- **单文件 EXE** — 打包为独立可执行文件，内置防崩溃底层防护参数

## 📸 界面预览

软件界面分为两列：
| 左列 | 右列 |
|------|------|
| 手动输入申请文件公开号（选填） | 拖拽/点击上传审查意见通知书 PDF（选填） |

点击 **🚀 开始下载** 按钮后自动完成全部流程。

## 🛠️ 技术栈

| 组件 | 用途 |
|------|------|
| `customtkinter` | 现代化桌面 GUI 界面 |
| `tkinterdnd2` | 文件拖拽支持 |
| `PyMuPDF (fitz)` | PDF 文本提取 |
| `selenium` + `webdriver-manager` | 无头浏览器自动抓取 |
| `PyInstaller` | 打包为单文件 `.exe` |

## 📦 快速开始

### 方式一：直接使用（推荐）

1. 从 [Releases](https://github.com/vvangpc/PatentsDown/releases) 下载最新的 `PatentDownloader.exe`
2. 双击运行（首次启动需等待几秒自动配置浏览器驱动）
3. 拖入 PDF 或输入公开号 → 点击下载

> ⚠️ 运行要求：Windows 10/11 64位，已安装 Google Chrome 浏览器

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/vvangpc/PatentsDown.git
cd PatentsDown

# 创建虚拟环境并安装依赖
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 运行
python main.py
```

### 自行打包 EXE

```bash
pyinstaller --noconfirm --noconsole --onefile ^
  --collect-all customtkinter ^
  --collect-all tkinterdnd2 ^
  --collect-all certifi ^
  --collect-all webdriver_manager ^
  --collect-all selenium ^
  --name "PatentDownloader" main.py
```

生成的文件位于 `dist/PatentDownloader.exe`。

## 📁 项目结构

```
PatentsDown/
├── main.py           # 主程序入口（GUI 界面）
├── extractor.py      # PDF 文本提取 + 专利号正则匹配
├── downloader.py     # Google Patents 自动搜索与下载
├── requirements.txt  # Python 依赖
└── README.md
```

## 📝 使用说明

1. **只有审查意见通知书** — 拖入 PDF，点击下载 → 自动提取并下载所有对比文件
2. **只知道公开号** — 在左侧输入框填入公开号（如 `CN116123456A`），点击下载
3. **两者都有** — 填入公开号 + 拖入 PDF → 先下载申请文件，再下载对比文件
4. 下载的文件保存在审查意见通知书 PDF 的同一目录下

## ⚠️ 注意事项

- 本工具通过 Google Patents 公开渠道下载，需要网络能访问 `patents.google.com`
- **不调用任何 LLM/AI 接口**，所有处理均在本地完成
- 部分未被 Google Patents 收录的专利可能下载失败，日志会给出提示
- 首次运行时 `webdriver-manager` 会自动下载匹配您 Chrome 版本的驱动

## 📄 License

MIT License
