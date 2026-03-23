import os
import threading
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from extractor import process_office_action
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
        self.geometry("800x650")
        self.pdf_path = None  # 用户拖入的审查意见通知书路径
        
        # ===== 顶部标题 =====
        self.label_title = ctk.CTkLabel(self, text="专利对比文件自动下载工具",
                                         font=("Microsoft YaHei", 22, "bold"))
        self.label_title.pack(pady=(15, 5))

        self.label_subtitle = ctk.CTkLabel(self, text="自动提取对比文件专利号并从 Google Patents 下载全文",
                                            font=("Microsoft YaHei", 13), text_color="gray")
        self.label_subtitle.pack(pady=(0, 10))

        # ===== 中间两列区域 =====
        self.mid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mid_frame.pack(pady=5, padx=20, fill="x")
        self.mid_frame.columnconfigure(0, weight=1)
        self.mid_frame.columnconfigure(1, weight=1)

        # --- 左列: 手动输入申请文件公开号 ---
        self.left_frame = ctk.CTkFrame(self.mid_frame, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(self.left_frame, text="申请文件公开号",
                     font=("Microsoft YaHei", 14, "bold")).pack(pady=(12, 4))
        ctk.CTkLabel(self.left_frame, text="（选填）手动输入本申请的公开号\n例如: CN116123456A",
                     font=("Microsoft YaHei", 11), text_color="gray").pack(pady=(0, 6))

        self.entry_pub_number = ctk.CTkEntry(self.left_frame, width=260, height=40,
                                              placeholder_text="输入公开号，如 CN116123456A",
                                              font=("Consolas", 14))
        self.entry_pub_number.pack(pady=(0, 12), padx=15)

        # --- 右列: 拖拽上传审查意见通知书 ---
        self.right_frame = ctk.CTkFrame(self.mid_frame, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(self.right_frame, text="审查意见通知书",
                     font=("Microsoft YaHei", 14, "bold")).pack(pady=(12, 4))
        ctk.CTkLabel(self.right_frame, text="（选填）拖拽 PDF 或点击选择",
                     font=("Microsoft YaHei", 11), text_color="gray").pack(pady=(0, 6))

        self.drop_area = ctk.CTkFrame(self.right_frame, height=50, corner_radius=8,
                                       border_width=2, border_color="gray")
        self.drop_area.pack(pady=(0, 12), padx=15, fill="x")
        self.drop_area.pack_propagate(False)

        self.label_drop = ctk.CTkLabel(self.drop_area, text="将 PDF 拖拽到这里",
                                        font=("Microsoft YaHei", 13, "bold"), text_color="gray",
                                        cursor="hand2")
        self.label_drop.pack(expand=True)
        self.label_drop.bind("<Button-1>", self.on_click_select)

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        # ===== 保存目录选择行 =====
        self.dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_frame.pack(pady=(8, 2), padx=20, fill="x")

        ctk.CTkLabel(self.dir_frame, text="保存目录:",
                     font=("Microsoft YaHei", 12)).pack(side="left", padx=(0, 5))
        self.label_save_dir = ctk.CTkLabel(self.dir_frame, text="（自动使用审查意见通知书所在目录）",
                                            font=("Microsoft YaHei", 11), text_color="gray")
        self.label_save_dir.pack(side="left", fill="x", expand=True)

        # ===== 开始下载按钮 =====
        self.btn_download = ctk.CTkButton(self, text="🚀 开始下载", font=("Microsoft YaHei", 16, "bold"),
                                           height=45, corner_radius=10,
                                           command=self.on_start_download)
        self.btn_download.pack(pady=12, padx=80, fill="x")

        # ===== 进度条 =====
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self, variable=self.progress_var, width=650)
        self.progress_bar.pack(pady=(5, 8), padx=20, fill="x")
        self.progress_bar.set(0)

        # ===== 日志区域 =====
        self.textbox_log = ctk.CTkTextbox(self, height=180, state="disabled",
                                           font=("Consolas", 12))
        self.textbox_log.pack(pady=(0, 10), padx=20, fill="both", expand=True)

    def log(self, text):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", text + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        if not files:
            return
        file_path = files[0]
        if not file_path.lower().endswith(".pdf"):
            self.log("错误：请拖入 PDF 文件！")
            return
        self.pdf_path = file_path
        self.label_drop.configure(text=f"✅ {os.path.basename(file_path)}", text_color="green")
        self.label_save_dir.configure(text=os.path.dirname(file_path))
        self.log(f"已选择文件: {os.path.basename(file_path)}")

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

    def on_start_download(self):
        pub_number = self.entry_pub_number.get().strip()
        pdf_path = self.pdf_path

        if not pub_number and not pdf_path:
            messagebox.showwarning("提示", "请至少：\n- 输入申请文件公开号\n- 或拖入审查意见通知书 PDF")
            return

        # 确定保存目录
        if pdf_path:
            save_dir = os.path.dirname(pdf_path)
        else:
            save_dir = filedialog.askdirectory(title="请选择下载文件的保存目录")
            if not save_dir:
                return
            self.label_save_dir.configure(text=save_dir)

        self.btn_download.configure(state="disabled", text="⏳ 正在下载...")
        self.progress_bar.set(0.1)

        threading.Thread(target=self.process_all,
                         args=(pub_number, pdf_path, save_dir),
                         daemon=True).start()

    def process_all(self, pub_number, pdf_path, save_dir):
        all_downloads = []  # [(label, patent_number), ...]

        # 1. 如果用户输入了申请文件公开号
        if pub_number:
            # 清洗：去空格，统一大写
            pub_number = pub_number.upper().replace(" ", "")
            all_downloads.append(("申请文件", pub_number))
            self.log(f">> 申请文件公开号: {pub_number}")

        # 2. 如果上传了审查意见通知书，解析对比文件
        if pdf_path:
            self.log(">> 正在解析审查意见通知书 PDF 第一页...")
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
            self.btn_download.configure(state="normal", text="🚀 开始下载")
            self.progress_bar.set(0)
            return

        self.progress_bar.set(0.3)
        total = len(all_downloads)
        self.log(f"\n>> 共 {total} 个文件待下载，正在初始化下载器...")
        self.log("（初次启动可能需要下载 WebDriver，请耐心等待）")

        success_count = process_downloads(all_downloads, save_dir, log_callback=self.log)

        self.progress_bar.set(1.0)
        self.log(f"\n===== 任务完成 =====")
        self.log(f"共需下载 {total} 个文件，成功 {success_count} 个")
        self.log(f"文件保存在: {save_dir}")

        self.btn_download.configure(state="normal", text="🚀 开始下载")
        self.after(0, lambda: messagebox.showinfo("完成",
            f"任务已完成！\n成功下载 {success_count}/{total} 个文件。\n保存位置: {save_dir}"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
