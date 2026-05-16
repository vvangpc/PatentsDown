## 🆕 v3.0 — 双模式标签页 + 现代化紧凑 GUI

一次大版本更新：双工作流标签页彻底分离，UI 全面重做。

### 主要变化

- 🆕 **双模式标签页**：智能识别 PDF 与手动输入公开号两种工作流彻底分开为独立 Tab，互不干扰。
- 🆕 **模式二 · 手动输入**：动态行 + 2 列网格布局，默认 4 个输入框，可一键增删；按行优先自动重排编号 D1, D2, ...
- 🎨 **现代化 GUI 全面重做**：基于 `customtkinter` 重构，新蓝色主题图标、统一配色、紧凑面板、明暗模式自适应。
- 📐 **紧凑布局**：默认窗口 800×660，更贴合主流笔记本屏幕；切换标签页时下方控件位置固定不抖动。
- 🆕 **下载按钮归位**：[🚀 开始下载] 与 [📂 选择目录] 同行排列，节省纵向空间。
- 🆕 **新图标**：蓝色渐变 + 白色 `P` + 向下箭头，标题栏、任务栏、EXE 三处统一。
- ✏️ 应用统一更名为「专利文件下载器」。

### 下载

- [`PatentsDown_v3.0.exe`](https://github.com/vvangpc/PatentsDown/releases/download/v3.0/PatentsDown_v3.0.exe) — 46 MB，Windows 10/11 单文件免安装，双击即用。

### 截图

![模式一 · 智能识别](https://github.com/vvangpc/PatentsDown/raw/main/docs/screenshot_mode1.png)
![模式二 · 手动输入](https://github.com/vvangpc/PatentsDown/raw/main/docs/screenshot_mode2.png)

### 兼容性

- 沿用既有下载引擎（requests 直连 + Selenium 回退），所有 v2.x 已支持的国家/地区（CN/US/WO/EP/JP/KR/DE/FR/GB/TW/AU）继续可用。
- 增量下载、文件大小校验、失败清单等核心能力不变。

完整说明见 [README](https://github.com/vvangpc/PatentsDown/blob/main/README.md)。
