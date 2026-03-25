import fitz  # PyMuPDF
import re
import os

def extract_text_from_first_page(pdf_path):
    """提取PDF第一页的全部文本"""
    try:
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            doc.close()
            return text
        else:
            return ""
    except Exception as e:
        print(f"读取 PDF 出错: {e}")
        return ""

def extract_application_number(text):
    """
    提取审查意见通知书中 "申请号" 字段
    格式通常为: 申请号 202310123456.7 或 申请号：2023101234567
    返回清洗后的纯数字申请号(去掉点号)，例如 "2023101234567"
    """
    # 匹配 "申请号" 后面跟着的数字(可能带点号分隔)
    pattern = r"申请号[：:\s]*(\d[\d.]+\d)"
    match = re.search(pattern, text)
    if match:
        raw = match.group(1)
        # 去掉中间的点号，例如 "202310123456.7" -> "2023101234567"
        clean = raw.replace(".", "")
        return clean
    return None

def extract_patent_numbers(text):
    """
    按出现顺序提取专利号，返回有序列表 [(label, patent_number), ...]
    例如: [("D1", "CN115640636A"), ("D2", "US20190123456A1")]
    """
    seen = set()
    ordered_patents = []
    
    # 匹配以 CN, US, WO, EP, JP, KR, DE, FR, GB, TW, AU 开头，紧跟数字和可能的符号（/, -, 中划线等），最后可能带1-2位字母数字结尾
    pattern = r"\b(CN|US|WO|EP|JP|KR|DE|FR|GB|TW|AU)\s*[A-Z]?\s*[\d\-\/]+\s*[A-Z0-9]{0,2}\b"
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for m in matches:
        raw_match = m.group(0).upper()
        clean_no = re.sub(r'\s+', '', raw_match)
        if clean_no not in seen:
            seen.add(clean_no)
            ordered_patents.append(clean_no)
    
    # 按出现顺序分配 D1, D2, D3... 标签
    labeled_patents = []
    for i, pn in enumerate(ordered_patents, start=1):
        labeled_patents.append((f"D{i}", pn))
        
    return labeled_patents

def process_office_action(pdf_path):
    """
    返回: (success, app_number_or_none, patent_list_or_error_msg)
    app_number: 申请号（纯数字字符串）或 None
    patent_list: [("D1", "CN..."), ...] 或 错误信息字符串
    """
    print(f"开始解析: {os.path.basename(pdf_path)}")
    text = extract_text_from_first_page(pdf_path)
    if not text.strip():
         return False, None, "提取文本为空或失败，可能是扫描件。"
    
    # 提取申请号
    app_number = extract_application_number(text)
    
    # 提取对比文件专利号
    patents = extract_patent_numbers(text)
    if not patents and not app_number:
        return False, None, "未在第一页找到申请号或对比文件专利号。"
        
    return True, app_number, patents
