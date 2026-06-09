"""链路2（VPS 中转）本地配置读写。

配置存于 %APPDATA%\\PatentsDown\\link_config.json（不进 Git 仓库，避免暴露 VPS）。
回退到 exe / 脚本同目录（无 APPDATA 的环境）。
"""
import json
import os
import sys

APP_DIR_NAME = "PatentsDown"
CONFIG_FILENAME = "link_config.json"


def _config_dir():
    base = os.environ.get("APPDATA")
    if base:
        return os.path.join(base, APP_DIR_NAME)
    # 回退：打包后用 exe 同目录，源码用脚本同目录
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.path.join(_config_dir(), CONFIG_FILENAME)


def load():
    """返回 {"base_url": "...", "token": "..."}；读不到 / 格式异常返回空 dict。"""
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {
                "base_url": str(data.get("base_url", "")).strip(),
                "token": str(data.get("token", "")).strip(),
            }
    except (OSError, ValueError):
        pass
    return {}


def save(base_url, token):
    """写入配置（自动创建目录）。"""
    target_dir = _config_dir()
    os.makedirs(target_dir, exist_ok=True)
    payload = {
        "base_url": (base_url or "").strip(),
        "token": (token or "").strip(),
    }
    with open(config_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def is_configured():
    """base_url 与 token 均非空才算配置完成。"""
    cfg = load()
    return bool(cfg.get("base_url")) and bool(cfg.get("token"))
