"""
专利 PDF 下载器
策略: 优先使用 requests 直连 Google Patents（免浏览器极速下载）
      仅当直连失败时，才 fallback 到 Selenium 浏览器模式
"""
import os
import re
import time
import random
import subprocess
import requests
import sys

# Windows PyInstaller --noconsole 模式下防崩溃保护
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# ============================================================
#  通用工具函数
# ============================================================

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/120.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": _UA,
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    # 去掉 br：requests 默认未装 brotli 解码库时，若声明 br 会拿到无法解码的乱码响应，
    # 导致正则匹配不到 PDF 链接（与 vps_server/server.py 保持一致）。
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


def _extract_pdf_url(html):
    """从 Google Patents 页面 HTML 提取 PDF 真实地址。

    PDF 真实路径带哈希目录（如 ad/75/30/...），无法靠专利号拼接，必须从页面解析。
    优先解析 Google 官方给出的 <meta name="citation_pdf_url" content="...">；
    解析不到再兜底扫描页面里第一条 patentimages 直链。
    """
    m = re.search(
        r'<meta\s+name=["\']citation_pdf_url["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(
        r'https://patentimages\.storage\.googleapis\.com/[^"\'>\s]+\.pdf', html)
    return m.group(0) if m else None


def download_file(url, filename, save_dir, logger, max_retries=3):
    """下载文件到本地，支持自动重试"""
    save_path = os.path.join(save_dir, f"{filename}.pdf")
    # 如果文件已存在，且大于 50KB（结合了上一次的防坑校验），则直接跳过
    if os.path.exists(save_path) and os.path.getsize(save_path) > 50 * 1024:
        logger(f"⏩ 文件已存在且完整，自动跳过: {filename}.pdf")
        return True

    for attempt in range(1, max_retries + 1):
        try:
            response = SESSION.get(url, stream=True, timeout=60)
            response.raise_for_status()

            save_path = os.path.join(save_dir, f"{filename}.pdf")
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # --- 校验：必须是真 PDF（%PDF 文件头），否则视为失败并删除 ---
            file_size = os.path.getsize(save_path)
            with open(save_path, "rb") as fh:
                head = fh.read(5)
            if not head.startswith(b"%PDF"):
                logger(f"❌ 下载内容不是有效 PDF（{file_size / 1024:.1f} KB，文件头 {head!r}），"
                       f"可能是报错页/验证码页，已删除。")
                try:
                    os.remove(save_path)
                except OSError:
                    pass
                return False
            if file_size < 50 * 1024:  # 真 PDF 但偏小，保留并提醒
                logger(f"⚠️ 警告：下载的 PDF 偏小 ({file_size / 1024:.1f} KB)，请手动确认完整性。")
            else:
                logger(f"✅ 成功保存: {os.path.basename(save_path)} ({file_size / 1024:.1f} KB)")

            return True
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger(f"网络错误 (第 {attempt}/{max_retries} 次尝试): {e}")
            if attempt < max_retries:
                logger("等待 2 秒后重试...")
                time.sleep(2)
            else:
                logger("已达最大重试次数，下载失败。")
                return False
        except Exception as e:
            logger(f"下载文件时出错: {e}")
            return False
    return False

# ============================================================
#  方案一: 免浏览器直连 (requests + 正则提取 PDF 链接)
# ============================================================

def download_via_requests(patent_number, save_dir, filename, logger):
    """
    纯 requests 方案：直接获取 Google Patents 页面源码，
    用正则提取 PDF 下载链接，完全不需要启动浏览器。
    """
    try:
        url = f"https://patents.google.com/patent/{patent_number}/en"
        logger(f"[直连模式] 访问: {url}")

        # 针对 503/429（Google 反爬软封锁）做指数退避重试
        resp = None
        backoffs = [5, 15]  # 重试 2 次
        for i in range(len(backoffs) + 1):
            resp = SESSION.get(url, timeout=20)
            if resp.status_code in (503, 429):
                if i < len(backoffs):
                    wait = backoffs[i]
                    logger(f"[直连模式] 收到 {resp.status_code}（Google 限流），"
                           f"{wait} 秒后重试（{i + 1}/{len(backoffs)}）...")
                    time.sleep(wait)
                    continue
                logger(f"[直连模式] 多次重试仍返回 {resp.status_code}，转浏览器模式")
                return False
            break
        resp.raise_for_status()
        html = resp.text

        # 检测 reCAPTCHA / 人机验证
        html_lower = html.lower()
        if "recaptcha" in html_lower or "captcha" in html_lower or "unusual traffic" in html_lower:
            logger("⚠️ 触发 Google 频繁访问验证，直连模式跳过")
            return False

        # 优先解析 citation_pdf_url meta 标签，兜底用正则扫描 patentimages 直链
        pdf_url = _extract_pdf_url(html)
        if pdf_url:
            logger(f"[直连模式] 找到 PDF 链接，正在下载...")
            return download_file(pdf_url, filename, save_dir, logger)
        else:
            logger("[直连模式] 未在页面源码中找到 PDF 链接")
            return False

    except requests.exceptions.RequestException as e:
        logger(f"[直连模式] 网络请求失败: {e}")
        return False
    except Exception as e:
        logger(f"[直连模式] 出错: {e}")
        return False

