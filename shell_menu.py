"""Windows 资源管理器右键菜单注册（HKCU，不需要管理员）

注册位置：HKCU\\Software\\Classes\\SystemFileAssociations\\.pdf\\shell\\PatentsDown
仅对当前用户生效，无需 UAC 弹窗。
"""
import os
import sys

try:
    import winreg
except ImportError:
    winreg = None  # 非 Windows 平台占位

MENU_TEXT = "专利文件下载"
BASE_KEY = r"Software\Classes\SystemFileAssociations\.pdf\shell\PatentsDown"
CMD_KEY = BASE_KEY + r"\command"


def get_exe_path():
    """打包模式返回 exe 完整路径；源码模式返回 None。"""
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return None


def is_registered():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CMD_KEY) as k:
            value, _ = winreg.QueryValueEx(k, None)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def get_registered_command():
    """返回当前注册的命令字符串（用于检测 exe 是否被移动）。"""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CMD_KEY) as k:
            value, _ = winreg.QueryValueEx(k, None)
            return value
    except FileNotFoundError:
        return None
    except OSError:
        return None


def register(exe_path):
    """写入右键菜单注册表项。exe_path 必须是绝对路径。"""
    if winreg is None:
        raise OSError("winreg 不可用，本功能仅支持 Windows")
    exe_path = os.path.abspath(exe_path)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, BASE_KEY) as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, MENU_TEXT)
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, f'"{exe_path}",0')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CMD_KEY) as k:
        winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f'"{exe_path}" "%1"')


def unregister():
    """移除右键菜单注册表项。"""
    if winreg is None:
        return
    for key in (CMD_KEY, BASE_KEY):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except FileNotFoundError:
            pass
        except OSError:
            pass
