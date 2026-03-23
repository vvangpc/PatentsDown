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

def download_from_google_patents(driver, patent_number, save_dir, filename, logger=print):
    """通过公开号/公告号从 Google Patents 下载 PDF。"""
    try:
        logger(f"尝试通过 Google Patents 搜索: {patent_number}")
        url = f"https://patents.google.com/patent/{patent_number}/en"
        driver.get(url)
        time.sleep(2)
        
        pdf_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'patentimages.storage.googleapis.com') and contains(@href, '.pdf')]")
        
        pdf_url = None
        if pdf_elements:
            pdf_url = pdf_elements[0].get_attribute("href")
            
        if not pdf_url:
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Download PDF')]")
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute("href")
                
        if pdf_url:
            logger(f"找到 PDF 链接，正在下载...")
            return download_file(pdf_url, filename, save_dir, logger)
        else:
            logger("未找到公开下载链接。")
            return False
            
    except Exception as e:
        logger(f"下载出错: {e}")
        return False

def download_file(url, filename, save_dir, logger):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
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
    except Exception as e:
        logger(f"直接下载文件时出错: {e}")
        return False
        
def process_downloads(download_list, save_dir, log_callback=None):
    """
    download_list: [("申请文件", "CN116123456A"), ("D1", "CN115640636A"), ...]
    save_dir: 保存目录（与审查意见通知书同目录）
    """
    if not log_callback:
        log_callback = print
        
    log_callback("正在初始化下载环境...")
    driver = init_driver(log_callback=log_callback)
    if not driver:
         log_callback("错误: 无法配置虚拟浏览器，请检查网络或是否安装了Chrome。")
         return 0
         
    success_count = 0
    try:
        for label, patent_number in download_list:
            filename = f"{label}-{patent_number}"  # 例如: 申请文件-CN116123456A 或 D1-CN115640636A
            log_callback(f"\n--- 开始获取 {filename} ---")
            success = download_from_google_patents(driver, patent_number, save_dir, filename, log_callback)
            if success:
                success_count += 1
            else:
                log_callback(f"❌ {filename} 下载失败。建议手动下载。")
            time.sleep(1)
    finally:
        driver.quit()
        
    return success_count
