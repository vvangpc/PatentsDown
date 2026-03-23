from extractor import extract_patent_numbers
from downloader import process_downloads
import os

mock_text = """
国家知识产权局 审查意见通知书
申请号：202310123456.7
申请日：2023年01月01日
对比文件列表：
对比文件1：CN 101234567 A，说明书第2页
对比文件2：US 20190123456 A1
D1: WO 2018/123456 A1
D2: EP 1234567 B1
相关文献：JP2010123456A
"""

# Test regex
print("--- 测试正则提取 ---")
patents = extract_patent_numbers(mock_text)
print(f"提取结果: {patents}")

# We will test download of an actual known patent
test_patent = "CN110123456A"
print(f"\n--- 测试下载一个真实专利: {test_patent} ---")
base_dir = os.path.dirname(os.path.abspath(__file__))
# process_downloads([test_patent], base_dir, log_callback=print) # Uncomment if want to test download
