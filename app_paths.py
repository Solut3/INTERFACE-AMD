import os
import sys
import platform


APP_NAME = "INTERFACE-AMD"


def resource_path(relative_path: str) -> str:
    """
    Resolve caminho para assets tanto em modo dev quanto empacotado (PyInstaller).
    """
    base_dir = getattr(sys, "_MEIPASS", None)
    if base_dir:
        return os.path.join(base_dir, relative_path)
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)


def data_dir() -> str:
    """
    Pasta gravável para config/perfis (Windows/Linux).
    - Windows: %APPDATA%\\INTERFACE-AMD
    - Linux:   ~/.config/INTERFACE-AMD
    """
    if platform.system().lower() == "windows":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(root, APP_NAME)
    else:
        path = os.path.join(os.path.expanduser("~/.config"), APP_NAME)

    os.makedirs(path, exist_ok=True)
    return path


def config_path(filename: str) -> str:
    return os.path.join(data_dir(), filename)

