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

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except Exception as e:
    # Friendly warning; fallback to builtin tkinter
    print("Warning: customtkinter not installed or failed to import. Falling back to tkinter. (Install with `pip install customtkinter` for the modern UI.)")
    CTK_AVAILABLE = False

class FTPClient:
    def __init__(self):
        self.ftp = None
        self.speed = 0.0
        self.connected = False

    def connect(self, host, user, password, port=21, timeout=30, passive=True):
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=timeout)
        ftp.login(user, password)
        ftp.set_pasv(passive)
        self.ftp = ftp
        self.connected = True

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                try:
                    self.ftp.close()
                except:
                    pass
            self.ftp = None
        self.connected = False

    def cwd(self, path):
        if not self.ftp:
            raise RuntimeError("Not connected")
        self.ftp.cwd(path)

    def pwd(self):
        if not self.ftp:
            return "/"
        return self.ftp.pwd()

    def nlst(self, path=None):
        if not self.ftp:
            return []
        return self.ftp.nlst(path) if path else self.ftp.nlst()

    def size(self, remote):
        if not self.ftp:
            return 0
        try:
            return self.ftp.size(remote)
        except Exception:
            return 0

    def retrbinary_to_fd(self, remote, fd, progress_callback=None, chunk_size=8192):
        total = self.size(remote)
        received = 0
        last_time = time.time()
        last_bytes = 0

        def handler(data):
            nonlocal received, last_time, last_bytes
            fd.write(data)
            received += len(data)
            now = time.time()
            if now - last_time >= 1:
                speed = (received - last_bytes) / (now - last_time)
                last_bytes = received
                last_time = now
                self.speed = speed
            else:
                speed = getattr(self, "speed", 0.0)
            if progress_callback:
                progress_callback(received, total, speed)

        if not self.ftp:
            raise RuntimeError("Not connected")
        self.ftp.retrbinary(f"RETR {remote}", handler, blocksize=chunk_size)

    def storbinary_from_fd(self, remote, fd, progress_callback=None, chunk_size=8192):
        fd.seek(0, os.SEEK_END)
        total = fd.tell()
        fd.seek(0)
        sent = 0
        last_time = time.time()
        last_bytes = 0

        def callback(chunk):
            nonlocal sent, last_time, last_bytes
            sent += len(chunk)
            now = time.time()
            if now - last_time >= 1:
                speed = (sent - last_bytes) / (now - last_time)
                last_bytes = sent
                last_time = now
                self.speed = speed
            else:
                speed = getattr(self, "speed", 0.0)
            if progress_callback:
                progress_callback(sent, total, speed)

        if not self.ftp:
            raise RuntimeError("Not connected")
        self.ftp.storbinary(f"STOR {remote}", fd, blocksize=chunk_size, callback=lambda b: callback(b))
