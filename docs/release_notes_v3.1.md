## 🆕 v3.1 — Windows 右键菜单集成

省去「打开 App → 拖文件」两步，直接在资源管理器里右键 PDF 即可开始下载。

### 新特性

- 🪄 **Windows 右键菜单集成**：注册后可在资源管理器里右键任意 PDF → 「专利文件下载」即可启动 App 并自动加载到模式一。
- ⌨️ **CLI 参数支持**：`专利文件下载器_v3.1.exe "C:\path\to\审查意见.pdf"` 也能达到相同效果。
- ⚙️ **App 内一键开关**：底部 [➕ 添加右键菜单] 按钮，写入 HKCU 注册表（仅当前用户，**无需管理员**）；再次点击即可移除。
- 🛡️ **路径过期检测**：移动 exe 后启动，App 会在日志中提示需要重新注册右键菜单。

### 如何使用右键菜单

1. 把 `PatentsDown_v3.1.exe` 放在稳定位置（如 `C:\Tools\`）。
2. 双击启动 App → 点底部 [➕ 添加右键菜单]。
3. 之后右键任意 PDF → 「专利文件下载」 → App 启动并加载该 PDF → 点 [🚀 开始下载] 即可。

技术细节：注册位置 `HKCU\Software\Classes\SystemFileAssociations\.pdf\shell\PatentsDown`，纯当前用户级别。

### 下载

- [`PatentsDown_v3.1.exe`](https://github.com/vvangpc/PatentsDown/releases/download/v3.1/PatentsDown_v3.1.exe) — 46 MB，Windows 10/11 单文件免安装。

### 兼容性

- 沿用 v3.0 的双模式标签页 / 现代化 GUI / 紧凑布局。
- 下载引擎、解析逻辑、所有支持的国家/地区均不变。
- 拖拽与点击选择 PDF 的原有用法继续可用，不强制使用右键菜单。

完整说明见 [README](https://github.com/vvangpc/PatentsDown/blob/main/README.md)。
