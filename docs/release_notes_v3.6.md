## 🆕 v3.6 — 新增「下载链路」选择（链路1 直连 / 链路2 VPS 中转）

### 背景

当出口 IP 被 Google Patents 风控时，直连 `patents.google.com` 会连续返回 **503（限流）**，
导致下载失败（日志表现为「多次重试仍返回 503，转浏览器模式」）。若另有一台 IP 未被风控的
VPS，可让它代为下载、再把 PDF 回传到本机。

### 新特性

- 🔀 **底部新增两个互斥复选框「链路1 · 直连」/「链路2 · VPS」**（在「添加右键菜单」按钮前面）。
  - **链路1 · 直连**：保持原行为 —— 本机 `requests` 直连 + Selenium 浏览器兜底。
  - **链路2 · VPS**：把公开号发送到部署在 VPS 上的下载服务，由 VPS 用自己的 IP 下载，
    完成后把 PDF 字节回传本机保存。两条链路共用「失败清单 / 图片型(扫描件)PDF 检测 / 完成弹窗」。
- ⚙ **链路2 设置弹窗**：填写 VPS 地址与令牌 Token，可「测试连接」，保存到本地
  `%APPDATA%\PatentsDown\link_config.json`（**不进 Git 仓库**，避免暴露自己的 VPS）。
  勾选链路2 但未配置时会自动弹出设置窗引导填写。

### VPS 服务端

新增 `vps_server/`（自包含，整目录拷到 VPS 即可部署）：

| 文件 | 说明 |
| --- | --- |
| `server.py` | Flask 服务：`GET /health`、`POST /download`（Bearer Token 鉴权），仅依赖 flask + requests，无需浏览器 |
| `requirements.txt` | `flask` / `requests` |
| `patentsdown-server.service` | systemd 单元，开机自启、日志走 journald |
| `README_DEPLOY.md` | Ubuntu 24 部署步骤（venv + ufw + 自测） |

鉴权仅靠 `Authorization: Bearer <TOKEN>`（token 即凭证），防火墙放行端口但不锁单一 IP，
方便在多台电脑上凭同一 token 使用。

### Release 资产说明

| 文件 | 说明 |
| --- | --- |
| `PatentsDown_v3.6_Setup.exe` | **安装版**，双击安装，启动快，推荐日常使用 |
| `PatentsDown_v3.6_Portable.exe` | **便携版**（单文件免安装），首次启动需解压、略慢 |
