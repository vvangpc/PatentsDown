"""
PatentsDown VPS 中转下载服务（链路2 服务端）

部署在未被 Google Patents 风控的 VPS 上：
接收公开号 → 用本机（VPS）IP 抓取 Google Patents 页面 → 提取并下载 PDF → 把字节回传给客户端。

设计要点：
- 仅依赖 flask + requests，不需要浏览器 / Selenium（VPS 的 IP 未被封，直连即可）。
- 鉴权：请求头 Authorization: Bearer <AUTH_TOKEN>，token 即唯一凭证。
- 抓取逻辑与客户端 downloader.py 的 download_via_requests 保持一致，确保解析行为相同。
"""
import hmac
import os
import re
import time

import requests
from flask import Flask, Response, jsonify, request

# ============================================================
#  配置（环境变量可覆盖；部署时请务必修改 AUTH_TOKEN）
# ============================================================
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# 访问令牌：客户端请求头必须为 `Authorization: Bearer <AUTH_TOKEN>`。
# 部署时改成自己的随机串，例如：
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 也可不改此处、改用环境变量 / systemd 的 Environment=AUTH_TOKEN=... 注入。
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "CHANGE_ME_TO_A_RANDOM_TOKEN")

MIN_PDF_SIZE = 50 * 1024  # 小于 50KB 视为异常（验证码页 / 损坏）

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/120.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": _UA,
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    # 去掉 br：避免 VPS 上缺 brotli 解码库导致响应体乱码
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://patents.google.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Chromium";v="120", "Not(A:Brand";v="24", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# 全局会话，复用连接并保留 cookie，降低被 Google 限流的概率
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

PDF_PATTERN = r'https://patentimages\.storage\.googleapis\.com/[^"\'>\s]+\.pdf'

app = Flask(__name__)


def _log(msg):
    print(msg, flush=True)


def fetch_pdf_bytes(patent_number):
    """抓取 Google Patents 页面 → 提取 PDF 链接 → 下载 PDF 字节。

    返回 (pdf_bytes | None, error_str)。成功时 error_str 为 ""。
    """
    url = f"https://patents.google.com/patent/{patent_number}/en"
    _log(f"[{patent_number}] 访问: {url}")

    # 针对 503/429（Google 反爬软封锁）做指数退避重试
    resp = None
    backoffs = [5, 15]  # 重试 2 次
    for i in range(len(backoffs) + 1):
        try:
            resp = SESSION.get(url, timeout=20)
        except requests.exceptions.RequestException as e:
            return None, f"请求页面失败: {e}"
        if resp.status_code in (503, 429):
            if i < len(backoffs):
                wait = backoffs[i]
                _log(f"[{patent_number}] 收到 {resp.status_code}（限流），"
                     f"{wait}s 后重试（{i + 1}/{len(backoffs)}）")
                time.sleep(wait)
                continue
            return None, f"多次重试仍返回 {resp.status_code}（Google 限流）"
        break

    if resp.status_code != 200:
        return None, f"页面返回 HTTP {resp.status_code}"

    html = resp.text
    low = html.lower()
    if "recaptcha" in low or "captcha" in low or "unusual traffic" in low:
        return None, "触发 Google 人机验证（captcha）"

    matches = re.findall(PDF_PATTERN, html)
    if not matches:
        return None, "页面源码中未找到 PDF 链接"

    pdf_url = matches[0]
    _log(f"[{patent_number}] 找到 PDF: {pdf_url}")
    try:
        r = SESSION.get(pdf_url, stream=True, timeout=60)
        r.raise_for_status()
        data = r.content
    except requests.exceptions.RequestException as e:
        return None, f"下载 PDF 失败: {e}"

    if len(data) < MIN_PDF_SIZE:
        return None, f"下载的文件过小 ({len(data) / 1024:.1f} KB)，可能损坏或被拦截"

    _log(f"[{patent_number}] 成功，{len(data) / 1024:.1f} KB")
    return data, ""


def _check_auth():
    """校验 Bearer Token（常量时间比较）。"""
    auth = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not auth.startswith(prefix):
        return False
    token = auth[len(prefix):]
    return hmac.compare_digest(token, AUTH_TOKEN)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/download")
def download():
    if not _check_auth():
        return jsonify({"ok": False, "error": "未授权（token 错误或缺失）"}), 401

    body = request.get_json(silent=True) or {}
    pn = (body.get("patent_number") or "").strip().upper().replace(" ", "")
    if not pn:
        return jsonify({"ok": False, "error": "缺少 patent_number"}), 400

    pdf, err = fetch_pdf_bytes(pn)
    if pdf is None:
        # 502：上游（Google）问题，交给客户端记为失败
        return jsonify({"ok": False, "error": err}), 502

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{pn}.pdf"',
            "X-Patent-Number": pn,
        },
    )


if __name__ == "__main__":
    token_state = "已设置" if AUTH_TOKEN != "CHANGE_ME_TO_A_RANDOM_TOKEN" else "未修改 ⚠️"
    _log(f"PatentsDown VPS 服务启动: http://{HOST}:{PORT}  (AUTH_TOKEN {token_state})")
    app.run(host=HOST, port=PORT, threaded=True)
