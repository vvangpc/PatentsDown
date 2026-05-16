import os
import sys
import threading
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
import re
from extractor import process_office_action, extract_text_from_first_page, extract_application_number
from downloader import process_downloads
from tkinter import messagebox, filedialog


APP_NAME = "专利文件下载器"
APP_VERSION = "v3.0"

PRIMARY = "#1976D2"
PRIMARY_HOVER = "#1565C0"
PRIMARY_DARK = "#0D47A1"
PRIMARY_LIGHT = "#5B9BD5"
PRIMARY_LIGHT_DARK = "#4A8BC2"
ACCENT_TEXT = ("#1976D2", "#7BB8E8")
MUTED_TEXT = ("gray50", "gray60")
SUBTLE_TEXT = ("gray45", "gray65")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class App(Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("800x660")
        self.minsize(700, 580)
        self.pdf_path = None
        self.manual_save_dir = None
        self.mode2_entries = []  # list[(row_frame, entry, label)]

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._build_header()
        self._build_tabs()
        self._build_shared_area()

    # ============================================================
    #  顶部标题
    # ============================================================
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(10, 4), padx=20, fill="x")

        self.label_title = ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=("Microsoft YaHei", 24, "bold"),
        )
        self.label_title.pack(anchor="center")

        self.label_subtitle = ctk.CTkLabel(
            header,
            text="智能识别 · 手动输入 · 从 Google Patents 自动下载",
            font=("Microsoft YaHei", 14),
            text_color=MUTED_TEXT,
        )
        self.label_subtitle.pack(anchor="center", pady=(2, 0))

    # ============================================================
    #  标签页（Mode 1 / Mode 2）
    # ============================================================
    def _build_tabs(self):
        # 用固定高度的 wrapper 锁住 tabview 整体尺寸，
        # 防止切换 Tab 时被内容撑大导致下方控件抖动
        tab_container = ctk.CTkFrame(self, height=220, fg_color="transparent")
        tab_container.pack(pady=(4, 6), padx=20, fill="x")
        tab_container.pack_propagate(False)

        self.tabview = ctk.CTkTabview(
            tab_container,
            corner_radius=12,
            segmented_button_selected_color=PRIMARY,
            segmented_button_selected_hover_color=PRIMARY_HOVER,
            segmented_button_unselected_hover_color=("gray80", "gray28"),
            segmented_button_fg_color=("gray85", "gray25"),
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_mode1 = self.tabview.add("📄  模式一 · 智能识别")
        self.tab_mode2 = self.tabview.add("✍️  模式二 · 手动输入")

        self._build_mode1(self.tab_mode1)
        self._build_mode2(self.tab_mode2)

    # ============================================================
    #  模式一：申请文件公开号 + 审查意见 PDF 拖拽
    # ============================================================
    def _build_mode1(self, parent):
        # 先创建并 pack 底部条（仅提示文字），确保它固定在底部不被上方内容挤掉
        bottom_bar = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_bar.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            bottom_bar,
            text="💡 拖入 PDF 自动识别对比文件",
            font=("Microsoft YaHei", 13),
            text_color=SUBTLE_TEXT,
        ).pack(side="left")

        # 上方主体（不纵向 expand，避免列底部出现灰色空白）
        mid = ctk.CTkFrame(parent, fg_color="transparent")
        mid.pack(side="top", pady=(4, 0), padx=10, fill="x")
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)
        mid.rowconfigure(0, weight=1)

        # --- 左列：申请文件公开号 + 自动识别的申请号 ---
        left = ctk.CTkFrame(mid, corner_radius=10)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            left,
            text="申请文件公开号",
            font=("Microsoft YaHei", 15, "bold"),
        ).pack(pady=(8, 4))

        self.entry_pub_number = ctk.CTkEntry(
            left,
            height=38,
            placeholder_text="（选填）例如: CN116123456A",
            font=("Consolas", 15),
            corner_radius=8,
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
        )
        self.entry_pub_number.pack(pady=(0, 6), padx=12, fill="x")

        self.app_number_box = ctk.CTkFrame(
            left,
            height=34,
            corner_radius=8,
            border_width=1,
            border_color=("gray75", "gray35"),
            fg_color=("gray93", "gray20"),
        )
        self.app_number_box.pack(pady=(0, 8), padx=12, fill="x")
        self.app_number_box.pack_propagate(False)

        self.label_app_number = ctk.CTkLabel(
            self.app_number_box,
            text="申请号（自动识别）",
            font=("Consolas", 14),
            text_color=("gray60", "gray50"),
            cursor="hand2",
        )
        self.label_app_number.pack(expand=True)
        self.label_app_number.bind("<Button-1>", self._copy_app_number)

        # --- 右列：审查意见通知书拖拽区 ---
        right = ctk.CTkFrame(mid, corner_radius=10)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            right,
            text="审查意见通知书",
            font=("Microsoft YaHei", 15, "bold"),
        ).pack(pady=(8, 4))

        self.drop_area = ctk.CTkFrame(
            right,
            height=70,
            corner_radius=10,
            border_width=2,
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
            fg_color=("gray95", "gray17"),
        )
        self.drop_area.pack(pady=(0, 8), padx=12, fill="x")
        self.drop_area.pack_propagate(False)

        self.label_drop = ctk.CTkLabel(
            self.drop_area,
            text="📂  （选填）拖拽 PDF 或点击选择",
            font=("Microsoft YaHei", 14),
            text_color=(PRIMARY_LIGHT, "#7BB8E8"),
            cursor="hand2",
        )
        self.label_drop.pack(expand=True)
        self.label_drop.bind("<Button-1>", self.on_click_select)

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.on_drop)
        self.drop_area.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.drop_area.dnd_bind("<<DropLeave>>", self._on_drop_leave)

    # ============================================================
    #  模式二：动态行 — 多个对比文件公开号输入框
    # ============================================================
    def _build_mode2(self, parent):
        # 先 pack 底部条，再 pack 顶部说明与可滚动区域，确保布局稳定
        bottom_bar = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_bar.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

        ctk.CTkButton(
            bottom_bar,
            text="+  添加",
            font=("Microsoft YaHei", 14),
            height=32,
            width=84,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            text_color=ACCENT_TEXT,
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
            hover_color=("gray92", "gray22"),
            command=self._add_mode2_row,
        ).pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="清空全部",
            font=("Microsoft YaHei", 14),
            height=32,
            width=84,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            text_color=("gray45", "gray70"),
            border_color=("gray70", "gray40"),
            hover_color=("gray92", "gray22"),
            command=self._clear_mode2_inputs,
        ).pack(side="left", padx=(8, 0))

        # 顶部说明
        ctk.CTkLabel(
            parent,
            text="逐条输入对比文件公开号（自动按顺序编号为 D1, D2, ...）",
            font=("Microsoft YaHei", 14),
            text_color=SUBTLE_TEXT,
        ).pack(side="top", pady=(4, 2))

        # 中间可滚动 2 列网格：默认 4 项 = 2×2，新增按行优先延伸
        self.mode2_rows_frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=8,
        )
        self.mode2_rows_frame.pack(side="top", padx=12, pady=(0, 2), fill="both", expand=True)
        self.mode2_rows_frame.columnconfigure(0, weight=1, uniform="mode2")
        self.mode2_rows_frame.columnconfigure(1, weight=1, uniform="mode2")

        for _ in range(4):
            self._add_mode2_row()

    def _add_mode2_row(self):
        # row 容器：稍后通过 _relayout_mode2 用 grid 放到 2 列网格中
        row = ctk.CTkFrame(self.mode2_rows_frame, fg_color="transparent")

        idx_label = ctk.CTkLabel(
            row,
            text="",
            width=40,
            font=("Consolas", 15, "bold"),
            text_color=ACCENT_TEXT,
        )
        idx_label.pack(side="left", padx=(2, 4))

        entry = ctk.CTkEntry(
            row,
            height=32,
            placeholder_text="例如: CN115640636A",
            font=("Consolas", 14),
            corner_radius=8,
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
        )
        entry.pack(side="left", padx=(0, 4), fill="x", expand=True)

        btn_remove = ctk.CTkButton(
            row,
            text="✕",
            width=30,
            height=30,
            font=("Microsoft YaHei", 13, "bold"),
            corner_radius=8,
            fg_color=("gray85", "gray30"),
            hover_color=("#E57373", "#B71C1C"),
            text_color=("gray30", "gray80"),
            command=lambda r=row: self._remove_mode2_row(r),
        )
        btn_remove.pack(side="right")

        self.mode2_entries.append((row, entry, idx_label))
        self._relayout_mode2()

    def _remove_mode2_row(self, row):
        if len(self.mode2_entries) <= 1:
            return
        self.mode2_entries = [(r, e, l) for r, e, l in self.mode2_entries if r is not row]
        row.destroy()
        self._relayout_mode2()

    def _relayout_mode2(self):
        """行优先在 2 列网格中重新放置并按 1..n 编号"""
        for i, (frame, _e, lbl) in enumerate(self.mode2_entries):
            lbl.configure(text=f"D{i + 1}")
            frame.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=2)

    def _clear_mode2_inputs(self):
        for _r, entry, _l in self.mode2_entries:
            entry.delete(0, "end")

    # ============================================================
    #  共享底部区域：保存目录 / 进度 / 日志 / 版本号
    # ============================================================
    def _build_shared_area(self):
        # --- 保存目录行（同行包含选择目录 + 开始下载两个按钮） ---
        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.pack(pady=(6, 2), padx=20, fill="x")

        ctk.CTkLabel(
            dir_frame,
            text="保存目录:",
            font=("Microsoft YaHei", 14, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.label_save_dir = ctk.CTkLabel(
            dir_frame,
            text="（模式一自动使用 PDF 所在目录；模式二请点右侧选择）",
            font=("Microsoft YaHei", 13),
            text_color="gray",
            anchor="w",
        )
        self.label_save_dir.pack(side="left", fill="x", expand=True)

        # 右侧两个按钮：先 pack 下载按钮（side="right" 最右），再 pack 选择目录（紧靠下载左侧）
        self.btn_download = ctk.CTkButton(
            dir_frame,
            text="🚀  开始下载",
            font=("Microsoft YaHei", 14, "bold"),
            width=140,
            height=32,
            corner_radius=8,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self.on_start_download,
        )
        self.btn_download.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            dir_frame,
            text="📂  选择目录",
            font=("Microsoft YaHei", 13),
            width=116,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            text_color=ACCENT_TEXT,
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
            hover_color=("gray92", "gray22"),
            command=self._choose_save_dir,
        ).pack(side="right")

        # --- 进度区 ---
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(pady=(6, 2), padx=20, fill="x")

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="就绪",
            font=("Microsoft YaHei", 13),
            text_color=MUTED_TEXT,
        )
        self.progress_label.pack(anchor="w")

        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            progress_color=PRIMARY,
        )
        self.progress_bar.pack(fill="x", pady=(3, 0))
        self.progress_bar.set(0)

        # --- 日志区 ---
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(pady=(4, 0), padx=22, fill="x")

        ctk.CTkLabel(
            log_header,
            text="运行日志",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=MUTED_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="清空",
            font=("Microsoft YaHei", 12),
            width=64,
            height=24,
            corner_radius=6,
            fg_color="transparent",
            border_width=1,
            text_color=("gray45", "gray70"),
            border_color=("gray70", "gray40"),
            hover_color=("gray92", "gray22"),
            command=self._clear_log,
        ).pack(side="right")

        self.textbox_log = ctk.CTkTextbox(
            self,
            height=100,
            state="disabled",
            font=("Consolas", 13),
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        self.textbox_log.pack(pady=(2, 4), padx=20, fill="both", expand=True)

        # --- 底部版本号 ---
        self.footer = ctk.CTkLabel(
            self,
            text=f"{APP_VERSION}  |  PatentsDown",
            font=("Microsoft YaHei", 12),
            text_color=("gray65", "gray45"),
        )
        self.footer.pack(pady=(0, 4))

    # ============================================================
    #  申请号自动识别 + 点击复制
    # ============================================================
    def _extract_and_show_app_number(self, pdf_path):
        text = extract_text_from_first_page(pdf_path)
        if text.strip():
            app_number = extract_application_number(text)
            if app_number:
                clean_number = re.sub(r"[^\dxX]", "", app_number)
                self.label_app_number.configure(
                    text=clean_number,
                    text_color=ACCENT_TEXT,
                )
                self.app_number_box.configure(
                    border_color=(PRIMARY, PRIMARY_LIGHT_DARK),
                    fg_color=("gray96", "gray18"),
                )
                self.log(f"识别到申请号: {clean_number}（点击可复制）")
                return
        self.label_app_number.configure(
            text="未识别到申请号", text_color=("gray60", "gray50")
        )

    def _copy_app_number(self, event=None):
        text = self.label_app_number.cget("text")
        if text and text not in ("申请号（自动识别）", "未识别到申请号"):
            self.clipboard_clear()
            self.clipboard_append(text)
            original_text = text
            self.label_app_number.configure(text="✅ 已复制!", text_color="green")
            self.after(
                1000,
                lambda: self.label_app_number.configure(
                    text=original_text, text_color=ACCENT_TEXT
                ),
            )

    # ============================================================
    #  拖拽视觉反馈
    # ============================================================
    def _on_drop_enter(self, event=None):
        self.drop_area.configure(
            border_color=PRIMARY_DARK, fg_color=("gray90", "gray20")
        )

    def _on_drop_leave(self, event=None):
        self.drop_area.configure(
            border_color=(PRIMARY_LIGHT, PRIMARY_LIGHT_DARK),
            fg_color=("gray95", "gray17"),
        )

    # ============================================================
    #  日志 / 状态工具
    # ============================================================
    def log(self, text):
        def update_ui():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", text + "\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
        self.after(0, update_ui)

    def _clear_log(self):
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")

    def _set_running_state(self, running):
        text = "⏳  正在下载..." if running else "🚀  开始下载"
        state = "disabled" if running else "normal"
        self.btn_download.configure(state=state, text=text)
        if running:
            self.progress_bar.set(0.05)
            self.progress_label.configure(text="正在初始化...")

    # ============================================================
    #  拖拽 / 文件选择
    # ============================================================
    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        if not files:
            return
        file_path = files[0]
        if not file_path.lower().endswith(".pdf"):
            self.log("错误：请拖入 PDF 文件！")
            return
        self.pdf_path = file_path
        self._on_drop_leave()
        self.label_drop.configure(
            text=f"✅  {os.path.basename(file_path)}", text_color="green"
        )
        self.label_save_dir.configure(text=os.path.dirname(file_path))
        self.manual_save_dir = None
        self.log(f"已选择文件: {os.path.basename(file_path)}")
        self._extract_and_show_app_number(file_path)

    def on_click_select(self, event=None):
        file_path = filedialog.askopenfilename(
            title="选择审查意见通知书 PDF",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        if file_path:
            self.pdf_path = file_path
            self.label_drop.configure(
                text=f"✅  {os.path.basename(file_path)}", text_color="green"
            )
            self.label_save_dir.configure(text=os.path.dirname(file_path))
            self.manual_save_dir = None
            self.log(f"已选择文件: {os.path.basename(file_path)}")
            self._extract_and_show_app_number(file_path)

    def _choose_save_dir(self):
        save_dir = filedialog.askdirectory(title="请选择下载文件的保存目录")
        if save_dir:
            self.manual_save_dir = save_dir
            self.label_save_dir.configure(text=save_dir)

    # ============================================================
    #  下载分发：根据当前 Tab 收集下载列表
    # ============================================================
    def on_start_download(self):
        active = self.tabview.get()
        if "模式一" in active:
            download_list = self._collect_mode1()
            require_pdf_or_pub = True
        else:
            download_list = self._collect_mode2()
            require_pdf_or_pub = False

        if not download_list:
            if require_pdf_or_pub:
                messagebox.showwarning(
                    "提示",
                    "请至少：\n- 输入申请文件公开号\n- 或拖入审查意见通知书 PDF",
                )
            else:
                messagebox.showwarning("提示", "请至少输入一个对比文件公开号。")
            return

        save_dir = self._resolve_save_dir()
        if not save_dir:
            return

        self._set_running_state(True)
        threading.Thread(
            target=self._run_downloads,
            args=(download_list, save_dir),
            daemon=True,
        ).start()

    def _collect_mode1(self):
        results = []
        pub_number = self.entry_pub_number.get().strip()
        if pub_number:
            pub_number = pub_number.upper().replace(" ", "")
            results.append(("申请文件", pub_number))
            self.log(f">> 申请文件公开号: {pub_number}")

        if self.pdf_path:
            self.log(">> 正在解析审查意见通知书 PDF 第一页...")
            self.after(0, lambda: self.progress_label.configure(text="正在解析 PDF..."))
            success, _app_number, result = process_office_action(self.pdf_path)
            if success and result:
                display_list = ", ".join([f"{label}-{pn}" for label, pn in result])
                self.log(f"成功识别 {len(result)} 个对比文件: {display_list}")
                results.extend(result)
            else:
                if isinstance(result, str):
                    self.log(f"解析提示: {result}")
                else:
                    self.log("未在 PDF 中识别到对比文件专利号。")
        return results

    def _collect_mode2(self):
        results = []
        for _r, entry, _l in self.mode2_entries:
            raw = entry.get().strip()
            if not raw:
                continue
            cleaned = raw.upper().replace(" ", "")
            results.append((f"D{len(results) + 1}", cleaned))
        if results:
            display_list = ", ".join([f"{label}-{pn}" for label, pn in results])
            self.log(f">> 已收集 {len(results)} 个对比文件: {display_list}")
        return results

    def _resolve_save_dir(self):
        if self.manual_save_dir and os.path.isdir(self.manual_save_dir):
            return self.manual_save_dir
        if self.pdf_path and os.path.isfile(self.pdf_path):
            return os.path.dirname(self.pdf_path)
        save_dir = filedialog.askdirectory(title="请选择下载文件的保存目录")
        if save_dir:
            self.manual_save_dir = save_dir
            self.label_save_dir.configure(text=save_dir)
            return save_dir
        return None

    # ============================================================
    #  后台下载线程
    # ============================================================
    def _run_downloads(self, download_list, save_dir):
        total = len(download_list)
        self.after(0, lambda: self.progress_bar.set(0.15))
        self.after(0, lambda: self.progress_label.configure(text=f"正在下载 (0/{total})..."))
        self.log(f"\n>> 共 {total} 个文件待下载，正在初始化下载器...")
        self.log("（初次启动可能需要下载 WebDriver，请耐心等待）")

        download_count = [0]

        def log_with_progress(text):
            self.log(text)
            if text.startswith("✅") or text.startswith("⏩"):
                download_count[0] += 1
                self.after(
                    0,
                    lambda: self.progress_label.configure(
                        text=f"正在下载 ({download_count[0]}/{total})..."
                    ),
                )
                progress = 0.15 + 0.85 * (download_count[0] / total)
                self.after(0, lambda p=progress: self.progress_bar.set(p))

        success_count = process_downloads(
            download_list, save_dir, log_callback=log_with_progress
        )

        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(
            0,
            lambda: self.progress_label.configure(
                text=f"下载完成 — 成功 {success_count}/{total}"
            ),
        )
        self.log(f"\n===== 任务完成 =====")
        self.log(f"共需下载 {total} 个文件，成功 {success_count} 个")
        self.log(f"文件保存在: {save_dir}")

        failed_count = total - success_count
        if failed_count > 0:
            self.log(f"\n⚠️ 以下 {failed_count} 个文件下载失败，请手动处理：")
            for label, pn in download_list:
                if not os.path.exists(os.path.join(save_dir, f"{label}-{pn}.pdf")):
                    self.log(f"{pn}")

        self.after(0, lambda: self._set_running_state(False))
        self.after(
            0,
            lambda: messagebox.showinfo(
                "完成",
                f"任务已完成！\n成功下载 {success_count}/{total} 个文件。\n保存位置: {save_dir}",
            ),
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