# ============================================================
#  方案二: Selenium 浏览器模式 (Fallback)
# ============================================================

def find_chrome():
    """探测本机 Google Chrome 可执行文件路径，找不到返回 None"""
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                     r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                     r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def init_driver(log_callback=print):
    """初始化标准 Selenium Chrome 浏览器（可见窗口）。
    Selenium 4.6+ 内置 Selenium Manager，会自动匹配本机 Chrome 版本下载驱动。"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        log_callback(f"❌ selenium 库未安装: {e}")
        return None

    chrome_path = find_chrome()
    if not chrome_path:
        log_callback("❌ 未检测到 Google Chrome，请先安装 Chrome 后重试。")
        return None

    options = Options()
    options.binary_location = chrome_path
    # 可见窗口模式：不加 --headless，便于用户手动过人机验证
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={_UA}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        log_callback(f"❌ 浏览器启动失败，原因: {str(e)[:200]}")
        log_callback("   （请确认 Chrome 已正常安装，且能联网下载匹配的 chromedriver）")
        return None

def download_via_selenium(driver, patent_number, save_dir, filename, logger):
    """Selenium Fallback: 通过真实浏览器加载页面并提取 PDF 链接"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        return False

    try:
        logger(f"[浏览器模式] 访问 Google Patents: {patent_number}")
        url = f"https://patents.google.com/patent/{patent_number}/en"
        driver.get(url)

        # 检测 reCAPTCHA：不再直接跳过，而是等用户在可见窗口里手动过验证
        wait_timeout = 15
        page_src = driver.page_source.lower()
        if "recaptcha" in page_src or "captcha" in page_src or "unusual traffic" in page_src:
            logger("⚠️ 检测到人机验证，请在弹出的浏览器窗口中完成验证，"
                   "程序将自动继续（最多等待 180 秒）...")
            wait_timeout = 180

        # 显式等待 PDF 链接出现
        pdf_xpath = "//a[contains(@href, 'patentimages.storage.googleapis.com') and contains(@href, '.pdf')]"
        try:
            WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_element_located((By.XPATH, pdf_xpath))
            )
        except Exception:
            pass

        pdf_elements = driver.find_elements(By.XPATH, pdf_xpath)
        pdf_url = None
        if pdf_elements:
            pdf_url = pdf_elements[0].get_attribute("href")

        if not pdf_url:
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Download PDF')]")
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute("href")

        if pdf_url:
            logger("[浏览器模式] 找到 PDF 链接，正在下载...")
            return download_file(pdf_url, filename, save_dir, logger)
        else:
            logger("[浏览器模式] 未找到公开下载链接。")
            return False

    except Exception as e:
        logger(f"[浏览器模式] 出错: {e}")
        return False

# ============================================================
#  主调度: requests 优先 → Selenium fallback
# ============================================================

def process_downloads(download_list, save_dir, log_callback=None):
    """
    download_list: [("申请文件", "CN116123456A"), ("D1", "CN115640636A"), ...]
    save_dir: 保存目录
    策略: 优先 requests 直连，失败后才启动 Selenium
    """
    if not log_callback:
        log_callback = print

    success_count = 0
    selenium_needed = []  # 收集直连失败的条目，统一用 Selenium 重试

    # —————— 第一轮: requests 直连（极速，免浏览器） ——————
    log_callback("🚀 正在使用免浏览器极速模式下载...")
    for label, patent_number in download_list:
        filename = f"{label}-{patent_number}"
        log_callback(f"\n--- 开始获取 {filename} ---")
        success = download_via_requests(patent_number, save_dir, filename, log_callback)
        if success:
            success_count += 1
        else:
            selenium_needed.append((label, patent_number))
        time.sleep(0.5 + random.uniform(0, 0.5))  # 礼貌间隔 + 随机抖动，降低被 Google 限流的概率

    # —————— 第二轮: Selenium Fallback（仅处理失败条目） ——————
    if selenium_needed:
        log_callback(f"\n🔄 {len(selenium_needed)} 个文件直连失败，启动浏览器模式重试...")
        log_callback("（首次使用可能需下载 ChromeDriver，请耐心等待）")
        driver = init_driver(log_callback=log_callback)
        if not driver:
            log_callback("⚠️ 浏览器模式不可用，以下文件需手动下载：")
            for label, pn in selenium_needed:
                log_callback(f"  ❌ {label}-{pn}")
            return success_count

        try:
            for label, patent_number in selenium_needed:
                filename = f"{label}-{patent_number}"
                log_callback(f"\n--- [浏览器重试] {filename} ---")
                success = download_via_selenium(driver, patent_number, save_dir, filename, log_callback)
                if success:
                    success_count += 1
                else:
                    log_callback(f"❌ {filename} 下载失败。建议手动下载。")
                time.sleep(1 + random.uniform(0, 0.5))
        finally:
            driver.quit()

    return success_count
