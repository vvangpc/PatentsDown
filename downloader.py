"""
专利 PDF 下载器
策略: 优先使用 requests 直连 Google Patents（免浏览器极速下载）
      仅当直连失败时，才 fallback 到 Selenium 浏览器模式
"""
import os
import re
import time
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def download_file(url, filename, save_dir, logger, max_retries=3):
    """下载文件到本地，支持自动重试"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, stream=True, timeout=60)
            response.raise_for_status()

            save_path = os.path.join(save_dir, f"{filename}.pdf")
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger(f"✅ 成功保存: {os.path.basename(save_path)}")
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
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        html = resp.text

        # 检测 reCAPTCHA / 人机验证
        html_lower = html.lower()
        if "recaptcha" in html_lower or "captcha" in html_lower or "unusual traffic" in html_lower:
            logger("⚠️ 触发 Google 频繁访问验证，直连模式跳过")
            return False

        # 用正则提取 PDF 链接
        pdf_pattern = r'https://patentimages\.storage\.googleapis\.com/[^"\'>\s]+\.pdf'
        matches = re.findall(pdf_pattern, html)

        if matches:
            pdf_url = matches[0]
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

def init_driver(log_callback=print):
    """初始化 Selenium 浏览器，带完整的防崩溃参数"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as e:
        log_callback(f"Selenium 相关库未安装: {e}")
        return None

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")  # 抑制控制台日志
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        driver_path = ChromeDriverManager().install()
    except Exception as e:
        log_callback(f"ChromeDriver 下载失败（请检查网络连接）: {e}")
        return None

    try:
        service = ChromeService(
            executable_path=driver_path,
            creation_flags=subprocess.CREATE_NO_WINDOW  # 防止 PyInstaller 无控制台崩溃
        )
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        log_callback(f"Chrome 浏览器启动失败: {e}")
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

        # 检测 reCAPTCHA
        page_src = driver.page_source.lower()
        if "recaptcha" in page_src or "captcha" in page_src or "unusual traffic" in page_src:
            logger("⚠️ 触发 Google 频繁访问验证，当前文件跳过下载")
            return False

        # 显式等待（最多 10 秒）
        pdf_xpath = "//a[contains(@href, 'patentimages.storage.googleapis.com') and contains(@href, '.pdf')]"
        try:
            WebDriverWait(driver, 10).until(
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
        time.sleep(0.5)  # 礼貌间隔，降低被 Google 限流的概率

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
                time.sleep(1)
        finally:
            driver.quit()

    return success_count
