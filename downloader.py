import os
import time
import requests
import sys

# Windows PyInstaller --noconsole 模式下防崩溃保护
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init_driver(log_callback=print):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
         service = ChromeService(ChromeDriverManager().install())
         driver = webdriver.Chrome(service=service, options=chrome_options)
         return driver
    except Exception as e:
         log_callback(f"WebDriver 初始化失败，详细原因: {e}")
         return None

def _check_captcha(driver, logger):
    """检查页面是否触发了 Google reCAPTCHA / 人机验证"""
    try:
        page_src = driver.page_source.lower()
        captcha_indicators = [
            "recaptcha", "g-recaptcha", "captcha-form",
            "unusual traffic", "our systems have detected",
            "sorry/index", "ipv4.google.com/sorry"
        ]
        for indicator in captcha_indicators:
            if indicator in page_src:
                logger("⚠️ 触发 Google 频繁访问验证，当前文件跳过下载")
                return True
    except Exception:
        pass
    return False

def download_from_google_patents(driver, patent_number, save_dir, filename, logger=print):
    """通过公开号/公告号从 Google Patents 下载 PDF（使用显式等待）。"""
    try:
        logger(f"尝试通过 Google Patents 搜索: {patent_number}")
        url = f"https://patents.google.com/patent/{patent_number}/en"
        driver.get(url)
        
        # 检查是否触发验证码
        if _check_captcha(driver, logger):
            return False
        
        # 显式等待最多 10 秒，直到 PDF 链接出现
        pdf_xpath = "//a[contains(@href, 'patentimages.storage.googleapis.com') and contains(@href, '.pdf')]"
        pdf_url = None
        
        try:
            wait = WebDriverWait(driver, 10)
            pdf_element = wait.until(EC.presence_of_element_located((By.XPATH, pdf_xpath)))
            pdf_url = pdf_element.get_attribute("href")
        except Exception:
            # 显式等待超时，尝试备用 XPath
            try:
                pdf_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Download PDF')]")
                if pdf_links:
                    pdf_url = pdf_links[0].get_attribute("href")
            except Exception:
                pass
                
        if pdf_url:
            logger(f"找到 PDF 链接，正在下载...")
            return download_file(pdf_url, filename, save_dir, logger)
        else:
            logger("未找到公开下载链接。")
            return False
            
    except Exception as e:
        logger(f"下载出错: {e}")
        return False

def download_file(url, filename, save_dir, logger, max_retries=3):
    """下载文件，支持最多 max_retries 次重试。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            save_path = os.path.join(save_dir, f"{filename}.pdf")
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger(f"✅ 成功保存: {os.path.basename(save_path)}")
            return True
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries:
                logger(f"⏳ 网络异常，正在进行第 {attempt + 1}/{max_retries} 次重试...")
                time.sleep(2)
            else:
                logger(f"❌ 重试 {max_retries} 次后仍失败: {e}")
                return False
        except Exception as e:
            logger(f"❌ 下载文件时出错: {e}")
            return False
    
    return False
        
def process_downloads(download_list, save_dir, log_callback=None, status_callback=None):
    """
    download_list: [("申请文件", "CN116123456A"), ("D1", "CN115640636A"), ...]
    save_dir: 保存目录
    log_callback: 日志回调函数
    status_callback: 状态更新回调函数 status_callback(index, new_status)
    """
    if not log_callback:
        log_callback = print
        
    log_callback("正在初始化下载环境...")
    driver = init_driver(log_callback=log_callback)
    if not driver:
         log_callback("错误: 无法配置虚拟浏览器，请检查网络或是否安装了Chrome。")
         # 将所有项标记为失败
         if status_callback:
             for i in range(len(download_list)):
                 status_callback(i, "❌ 浏览器错误")
         return 0
         
    success_count = 0
    try:
        for idx, (label, patent_number) in enumerate(download_list):
            filename = f"{label}-{patent_number}"
            log_callback(f"\n--- 开始获取 {filename} ---")
            
            if status_callback:
                status_callback(idx, "⏳ 下载中...")
            
            success = download_from_google_patents(driver, patent_number, save_dir, filename, log_callback)
            
            if success:
                success_count += 1
                if status_callback:
                    status_callback(idx, "✅ 成功")
            else:
                log_callback(f"❌ {filename} 下载失败。建议手动下载。")
                if status_callback:
                    status_callback(idx, "❌ 失败")
            time.sleep(1)
    finally:
        driver.quit()
        
    return success_count
