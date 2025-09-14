import os, sys

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource (works in dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        # running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # running in normal Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
