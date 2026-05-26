import fitz  # PyMuPDF
import re
import os


# 专利公开号正则（CN/US/WO/EP/JP/KR/DE/FR/GB/TW/AU）
# 抽成模块级常量，供三条解析路径共用
PATENT_NUMBER_PATTERN = (
    r"\b(CN|US|WO|EP|JP|KR|DE|FR|GB|TW|AU)\s*[A-Z]?\s*[\d\-\/]+\s*[A-Z0-9]{0,2}\b"
)
_PATENT_RE = re.compile(PATENT_NUMBER_PATTERN, re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?$")


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
    pattern = r"申请号[：:\s]*(\d[\d.]+\d)"
    match = re.search(pattern, text)
    if match:
        raw = match.group(1)
        clean = raw.replace(".", "")
        return clean
    return None


def _match_patent(cell_text):
    """在单元格文本中尝试匹配第一个专利公开号；命中返回 clean_no，否则 None。"""
    if not cell_text:
        return None
    m = _PATENT_RE.search(cell_text)
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(0).upper())


# ============================================================
#  路径 a: PyMuPDF find_tables() —— 表格结构感知
# ============================================================
def _parse_via_find_tables(page):
    """
    返回 (patent_list, skipped_list, hit)。
    hit=True 表示找到了目标对比文件表格（即使该表里 patent_list 为空也算 hit，
    比如所有行都是非专利时）。
    """
    try:
        finder = page.find_tables()
    except Exception:
        return [], [], False

    tables = getattr(finder, "tables", None)
    if not tables:
        # 不同版本 find_tables() 返回值不一致，做一次兜底
        try:
            tables = list(finder)
        except Exception:
            return [], [], False

    for tbl in tables:
        try:
            rows = tbl.extract()
        except Exception:
            continue
        if not rows or len(rows) < 2:
            continue

        # 找到目标表格：header 行同时含「编号」和「文件号」或「名称」
        header_text = " ".join(str(c or "") for c in rows[0])
        if "编号" not in header_text:
            continue
        if ("文件号" not in header_text) and ("名称" not in header_text):
            continue

        patent_list = []
        skipped_list = []
        seen = set()
        for row in rows[1:]:
            if not row or len(row) < 2:
                continue
            num_cell = (row[0] or "").strip()
            name_cell = (row[1] or "").strip().replace("\n", " ")
            # 第 0 列必须是正整数（OA 编号列）
            num_match = re.match(r"^\s*(\d{1,3})\s*$", num_cell)
            if not num_match:
                continue
            n = int(num_match.group(1))
            clean_no = _match_patent(name_cell)
            if clean_no and clean_no not in seen:
                seen.add(clean_no)
                patent_list.append((f"D{n}", clean_no))
            else:
                skipped_list.append((n, name_cell))
        return patent_list, skipped_list, True

    return [], [], False


# ============================================================
#  路径 b: 启发式行分组 —— 基于纯文本
# ============================================================
def _parse_via_line_grouping(text):
    """
    在 page.get_text() 的纯文本上，识别「编号 N 独占一行 + 后续是该行内容 + 下一个 N」
    的序列。返回 (patent_list, skipped_list, hit)。
    """
    if not text:
        return [], [], False

    # 定位对比文件表所在区段
    anchors = ["本通知书引用下列对比文件", "文件号或名称", "对比文件"]
    start = -1
    for a in anchors:
        idx = text.find(a)
        if idx >= 0:
            start = idx
            break
    segment = text[start:] if start >= 0 else text

    lines = [ln.strip() for ln in segment.splitlines()]
    # 丢弃日期行和空行干扰
    cleaned = []
    for ln in lines:
        if not ln:
            continue
        if _DATE_RE.match(ln):
            continue
        cleaned.append(ln)

    # 扫描：编号行（独占一个正整数）+ 该编号后续的内容行（在下个编号前）
    groups = []  # list[(n, content_text)]
    current_n = None
    current_buf = []
    for ln in cleaned:
        if re.match(r"^\d{1,3}$", ln):
            n = int(ln)
            # 合理性约束：1-99，且严格递增（避免把正文里的数字误判为编号）
            if 1 <= n <= 99 and (not groups or n > groups[-1][0] or current_n is None):
                if current_n is not None:
                    groups.append((current_n, " ".join(current_buf).strip()))
                current_n = n
                current_buf = []
                continue
        if current_n is not None:
            current_buf.append(ln)
    if current_n is not None:
        groups.append((current_n, " ".join(current_buf).strip()))

    if not groups:
        return [], [], False

    patent_list = []
    skipped_list = []
    seen = set()
    for n, content in groups:
        clean_no = _match_patent(content)
        if clean_no and clean_no not in seen:
            seen.add(clean_no)
            patent_list.append((f"D{n}", clean_no))
        else:
            skipped_list.append((n, content))
    return patent_list, skipped_list, True


