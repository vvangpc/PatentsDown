import os
import subprocess
import sys
import customtkinter
import tkinterdnd2

def get_resource_path():
    # 获取 customtkinter 路径
    ctk_path = os.path.dirname(customtkinter.__file__)
    # 获取 tkinterdnd2 路径
    tkdnd_path = os.path.dirname(tkinterdnd2.__file__)
    
    # 构造 PyInstaller add-data 参数
    # 注意: Windows 下使用 ; 分隔，Linux 下使用 : 分隔
    separator = ";" if os.name == "nt" else ":"
    
    # customtkinter 的主题文件夹
    ctk_data = f"{ctk_path}{os.sep}assets{os.sep}themes{separator}customtkinter/assets/themes"
    if not os.path.exists(os.path.join(ctk_path, "assets", "themes")):
        # 兼容旧版本
        ctk_data = f"{ctk_path}{os.sep}themes{separator}customtkinter/themes"

    # tkinterdnd2 的驱动文件夹 (必须要带上，否则 DND 功能不生效)
    tkdnd_data = f"{tkdnd_path}{os.sep}tkdnd{separator}tkinterdnd2/tkdnd"
    
    return ctk_data, tkdnd_data

def build():
    ctk_data, tkdnd_data = get_resource_path()
    
    cmd = [
        "pyinstaller",
        "--onefile",           # 单文件模式
        "--noconsole",         # 不显示终端窗口
        "--icon=icon.ico",     # 设置打包后应用程序的桌面图标
        "--clean",             # 构建前清理
        "--name", "专利附件下载器_v2.2",  # EXE 名称
        "--add-data", ctk_data,
        "--add-data", tkdnd_data,
        "main.py"
    ]
    
    print("正在启动打包程序...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\nSuccess! Generated EXE is in 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nFailed: {e}")

if __name__ == "__main__":
    build()
