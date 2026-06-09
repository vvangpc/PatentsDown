"""链路2：通过部署在 VPS 上的中转服务下载专利 PDF。

把公开号 POST 给 VPS，VPS 用未被风控的 IP 抓取 Google Patents 并回传 PDF 字节，本机落盘。
与 downloader.process_downloads 保持相同的日志约定（✅ / ⏩ / ⚠️ 前缀），
以复用 main.py 中基于日志前缀的进度回调。
"""
import os

import requests

MIN_PDF_SIZE = 50 * 1024  # 与 downloader.download_file 一致的防坑校验阈值


def _normalize_base(base_url):
    return (base_url or "").strip().rstrip("/")


def health_check(base_url, token, timeout=10):
    """供「测试连接」按钮调用，返回 (ok: bool, msg: str)。token 暂未被 /health 校验，仅做可达性探测。"""
    base = _normalize_base(base_url)
    if not base:
        return False, "VPS 地址为空"
    try:
        resp = requests.get(f"{base}/health", timeout=timeout)
    except requests.exceptions.RequestException as e:
        return False, f"无法连接: {e}"
    if resp.status_code == 200:
        return True, "连接成功 ✅"
    return False, f"服务返回 HTTP {resp.status_code}"


def _download_one(base, token, patent_number, save_path, logger):
    """请求 VPS 下载单篇并写盘。成功返回 True。"""
    try:
        resp = requests.post(
            f"{base}/download",
            json={"patent_number": patent_number},
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
            timeout=120,
        )
    except requests.exceptions.RequestException as e:
        logger(f"[链路2] {patent_number} 网络错误: {e}")
        return False

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", "")
        except ValueError:
            err = (resp.text or "")[:200]
        if resp.status_code == 401:
            logger("[链路2] 鉴权失败（token 错误或缺失），请在「⚙ 链路2 设置」中检查令牌。")
        else:
            logger(f"[链路2] {patent_number} 失败: {err or ('HTTP ' + str(resp.status_code))}")
        return False

    try:
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except OSError as e:
        logger(f"[链路2] {patent_number} 写入文件失败: {e}")
        return False

    size = os.path.getsize(save_path)
    if size < MIN_PDF_SIZE:
        logger(f"⚠️ 警告：下载的文件过小 ({size / 1024:.1f} KB)，可能已损坏，请手动检查！")
    else:
        logger(f"✅ 成功保存: {os.path.basename(save_path)} ({size / 1024:.1f} KB)")
    return True


def process_downloads_via_vps(download_list, save_dir, base_url, token, log_callback=None):
    """与 downloader.process_downloads 同签名（多 base_url / token 两参）。

    download_list: [("申请文件", "CN116123456A"), ("D1", "CN115640636A"), ...]
    逐条把公开号发给 VPS 下载并回传，返回成功数。
    本机 IP 已被封，故无 Selenium 兜底。
    """
    logger = log_callback or print
    base = _normalize_base(base_url)

    logger("🌐 正在通过 VPS 中转下载（链路2）...")
    if not base or not token:
        logger("❌ 链路2 未配置 VPS 地址或令牌。")
        return 0

    success_count = 0
    for label, patent_number in download_list:
        filename = f"{label}-{patent_number}"
        save_path = os.path.join(save_dir, f"{filename}.pdf")
        logger(f"\n--- 开始获取 {filename} ---")

        # 已存在且完整（>50KB）→ 直接跳过
        if os.path.exists(save_path) and os.path.getsize(save_path) > MIN_PDF_SIZE:
            logger(f"⏩ 文件已存在且完整，自动跳过: {filename}.pdf")
            success_count += 1
            continue

        if _download_one(base, token, patent_number, save_path, logger):
            success_count += 1
        else:
            logger(f"❌ {filename} 下载失败。")

    return success_count