# ============================================================
#  路径 c: 终极回退 —— 旧行为，全文 finditer，从 D1 顺序编号
# ============================================================
def _parse_via_flat_regex(text):
    """老逻辑：在全文上 finditer 抓所有专利号，按出现顺序 D1, D2, ... 编号。"""
    seen = set()
    ordered = []
    for m in _PATENT_RE.finditer(text):
        clean = re.sub(r"\s+", "", m.group(0).upper())
        if clean not in seen:
            seen.add(clean)
            ordered.append(clean)
    return [(f"D{i}", pn) for i, pn in enumerate(ordered, start=1)]


# ============================================================
#  对外入口
# ============================================================
def extract_comparison_files(pdf_path):
    """
    返回 (patent_list, skipped_list, warning_msg)：
      patent_list: [("D2", "CN115183638A"), ...]，D 标号 = OA 编号，可有缺口
      skipped_list: [(1, "15kV/100kA 冲击大电流系统设计"), ...]
      warning_msg: 若落到终极回退路径返回提示字符串，否则 ""
    """
    # 主路径：基于 PyMuPDF 表格 API
    try:
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            patent_list, skipped_list, hit = _parse_via_find_tables(page)
            if hit:
                doc.close()
                return patent_list, skipped_list, ""
            text = page.get_text()
            doc.close()
        else:
            text = ""
    except Exception as e:
        print(f"读取 PDF 出错: {e}")
        text = extract_text_from_first_page(pdf_path)

    # 回退路径 b：启发式行分组
    patent_list, skipped_list, hit = _parse_via_line_grouping(text)
    if hit:
        return patent_list, skipped_list, ""

    # 终极回退 c：旧行为
    patent_list = _parse_via_flat_regex(text)
    if patent_list:
        return (
            patent_list,
            [],
            "⚠️ 未能解析对比文件表格结构，已按出现顺序编号，可能与 OA 编号不一致。",
        )
    return [], [], ""


# 旧函数保留 thin wrapper，避免误调用别处出错
def extract_patent_numbers(text):
    """已废弃：保留是为了兼容外部直接 import。仅走终极回退路径。"""
    return _parse_via_flat_regex(text)


def process_office_action(pdf_path):
    """
    返回: (success, app_number_or_none, patent_list_or_error_msg, skipped_list)
      app_number: 申请号（纯数字字符串）或 None
      patent_list: [("D2", "CN..."), ...] 或 错误信息字符串
      skipped_list: [(编号, 原文本), ...]，列举非专利对比文件
    """
    print(f"开始解析: {os.path.basename(pdf_path)}")
    text = extract_text_from_first_page(pdf_path)
    if not text.strip():
        return False, None, "提取文本为空或失败，可能是扫描件。", []

    app_number = extract_application_number(text)
    patents, skipped, warning = extract_comparison_files(pdf_path)

    # warning 经由 patent_list 后附加？为保持现有调用方接口，warning 拼到日志侧——这里我们
    # 通过把 warning 塞进 skipped 的前面作为伪记录会破坏语义；改为通过一个 None 触发的副渠道：
    # 直接在 patent_list 为非空时不返回 warning（GUI 已显示对比文件清单了），
    # 而在 patent_list 为空且有 warning 时把 warning 当作错误信息返回（更显眼）。
    if not patents and not app_number:
        msg = warning or "未在第一页找到申请号或对比文件专利号。"
        return False, None, msg, skipped

    # 把 warning 放进 skipped 之前作为编号 0 的特殊提示，便于上层统一日志展示
    if warning:
        skipped = [(0, warning)] + skipped

    return True, app_number, patents, skipped
