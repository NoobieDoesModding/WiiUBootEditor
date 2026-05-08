import os
import sys
import time
import threading
import tempfile
import json
import ftplib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    print("Warning: Pillow not installed. Image functionality will be limited. Install with `pip install pillow`.")
    PIL_AVAILABLE = False
import xml.etree.ElementTree as ET
import shutil
import colorsys
import urllib.request
import urllib.error
import subprocess
from Info import APP_NAME, VERSION, USER_DIR, USER_CFG, DEFAULT_CFG, UPDATE_LOG
from Locales import LOCALES
from FTP import FTPClient
from Utils import load_cfg, save_cfg, get_locale, convert_to_tga, cfg
from Gui import gui

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except Exception as e:
    # Friendly warning; fallback to builtin tkinter
    print("Warning: customtkinter not installed or failed to import. Falling back to tkinter. (Install with `pip install customtkinter` for the modern UI.)")
    CTK_AVAILABLE = False

# ---------------------------
# Utilities
# ---------------------------
def human_size(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ---------------------------
# FTP wrapper
# ---------------------------

# ---------------------------
# Main Application (CustomTkinter)
# ---------------------------

# ---------------------------
# Entry point bootstrap (fixed)
# ---------------------------
def main():
    """
    Initialize the UI. This main() handles a clean fallback when customtkinter
    is available but fails to initialize.
    """
    global CTK_AVAILABLE

    if CTK_AVAILABLE:
        try:
            # Best-effort apply saved appearance
            try:
                ctk.set_appearance_mode(cfg.get("appearance", "Dark"))
            except Exception:
                pass
            try:
                ctk.set_default_color_theme(cfg.get("accent", "blue"))
            except Exception:
                pass
            root = ctk.CTk()
        except Exception as e:
            # If CTk fails at runtime (rare), fall back
            print("Failed to initialize customtkinter. Falling back to tkinter:", e)
            CTK_AVAILABLE = False
            root = tk.Tk()
    else:
        root = tk.Tk()

    # Try to set window icon
    icon_path = cfg.get("icon_path", "") or ""
    if icon_path and os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = gui(root)
    root.mainloop()

if __name__ == "__main__":
    main()