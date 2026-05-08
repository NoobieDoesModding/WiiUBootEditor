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

APP_NAME = "WiiU Boot Editor"
VERSION = "1.2.0 Pre-Release"
USER_DIR = Path.home() / ".wiiu_boot_editor"
USER_DIR.mkdir(exist_ok=True)
USER_CFG = USER_DIR / "settings.json"

DEFAULT_CFG = {
    "appearance": "Dark",
    "accent": "blue",
    "rainbow": False,
    "language": "English",
    "ftp_port": 21,
    "ftp_passive": True,
    "timeout": 30,
    "icon_path": "",
    "update_url": ""
}

# Update log
UPDATE_LOG = """ver. 1.0:
- FTP Client added
- Base TGA conversion features

ver. 1.1.0 test:
- UI Overhaul
- Better FTP handling
- More UI Customization options
- Placeholder for Models window
- Placeholder for WiiU file reader
- This is a test version, it will not be released to the public.

ver. 1.1.0-experimental:

- FTP UI overhaul
- Future released experiment.
- First public experimental release.

ver. 1.2.0:

- Full structural overhaul, with a better code organization.
- More features to be announced.
- Might be the last version of the tool, except for bug fixes and quality of life improvements.

"""
