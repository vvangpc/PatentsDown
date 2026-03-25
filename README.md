# 🚀 专利对比文件自动下载工具 (PatentsDown) v2.0

一款零基础即用的 Windows 桌面工具，帮助专利代理人从**审查意见通知书** PDF 中自动提取对比文件专利号，并从 Google Patents 批量下载全文 PDF。

---

## ✨ v2.0 新特性

- **🧵 线程安全 UI 更新** — 利用 `after(0, ...)` 机制将界面更新操作推回主线程，彻底解决 Windows 系统下长时间下载导致的软件卡死或闪退问题。
- **🛡️ 深度反爬策略升级** — 集成 `undetected-chromedriver` 替换标准 Selenium，绕过底层特征检测，显著降低被 Google 拦截触发验证码的概率。
- **🔍 智能文件大小校验** — 实时检查下载文件。若文件小于 50KB（疑似验证码页面或拦截 HTML），自动在日志中报红警告，防止误下残破文件。
- **⏭️ 增量下载支持** — 自动识别本地已存在且大小正常的 PDF，重复运行同一任务时可秒速跳过已完成项，避免重复劳动与流量消耗。
- **📋 失败清单一键汇总** — 任务结束后若有失败项，自动在日志底部生成专门的“失败专利号列表”，方便用户直接框选复制。
- **⚡️ 极速直连优先** — 默认使用 `requests` 直连方案（免浏览器秒级下载），仅在被拦截时才自动唤醒浏览器兜底。

---

## 🛠️ 技术栈升级

| 组件 | 用途 |
|------|------|
| `customtkinter` | 现代化桌面 GUI 界面 |
| `tkinterdnd2` | 文件拖拽支持 |
| `PyMuPDF (fitz)` | PDF 文本提取 |
| `undetected-chromedriver` | **(v2.0 新增)** 专门混淆过的无头浏览器驱动，对抗反爬检测 |
| `requests` | 直连方案，低资源消耗 |
| `uv` | **(推荐)** 高性能依赖管理与脚本执行工具 |

---

## 📦 快速开始

### 方式一：从源码运行 (推荐使用 uv)

如果您安装了 [uv](https://github.com/astral-sh/uv)，只需两步：

```bash
# 1. 克隆并进入目录
git clone https://github.com/vvangpc/PatentsDown.git
cd PatentsDown

# 2. 直接运行（uv 会自动安装依赖）
uv run python main.py
```

### 方式二：传统 pip 安装

```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
pip install undetected-chromedriver setuptools  # v2.0 新增依赖
python main.py
```

## 📝 使用说明

1. **只有审查意见通知书** — 拖入 PDF，点击下载 → 自动提取并下载所有对比文件。
2. **只知道公开号** — 在左侧输入框填入公开号（如 `CN116123456A`），点击下载。
3. **已下载部分文件** — 再次运行时，工具会自动跳过已存在且完整的 PDF，只补齐缺失的文件。
4. **下载失败处理** — 任务结束后，从日志底部复制失败的专利号，直接粘贴到 Google Patents 手动搜索。

## ⚠️ 注意事项

- **环境要求** — 需要安装 **Google Chrome** 浏览器，且能正常访问 `patents.google.com`。
- **库依赖** — v2.0 依赖于 `setuptools` 以支持新驱动在 Python 3.12+ 上的运行。
- **本地化处理** — 工具不调用任何云端 AI 接口，不上传任何 PDF 内容，保护商业隐私。

## 📄 License

MIT License
