# PatentsDown VPS 中转下载服务 — 部署说明（链路2 服务端）

把本目录（`vps_server/`）部署到一台**未被 Google Patents 风控**的 VPS 上。
客户端（链路2）会把公开号 POST 给本服务，本服务用 VPS 自己的 IP 抓取并回传 PDF。

- 目标环境：Ubuntu 24（systemd）
- 依赖：Python3 + `flask` + `requests`（走 venv，规避 Ubuntu 24 的 PEP 668 限制）
- 鉴权：`Authorization: Bearer <AUTH_TOKEN>`，token 即唯一凭证；防火墙只放行端口（不锁 IP），
  方便你在多台电脑上凭同一个 token 使用。

---

## 一、上传文件到 VPS

把 `vps_server/` 下的 `server.py`、`requirements.txt`、`patentsdown-server.service`
放到 VPS 的 `/opt/patentsdown-server/`。例如在本机：

```bash
scp -r vps_server/* root@<VPS_IP>:/opt/patentsdown-server/
```

（若目录不存在，先 `ssh root@<VPS_IP> "mkdir -p /opt/patentsdown-server"`。）

## 二、生成访问令牌（Token）

在 VPS 上生成一个随机 token，记下来（客户端要填同一个）：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

把它填到 `server.py` 顶部的 `AUTH_TOKEN`，或写进 systemd 的 `Environment=AUTH_TOKEN=...`。

## 三、创建虚拟环境并安装依赖

```bash
cd /opt/patentsdown-server
sudo apt update && sudo apt install -y python3-venv
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 四、注册并启动 systemd 服务（开机自启）

```bash
sudo cp /opt/patentsdown-server/patentsdown-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now patentsdown-server
sudo systemctl status patentsdown-server      # 看是否 active (running)
```

## 五、放行防火墙端口

```bash
sudo ufw allow 8000/tcp        # token 即凭证，多台电脑可凭 token 访问
```

> 若你的云服务商还有「安全组 / 网络 ACL」，需在控制台同样放行 TCP 8000。

## 六、自测

```bash
# 健康检查
curl http://127.0.0.1:8000/health
# 期望: {"status":"ok"}

# 下载一篇（替换为你的 token）
curl -X POST http://127.0.0.1:8000/download \
  -H "Authorization: Bearer <你的TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"patent_number":"CN111877788A"}' -o t.pdf
file t.pdf          # 期望: PDF document
ls -lh t.pdf        # 期望: 大小 > 50KB
```

错误 / 缺失 token 应返回 401；命中 Google 限流或找不到 PDF 链接返回 502 + JSON 错误信息。

## 七、查看日志 / 重启

```bash
journalctl -u patentsdown-server -f      # 实时日志
sudo systemctl restart patentsdown-server
```

## 八、在客户端填写

打开 PatentsDown，点底部 `⚙` →「链路2 设置」弹窗：
- VPS 地址：`http://<VPS_IP>:8000`
- 令牌 Token：上面生成的随机串

点「测试连接」通过后保存，再勾选「链路2 · VPS」即可。
