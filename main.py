import os
import sys
import threading
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
import re
from extractor import process_office_action, extract_text_from_first_page, extract_application_number
from downloader import process_downloads
from tkinter import messagebox, filedialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class App(Tk):
    def __init__(self):
        super().__init__()

        self.title("专利对比文件自动下载工具")
        self.geometry("820x680")
        self.minsize(700, 580)
        self.pdf_path = None

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # ===== 顶部标题 =====
        self.label_title = ctk.CTkLabel(self, text="专利对比文件自动下载工具",
                                         font=("Microsoft YaHei", 22, "bold"))
        self.label_title.pack(pady=(20, 3))

        self.label_subtitle = ctk.CTkLabel(self, text="自动提取对比文件专利号并从 Google Patents 下载全文",
                                            font=("Microsoft YaHei", 12),
                                            text_color=("gray50", "gray60"))
        self.label_subtitle.pack(pady=(0, 15))

        # ===== 中间两列区域 =====
        self.mid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mid_frame.pack(pady=5, padx=20, fill="x")
        self.mid_frame.columnconfigure(0, weight=1)
        self.mid_frame.columnconfigure(1, weight=1)
        self.mid_frame.rowconfigure(0, weight=1)

        # --- 左列: 手动输入申请文件公开号 ---
        self.left_frame = ctk.CTkFrame(self.mid_frame, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(self.left_frame, text="申请文件公开号",
                     font=("Microsoft YaHei", 13, "bold")).pack(pady=(10, 4))

        self.entry_pub_number = ctk.CTkEntry(self.left_frame, height=38,
                                              placeholder_text="（选填）例如: CN116123456A",
                                              font=("Consolas", 13),
                                              corner_radius=8,
                                              border_color=("#5B9BD5", "#4A8BC2"))
        self.entry_pub_number.pack(pady=(0, 6), padx=12, fill="x")

        # --- 申请号显示框 (从审查意见中自动识别，点击复制) ---
        self.app_number_box = ctk.CTkFrame(self.left_frame, height=34, corner_radius=8,
                                            border_width=1,
                                            border_color=("gray75", "gray35"),
                                            fg_color=("gray93", "gray20"))
        self.app_number_box.pack(pady=(0, 10), padx=12, fill="x")
        self.app_number_box.pack_propagate(False)

        self.label_app_number = ctk.CTkLabel(self.app_number_box,
                                              text="申请号（自动识别）",
                                              font=("Consolas", 12),
                                              text_color=("gray60", "gray50"),
                                              cursor="hand2")
        self.label_app_number.pack(expand=True)
        self.label_app_number.bind("<Button-1>", self._copy_app_number)

        # --- 右列: 拖拽上传审查意见通知书 ---
        self.right_frame = ctk.CTkFrame(self.mid_frame, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(self.right_frame, text="审查意见通知书",
                     font=("Microsoft YaHei", 13, "bold")).pack(pady=(10, 4))

        self.drop_area = ctk.CTkFrame(self.right_frame, height=72, corner_radius=10,
                                       border_width=2, border_color=("#5B9BD5", "#4A8BC2"),
                                       fg_color=("gray95", "gray17"))
        self.drop_area.pack(pady=(0, 10), padx=12, fill="x")
        self.drop_area.pack_propagate(False)

        self.label_drop = ctk.CTkLabel(self.drop_area,
                                        text="📂 （选填）拖拽 PDF 或点击选择",
                                        font=("Microsoft YaHei", 12),
                                        text_color=("#5B9BD5", "#7BB8E8"),
                                        cursor="hand2")
        self.label_drop.pack(expand=True)
        self.label_drop.bind("<Button-1>", self.on_click_select)

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_area.dnd_bind('<<DropEnter>>', self._on_drop_enter)
        self.drop_area.dnd_bind('<<DropLeave>>', self._on_drop_leave)

        # ===== 保存目录选择行 =====
        self.dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_frame.pack(pady=(8, 2), padx=20, fill="x")

        ctk.CTkLabel(self.dir_frame, text="保存目录:",
                     font=("Microsoft YaHei", 12)).pack(side="left", padx=(0, 5))
        self.label_save_dir = ctk.CTkLabel(self.dir_frame, text="（自动使用审查意见通知书所在目录）",
                                            font=("Microsoft YaHei", 11), text_color="gray")
        self.label_save_dir.pack(side="left", fill="x", expand=True)

        # ===== 分隔线 =====
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray30")).pack(
            pady=(8, 0), padx=30, fill="x")

        # ===== 开始下载按钮 =====
        self.btn_download = ctk.CTkButton(self, text="🚀  开始下载",
                                           font=("Microsoft YaHei", 16, "bold"),
                                           height=48, corner_radius=12,
                                           fg_color="#1976D2", hover_color="#1565C0",
                                           command=self.on_start_download)
        self.btn_download.pack(pady=(14, 10), padx=60, fill="x")

        # ===== 进度条区域 =====
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=(2, 2), padx=20, fill="x")

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="就绪",
                                            font=("Microsoft YaHei", 11),
                                            text_color=("gray50", "gray60"))
        self.progress_label.pack(anchor="w")

        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, variable=self.progress_var)
        self.progress_bar.pack(fill="x", pady=(2, 0))
        self.progress_bar.set(0)

        # ===== 日志区域 =====
        self.log_label = ctk.CTkLabel(self, text="运行日志",
                                       font=("Microsoft YaHei", 11, "bold"),
                                       text_color=("gray50", "gray60"),
                                       anchor="w")
        self.log_label.pack(pady=(6, 0), padx=22, anchor="w")

        self.textbox_log = ctk.CTkTextbox(self, height=180, state="disabled",
                                           font=("Consolas", 11),
                                           corner_radius=8,
                                           border_width=1,
                                           border_color=("gray80", "gray30"))
        self.textbox_log.pack(pady=(2, 6), padx=20, fill="both", expand=True)

        # ===== 底部版本信息 =====
        self.footer = ctk.CTkLabel(self, text="v2.1  |  PatentsDown",
                                    font=("Microsoft YaHei", 10),
                                    text_color=("gray65", "gray45"))
        self.footer.pack(pady=(0, 6))

    # ===== 申请号提取与复制 =====
    def _extract_and_show_app_number(self, pdf_path):
        """从审查意见 PDF 中提取申请号并显示"""
        text = extract_text_from_first_page(pdf_path)
        if text.strip():
            app_number = extract_application_number(text)
            if app_number:
                # 只保留数字和 x/X
                clean_number = re.sub(r'[^\dxX]', '', app_number)
                self.label_app_number.configure(
                    text=clean_number,
                    text_color=("#1976D2", "#7BB8E8"))
                self.app_number_box.configure(
                    border_color=("#1976D2", "#4A8BC2"),
                    fg_color=("gray96", "gray18"))
                self.log(f"识别到申请号: {clean_number}（点击可复制）")
                return
        self.label_app_number.configure(text="未识别到申请号", text_color=("gray60", "gray50"))

    def _copy_app_number(self, event=None):
        """点击复制申请号到剪贴板"""
        text = self.label_app_number.cget("text")
        if text and text not in ("上传审查意见后自动显示", "未识别到申请号"):
            self.clipboard_clear()
            self.clipboard_append(text)
            # 短暂反馈
            original_text = text
            self.label_app_number.configure(text="✅ 已复制!", text_color="green")
            self.after(1000, lambda: self.label_app_number.configure(
                text=original_text, text_color=("#1976D2", "#7BB8E8")))

    # ===== 拖拽悬停效果 =====
    def _on_drop_enter(self, event=None):
        self.drop_area.configure(border_color="#2E7D32", fg_color=("gray90", "gray20"))

    def _on_drop_leave(self, event=None):
        self.drop_area.configure(border_color=("#5B9BD5", "#4A8BC2"),
                                  fg_color=("gray95", "gray17"))

    def log(self, text):
        def update_ui():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", text + "\n")
            self.textbox_log.see("end")
            self.textbox_log.configure(state="disabled")
        self.after(0, update_ui)

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
        self.label_drop.configure(text=f"✅ {os.path.basename(file_path)}", text_color="green")
        self.label_save_dir.configure(text=os.path.dirname(file_path))
        self.log(f"已选择文件: {os.path.basename(file_path)}")
        self._extract_and_show_app_number(file_path)

    def on_click_select(self, event=None):
        file_path = filedialog.askopenfilename(
            title="选择审查意见通知书 PDF",
            filetypes=[("PDF 文件", "*.pdf")]
        )
        if file_path:
            self.pdf_path = file_path
            self.label_drop.configure(text=f"✅ {os.path.basename(file_path)}",
                                       text_color="green")
            self.label_save_dir.configure(text=os.path.dirname(file_path))
            self.log(f"已选择文件: {os.path.basename(file_path)}")
            self._extract_and_show_app_number(file_path)

    def on_start_download(self):
        pub_number = self.entry_pub_number.get().strip()
        pdf_path = self.pdf_path

        if not pub_number and not pdf_path:
            messagebox.showwarning("提示", "请至少：\n- 输入申请文件公开号\n- 或拖入审查意见通知书 PDF")
            return

        if pdf_path:
            save_dir = os.path.dirname(pdf_path)
        else:
            save_dir = filedialog.askdirectory(title="请选择下载文件的保存目录")
            if not save_dir:
                return
            self.label_save_dir.configure(text=save_dir)

        self.after(0, lambda: self.btn_download.configure(state="disabled", text="⏳ 正在下载..."))
        self.after(0, lambda: self.progress_bar.set(0.1))
        self.after(0, lambda: self.progress_label.configure(text="正在初始化..."))

        threading.Thread(target=self.process_all,
                         args=(pub_number, pdf_path, save_dir),
                         daemon=True).start()

    def process_all(self, pub_number, pdf_path, save_dir):
        all_downloads = []

        if pub_number:
            pub_number = pub_number.upper().replace(" ", "")
            all_downloads.append(("申请文件", pub_number))
            self.log(f">> 申请文件公开号: {pub_number}")

        if pdf_path:
            self.log(">> 正在解析审查意见通知书 PDF 第一页...")
            self.after(0, lambda: self.progress_label.configure(text="正在解析 PDF..."))
            success, _app_number, result = process_office_action(pdf_path)

            if success and result:
                display_list = ', '.join([f"{label}-{pn}" for label, pn in result])
                self.log(f"成功识别 {len(result)} 个对比文件: {display_list}")
                all_downloads.extend(result)
            else:
                if isinstance(result, str):
                    self.log(f"解析提示: {result}")
                else:
                    self.log("未在 PDF 中识别到对比文件专利号。")

        if not all_downloads:
            self.log("没有需要下载的文件。")
            self.after(0, lambda: self.btn_download.configure(state="normal", text="🚀  开始下载"))
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, lambda: self.progress_label.configure(text="就绪"))
            return

        self.after(0, lambda: self.progress_bar.set(0.3))
        total = len(all_downloads)
        self.after(0, lambda: self.progress_label.configure(text=f"正在下载 (0/{total})..."))
        self.log(f"\n>> 共 {total} 个文件待下载，正在初始化下载器...")
        self.log("（初次启动可能需要下载 WebDriver，请耐心等待）")

        download_count = [0]
        original_log = self.log

        def log_with_progress(text):
            original_log(text)
            if text.startswith("✅") or text.startswith("⏩"):
                download_count[0] += 1
                self.after(0, lambda: self.progress_label.configure(
                    text=f"正在下载 ({download_count[0]}/{total})..."))
                progress = 0.3 + 0.7 * (download_count[0] / total)
                self.after(0, lambda p=progress: self.progress_bar.set(p))

        success_count = process_downloads(all_downloads, save_dir, log_callback=log_with_progress)

        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(0, lambda: self.progress_label.configure(
            text=f"下载完成 — 成功 {success_count}/{total}"))
        self.log(f"\n===== 任务完成 =====")
        self.log(f"共需下载 {total} 个文件，成功 {success_count} 个")
        self.log(f"文件保存在: {save_dir}")

        failed_count = total - success_count
        if failed_count > 0:
            self.log(f"\n⚠️ 以下 {failed_count} 个文件下载失败，请手动处理：")
            for label, pn in all_downloads:
                if not os.path.exists(os.path.join(save_dir, f"{label}-{pn}.pdf")):
                    self.log(f"{pn}")

        self.after(0, lambda: self.btn_download.configure(state="normal", text="🚀  开始下载"))
        self.after(0, lambda: messagebox.showinfo("完成",
            f"任务已完成！\n成功下载 {success_count}/{total} 个文件。\n保存位置: {save_dir}"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
