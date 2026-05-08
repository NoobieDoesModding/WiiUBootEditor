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
from Utils import load_cfg, save_cfg, get_locale, convert_to_tga


try:
    import customtkinter as ctk
    from CTkToolTip import CTkToolTip
    CTK_AVAILABLE = True
except Exception as e:
    # Friendly warning; fallback to builtin tkinter
    print("Warning: customtkinter not installed or failed to import. Falling back to tkinter. (Install with `pip install customtkinter` for the modern UI.)")
    CTK_AVAILABLE = False


class gui:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.ftp = FTPClient()
        self.cfg = load_cfg()
        self.progress_win = None
        self.progress_var = tk.DoubleVar(value=0.0)
        self.speed_var = tk.StringVar(value="")
        self.preview_img_ref = None
        self.current_local_dir = os.path.expanduser("~")
        self.current_remote_dir = "/"

        # rainbow animation params
        self._rainbow_active = load_cfg().get("rainbow", False)
        self._rainbow_h = 0.0
        self._rainbow_job = None

        self.icon_photo = None

        # Setup CTk defaults or warn
        if CTK_AVAILABLE:
            try:
                ctk.set_appearance_mode(self.cfg.get("appearance", "Dark"))
                try:
                    ctk.set_default_color_theme(self.cfg.get("accent", "blue"))
                except Exception:
                    pass
            except Exception:
                # In rare cases setting appearance may fail; fallback gracefully
                print("Warning: customtkinter appearance config failed; continuing with default.")
        else:
            print("Using standard tkinter UI (customtkinter unavailable).")

        # Attempt to set icon
        icon_path = self.cfg.get("icon_path", "") or ""
        if icon_path and os.path.exists(icon_path):
            try:
                if icon_path.lower().endswith('.ico'):
                    self.root.iconbitmap(icon_path)
                else:
                    img = Image.open(icon_path)
                    img = img.resize((32, 32), Image.LANCZOS)
                    self.icon_photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(True, self.icon_photo)
            except Exception:
                pass

        # maximize (best-effort)
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass

        self._build_ui()
        # apply language
        self.apply_language()
        # start rainbow if enabled
        if self._rainbow_active:
            self.start_rainbow()

    # -------------------------
    # Build UI using CTk if available for modern look
    # -------------------------
    def _build_ui(self):
        # top-level frame
        if CTK_AVAILABLE:
            container = ctk.CTkFrame(self.root, corner_radius=0)
            container.pack(fill="both", expand=True, padx=0, pady=0)
            left_w = ctk.CTkFrame(container, width=260, corner_radius=0)
            left_w.grid(row=0, column=0, padx=(0,0), pady=0, sticky="ns")
            right_w = ctk.CTkFrame(container, corner_radius=0)
            right_w.grid(row=0, column=1, sticky="nsew", pady=0)
        else:
            container = tk.Frame(self.root, bg="#f0f0f0")
            container.pack(fill="both", expand=True, padx=0, pady=0)
            left_w = tk.Frame(container, bg="#eaeaea", width=260)
            left_w.grid(row=0, column=0, padx=(0,0), pady=0, sticky="ns")
            right_w = tk.Frame(container, bg="#ffffff")
            right_w.grid(row=0, column=1, sticky="nsew", pady=0)

        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # ---------- Left panel (controls) ----------
        # Top action buttons
        if CTK_AVAILABLE:
            btn_style = {"corner_radius": 6, "height": 36}
            self.btn_settings = ctk.CTkButton(left_w, text=get_locale()["settings"], command=self.open_settings, **btn_style)
            self.btn_settings.pack(fill="x", pady=(12,6), padx=12)
            CTkToolTip(self.btn_settings, message="Customize appearance, language, and other settings.")
            self.btn_credits = ctk.CTkButton(left_w, text=get_locale()["credits"], command=self.open_credits, **btn_style)
            self.btn_credits.pack(fill="x", pady=6, padx=12)
            CTkToolTip(self.btn_credits, message="View credits and developer information.")
            self.btn_meta = ctk.CTkButton(left_w, text=get_locale()["edit_meta"], command=self.open_local_meta_editor, **btn_style)
            self.btn_meta.pack(fill="x", pady=6, padx=12)
            CTkToolTip(self.btn_meta, message="Edit meta.xml files for Wii U titles.")
            # New: Update Log and About buttons
            self.btn_updatelog = ctk.CTkButton(left_w, text="Update Log", command=self.show_update_log, **btn_style)
            self.btn_updatelog.pack(fill="x", pady=6, padx=12)
            CTkToolTip(self.btn_updatelog, message="View the changelog and update history.")
            self.btn_about = ctk.CTkButton(left_w, text=get_locale().get("about","About / Version"), command=self.open_about, **btn_style)
            self.btn_about.pack(fill="x", pady=6, padx=12)
            CTkToolTip(self.btn_about, message="Check version and update information.")
            ctk.CTkLabel(left_w, text=get_locale()["tga_header"], anchor="w").pack(fill="x", pady=(12,4), padx=12)
            self.btn_import_icon = ctk.CTkButton(left_w, text="Import iconTex (128x128, 32b)", command=lambda: self.import_img((128,128),32), **btn_style)
            self.btn_import_icon.pack(fill="x", pady=4, padx=12)
            CTkToolTip(self.btn_import_icon, message="Import and convert icon image to TGA format.")
            self.btn_import_drc = ctk.CTkButton(left_w, text="Import bootDrcTex (854x480, 24b)", command=lambda: self.import_img((854,480),24), **btn_style)
            self.btn_import_drc.pack(fill="x", pady=4, padx=12)
            CTkToolTip(self.btn_import_drc, message="Import and convert DRC boot image to TGA format.")
            self.btn_import_tv = ctk.CTkButton(left_w, text="Import bootTvTex (1280x720, 24b)", command=lambda: self.import_img((1280,720),24), **btn_style)
            self.btn_import_tv.pack(fill="x", pady=4, padx=12)
            CTkToolTip(self.btn_import_tv, message="Import and convert TV boot image to TGA format.")
            self.btn_import_logo = ctk.CTkButton(left_w, text="Import bootLogoTex (170x42, 32b)", command=lambda: self.import_img((170,42),32), **btn_style)
            self.btn_import_logo.pack(fill="x", pady=4, padx=12)
            CTkToolTip(self.btn_import_logo, message="Import and convert logo image to TGA format.")
            ctk.CTkLabel(left_w, text=get_locale()["ftp_header"], anchor="w").pack(fill="x", pady=(16,4), padx=12)
            self.btn_ftp = ctk.CTkButton(left_w, text="Open FTP Browser", command=self.open_ftp_browser, **btn_style)
            self.btn_ftp.pack(fill="x", pady=(4,12), padx=12)
            CTkToolTip(self.btn_ftp, message="Browse and manage files on Wii U via FTP.")
            # New: WiiU file browser button
            self.btn_wiiu = ctk.CTkButton(left_w, text="Open WiiU files (.szs, .params)", command=self.open_wiiu_files, **btn_style)
            self.btn_wiiu.pack(fill="x", pady=(0,12), padx=12)
            CTkToolTip(self.btn_wiiu, message="Open and edit Wii U boot files.")
            # Models button (new)
            self.btn_models = ctk.CTkButton(left_w, text="Models", command=self.open_models_window, **btn_style)
            self.btn_models.pack(fill="x", pady=(0,12), padx=12)
            CTkToolTip(self.btn_models, message="Manage 3D models for Wii U titles.")
        else:
            self.btn_settings = tk.Button(left_w, text=get_locale()["settings"], command=self.open_settings)
            self.btn_settings.pack(fill="x", pady=(12,6), padx=8)
            self.btn_credits = tk.Button(left_w, text=get_locale()["credits"], command=self.open_credits)
            self.btn_credits.pack(fill="x", pady=6, padx=8)
            self.btn_meta = tk.Button(left_w, text=get_locale()["edit_meta"], command=self.open_local_meta_editor)
            self.btn_meta.pack(fill="x", pady=6, padx=8)
            self.btn_updatelog = tk.Button(left_w, text="Update Log", command=self.show_update_log)
            self.btn_updatelog.pack(fill="x", pady=6, padx=8)
            self.btn_about = tk.Button(left_w, text=get_locale().get("about","About / Version"), command=self.open_about)
            self.btn_about.pack(fill="x", pady=6, padx=8)
            tk.Label(left_w, text=get_locale()["tga_header"], anchor="w").pack(fill="x", pady=(12,4), padx=8)
            tk.Button(left_w, text="Import iconTex (128x128, 32b)", command=lambda: self.import_img((128,128),32)).pack(fill="x", pady=4, padx=8)
            tk.Button(left_w, text="Import bootDrcTex (854x480, 24b)", command=lambda: self.import_img((854,480),24)).pack(fill="x", pady=4, padx=8)
            tk.Button(left_w, text="Import bootTvTex (1280x720, 24b)", command=lambda: self.import_img((1280,720),24)).pack(fill="x", pady=4, padx=8)
            tk.Button(left_w, text="Import bootLogoTex (170x42, 32b)", command=lambda: self.import_img((170,42),32)).pack(fill="x", pady=4, padx=8)
            tk.Label(left_w, text=get_locale()["ftp_header"], anchor="w").pack(fill="x", pady=(16,4), padx=8)
            tk.Button(left_w, text="Open FTP Browser", command=self.open_ftp_browser).pack(fill="x", pady=(4,12), padx=8)
            tk.Button(left_w, text="Open WiiU files (.szs, .params)", command=self.open_wiiu_files).pack(fill="x", pady=(0,12), padx=8)
            tk.Button(left_w, text="Models", command=self.open_models_window).pack(fill="x", pady=(0,12), padx=8)

        # Right panel (main)
        if CTK_AVAILABLE:
            topbar = ctk.CTkFrame(right_w, fg_color="transparent")
            topbar.pack(fill="x", padx=12, pady=(12,6))
            self.status_label = ctk.CTkLabel(topbar, text=f"{APP_NAME} — ready", anchor="w")
            self.status_label.pack(side="left")
            # small accent decorative bar
            self.accent_bar = ctk.CTkFrame(right_w, height=4, corner_radius=2)
            self.accent_bar.pack(fill="x", padx=12, pady=(0,12))
            main_area = ctk.CTkFrame(right_w, corner_radius=8)
            main_area.pack(fill="both", expand=True, padx=12, pady=12)
            self.welcome_label = ctk.CTkLabel(main_area, text=get_locale().get("welcome", "Welcome — use the left panel to select actions (FTP, TGA, meta.xml)."), justify="center")
            self.welcome_label.pack(expand=True, fill="both", padx=24, pady=24)
        else:
            topbar = tk.Frame(right_w, bg="#ffffff")
            topbar.pack(fill="x", padx=8, pady=(8,4))
            self.status_label = tk.Label(topbar, text=f"{APP_NAME} — ready", anchor="w")
            self.status_label.pack(side="left")
            self.accent_bar = tk.Frame(right_w, height=4, bg="#0078d7")
            self.accent_bar.pack(fill="x", padx=8, pady=(0,8))
            main_area = tk.Frame(right_w, bg="#fff")
            main_area.pack(fill="both", expand=True, padx=8, pady=8)
            self.welcome_label = tk.Label(main_area, text=get_locale().get("welcome", "Welcome — use the left panel to select actions (FTP, TGA, meta.xml)."), justify="center")
            self.welcome_label.pack(expand=True, fill="both", padx=12, pady=12)

    # Language application

    def apply_language(self):
        loc = get_locale()
        try:
            if CTK_AVAILABLE:
                self.btn_settings.configure(text=loc["settings"])
                self.btn_credits.configure(text=loc["credits"])
                self.btn_meta.configure(text=loc["edit_meta"])
                self.btn_about.configure(text=loc.get("about","About / Version"))
            else:
                self.btn_settings.configure(text=loc["settings"])
                self.btn_credits.configure(text=loc["credits"])
                self.btn_meta.configure(text=loc["edit_meta"])
                self.btn_about.configure(text=loc.get("about","About / Version"))
            # status updated
            self.status_label.configure(text=f"{APP_NAME} — {loc.get('done','Ready')}")
            self.welcome_label.configure(text=loc.get("welcome", "Welcome — use the left panel to select actions (FTP, TGA, meta.xml)."))
        except Exception:
            pass

    # Rainbow accent animation

    def start_rainbow(self):
        if not CTK_AVAILABLE:
            return
        self._rainbow_active = True
        self._rainbow_step()

    def stop_rainbow(self):
        self._rainbow_active = False
        if self._rainbow_job:
            self.root.after_cancel(self._rainbow_job)
            self._rainbow_job = None
        try:
            ctk.set_default_color_theme(self.cfg.get("accent", "blue"))
        except Exception:
            pass

    def _rainbow_step(self):
        h = self._rainbow_h % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.85, 0.95)
        hexcol = "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
        try:
            self.accent_bar.configure(fg_color=hexcol)
            if CTK_AVAILABLE:
                try:
                    self.btn_settings.configure(fg_color=hexcol)
                    self.btn_credits.configure(fg_color=hexcol)
                    self.btn_meta.configure(fg_color=hexcol)
                except Exception:
                    pass
        except Exception:
            pass

        self._rainbow_h += 0.007
        if self._rainbow_active:
            self._rainbow_job = self.root.after(40, self._rainbow_step)

    def open_ftp_browser(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("600x500")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("600x500")
        win.title("FTP Browser")
        win.transient(self.root)

        # Connection frame
        if CTK_AVAILABLE:
            conn_frame = ctk.CTkFrame(win)
            conn_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(conn_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5)
            host_var = ctk.StringVar(value=self.cfg.get("ftp_host", ""))
            host_entry = ctk.CTkEntry(conn_frame, textvariable=host_var)
            host_entry.grid(row=0, column=1, padx=5, pady=5)
            ctk.CTkLabel(conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
            port_var = ctk.StringVar(value=str(self.cfg.get("ftp_port", 21)))
            port_entry = ctk.CTkEntry(conn_frame, textvariable=port_var, width=60)
            port_entry.grid(row=0, column=3, padx=5, pady=5)
            ctk.CTkLabel(conn_frame, text="User:").grid(row=1, column=0, padx=5, pady=5)
            user_var = ctk.StringVar(value=self.cfg.get("ftp_user", ""))
            user_entry = ctk.CTkEntry(conn_frame, textvariable=user_var)
            user_entry.grid(row=1, column=1, padx=5, pady=5)
            ctk.CTkLabel(conn_frame, text="Password:").grid(row=1, column=2, padx=5, pady=5)
            pass_var = ctk.StringVar()
            pass_entry = ctk.CTkEntry(conn_frame, textvariable=pass_var, show="*")
            pass_entry.grid(row=1, column=3, padx=5, pady=5)
            connect_btn = ctk.CTkButton(conn_frame, text="Connect", command=lambda: self._ftp_connect(win, host_var.get(), user_var.get(), pass_var.get(), int(port_var.get())))
            connect_btn.grid(row=2, column=0, columnspan=4, pady=10)
        else:
            conn_frame = tk.Frame(win)
            conn_frame.pack(fill="x", padx=10, pady=10)
            tk.Label(conn_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5)
            host_var = tk.StringVar(value=self.cfg.get("ftp_host", ""))
            host_entry = tk.Entry(conn_frame, textvariable=host_var)
            host_entry.grid(row=0, column=1, padx=5, pady=5)
            tk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
            port_var = tk.StringVar(value=str(self.cfg.get("ftp_port", 21)))
            port_entry = tk.Entry(conn_frame, textvariable=port_var, width=10)
            port_entry.grid(row=0, column=3, padx=5, pady=5)
            tk.Label(conn_frame, text="User:").grid(row=1, column=0, padx=5, pady=5)
            user_var = tk.StringVar(value=self.cfg.get("ftp_user", ""))
            user_entry = tk.Entry(conn_frame, textvariable=user_var)
            user_entry.grid(row=1, column=1, padx=5, pady=5)
            tk.Label(conn_frame, text="Password:").grid(row=1, column=2, padx=5, pady=5)
            pass_var = tk.StringVar()
            pass_entry = tk.Entry(conn_frame, textvariable=pass_var, show="*")
            pass_entry.grid(row=1, column=3, padx=5, pady=5)
            connect_btn = tk.Button(conn_frame, text="Connect", command=lambda: self._ftp_connect(win, host_var.get(), user_var.get(), pass_var.get(), int(port_var.get())))
            connect_btn.grid(row=2, column=0, columnspan=4, pady=10)

        # File list frame
        if CTK_AVAILABLE:
            list_frame = ctk.CTkFrame(win)
            list_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.ftp_listbox = tk.Listbox(list_frame)
            self.ftp_listbox.pack(fill="both", expand=True, padx=5, pady=5)
            btn_frame = ctk.CTkFrame(win, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkButton(btn_frame, text="Download", command=self._ftp_download).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Upload", command=self._ftp_upload).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Close", command=win.destroy).pack(side="right", padx=5)
        else:
            list_frame = tk.Frame(win)
            list_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.ftp_listbox = tk.Listbox(list_frame)
            self.ftp_listbox.pack(fill="both", expand=True, padx=5, pady=5)
            btn_frame = tk.Frame(win)
            btn_frame.pack(fill="x", padx=10, pady=10)
            tk.Button(btn_frame, text="Download", command=self._ftp_download).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Upload", command=self._ftp_upload).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right", padx=5)

    def _ftp_connect(self, win, host, user, password, port):
        try:
            self.ftp.connect(host, user, password, port, timeout=30, passive=True)
            self._ftp_refresh_list()
            messagebox.showinfo("FTP", "Connected successfully")
        except Exception as e:
            messagebox.showerror("FTP Error", f"Failed to connect: {e}")

    def _ftp_refresh_list(self):
        try:
            files = self.ftp.nlst()
            self.ftp_listbox.delete(0, tk.END)
            for f in files:
                self.ftp_listbox.insert(tk.END, f)
        except Exception as e:
            messagebox.showerror("FTP Error", f"Failed to list files: {e}")

    def _ftp_download(self):
        selection = self.ftp_listbox.curselection()
        if not selection:
            messagebox.showwarning("FTP", "No file selected")
            return
        remote_file = self.ftp_listbox.get(selection[0])
        local_file = filedialog.asksaveasfilename(initialfile=remote_file)
        if not local_file:
            return
        try:
            with open(local_file, "wb") as f:
                self.ftp.ftp.retrbinary(f"RETR {remote_file}", f.write)
            messagebox.showinfo("FTP", "Download completed")
        except Exception as e:
            messagebox.showerror("FTP Error", f"Download failed: {e}")

    def _ftp_upload(self):
        local_file = filedialog.askopenfilename()
        if not local_file:
            return
        remote_file = os.path.basename(local_file)
        try:
            with open(local_file, "rb") as f:
                self.ftp.ftp.storbinary(f"STOR {remote_file}", f)
            self._ftp_refresh_list()
            messagebox.showinfo("FTP", "Upload completed")
        except Exception as e:
            messagebox.showerror("FTP Error", f"Upload failed: {e}")

    def open_wiiu_files(self):
        # Placeholder for WiiU files browser
        messagebox.showinfo("WiiU Files", "WiiU files browser not implemented yet.")

    def open_models_window(self):
        # Placeholder for models window
        messagebox.showinfo("Models", "Models window not implemented yet.")


    # TGA import

    def import_img(self, size, bits):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not path:
            return
        save = filedialog.asksaveasfilename(defaultextension=".tga", filetypes=[("TGA", "*.tga")])
        if not save:
            return
        try:
            convert_to_tga(path, save, size, bits)
            messagebox.showinfo(get_locale().get("done","Done"), "Successfully converted to TGA.")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {e}")

    # Settings

    def open_settings(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("560x340")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("560x340")
        win.title(loc["settings"])
        win.transient(self.root)
        win.grab_set()

        # Theme (appearance), Accent, Rainbow toggle, language, icon picker
        if CTK_AVAILABLE:
            frm = ctk.CTkFrame(win, corner_radius=6)
            frm.pack(fill="both", expand=True, padx=12, pady=12)
            ctk.CTkLabel(frm, text="Appearance:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
            appearance_var = ctk.StringVar(value=self.cfg.get("appearance","Dark"))
            appearance_combo = ctk.CTkOptionMenu(frm, values=["Light","Dark"], variable=appearance_var)
            appearance_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Accent (preset):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
            accent_var = ctk.StringVar(value=self.cfg.get("accent","blue"))
            accent_combo = ctk.CTkOptionMenu(frm, values=["blue","green","dark-blue","white","red","purple"], variable=accent_var)
            accent_combo.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Rainbow RGB:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
            rainbow_var = ctk.BooleanVar(value=self.cfg.get("rainbow", False))
            rainbow_switch = ctk.CTkSwitch(frm, text="", variable=rainbow_var)
            rainbow_switch.grid(row=2, column=1, sticky="w", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Language:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
            lang_var = ctk.StringVar(value=self.cfg.get("language","English"))
            lang_combo = ctk.CTkOptionMenu(frm, values=list(LOCALES.keys()), variable=lang_var)
            lang_combo.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

            frm.grid_columnconfigure(1, weight=1)
            btn_frame = ctk.CTkFrame(win, fg_color="transparent")
            btn_frame.pack(fill="x", padx=12, pady=(0,12))
            def on_save():
                self.cfg["appearance"] = appearance_var.get()
                self.cfg["accent"] = accent_var.get()
                self.cfg["rainbow"] = bool(rainbow_var.get())
                self.cfg["language"] = lang_var.get()
                save_cfg(self.cfg)
                # apply appearance & accent & rainbow
                try:
                    ctk.set_appearance_mode(self.cfg["appearance"])
                except Exception:
                    pass
                try:
                    ctk.set_default_color_theme(self.cfg["accent"])
                except Exception:
                    pass
                if self.cfg["rainbow"]:
                    self.start_rainbow()
                else:
                    self.stop_rainbow()
                if self.cfg["icon_path"] and os.path.exists(self.cfg["icon_path"]):
                    try:
                        if self.cfg["icon_path"].lower().endswith('.ico'):
                            self.root.iconbitmap(self.cfg["icon_path"])
                        else:
                            img = Image.open(self.cfg["icon_path"])
                            img = img.resize((32, 32), Image.LANCZOS)
                            self.icon_photo = ImageTk.PhotoImage(img)
                            self.root.iconphoto(True, self.icon_photo)
                    except Exception:
                        pass
                self.apply_language()
                messagebox.showinfo(loc["save"], loc["settings_saved"])
                win.destroy()
            ctk.CTkButton(btn_frame, text=loc["save"], command=on_save).pack(side="right", padx=8)
            ctk.CTkButton(btn_frame, text=loc["cancel"], command=win.destroy).pack(side="right", padx=8)
        else:
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True, padx=8, pady=8)
            tk.Label(frm, text="Appearance:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
            appearance_var = tk.StringVar(value=self.cfg.get("appearance","Dark"))
            tk.OptionMenu(frm, appearance_var, "Light", "Dark").grid(row=0, column=1, sticky="ew", padx=6, pady=6)
            tk.Label(frm, text="Accent (preset):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
            accent_var = tk.StringVar(value=self.cfg.get("accent","blue"))
            tk.OptionMenu(frm, accent_var, "blue", "green", "red", "purple").grid(row=1, column=1, sticky="ew", padx=6, pady=6)
            tk.Label(frm, text="Rainbow RGB:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
            rainbow_var = tk.BooleanVar(value=self.cfg.get("rainbow",False))
            tk.Checkbutton(frm, variable=rainbow_var).grid(row=2, column=1, sticky="w", padx=6, pady=6)
            tk.Label(frm, text="Language:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
            lang_var = tk.StringVar(value=self.cfg.get("language","English"))
            tk.OptionMenu(frm, lang_var, *list(LOCALES.keys())).grid(row=3, column=1, sticky="ew", padx=6, pady=6)

            frm.grid_columnconfigure(1, weight=1)
            btn_frame = tk.Frame(win)
            btn_frame.pack(fill="x", padx=8, pady=(0,8))
            def on_save():
                self.cfg["appearance"] = appearance_var.get()
                self.cfg["accent"] = accent_var.get()
                self.cfg["rainbow"] = bool(rainbow_var.get())
                self.cfg["language"] = lang_var.get()
                save_cfg(self.cfg)
                if self.cfg["icon_path"] and os.path.exists(self.cfg["icon_path"]):
                    try:
                        if self.cfg["icon_path"].lower().endswith('.ico'):
                            self.root.iconbitmap(self.cfg["icon_path"])
                        else:
                            img = Image.open(self.cfg["icon_path"])
                            img = img.resize((32, 32), Image.LANCZOS)
                            self.icon_photo = ImageTk.PhotoImage(img)
                            self.root.iconphoto(True, self.icon_photo)
                    except Exception:
                        pass
                self.apply_language()
                messagebox.showinfo(loc["save"], loc["settings_saved"])
                win.destroy()
            tk.Button(btn_frame, text=loc["save"], command=on_save).pack(side="right", padx=8)
            tk.Button(btn_frame, text=loc["cancel"], command=win.destroy).pack(side="right", padx=8)


    # Credits

    def open_credits(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("380x160")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("380x160")
        win.title(loc["credits"])
        text = f"Primary Developer: Noobie\n\nThanks for using WiiU Boot Editor.\nVersion: {VERSION}\n\nWarning some buttons may not work!"
        if CTK_AVAILABLE:
            ctk.CTkLabel(win, text=text, wraplength=360, justify="left").pack(padx=12, pady=12)
            ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=(0,12))
        else:
            tk.Label(win, text=text, wraplength=360, justify="left").pack(padx=12, pady=12)
            tk.Button(win, text="Close", command=win.destroy).pack(pady=(0,12))


    # Update Log viewer

    def show_update_log(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("420x260")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("420x260")
        win.title("Update Log")
        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.insert("1.0", UPDATE_LOG)
        txt.configure(state="disabled")
        if CTK_AVAILABLE:
            ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=(0,8))
        else:
            tk.Button(win, text="Close", command=win.destroy).pack(pady=(0,8))

    # About / Version and online update check

    def open_about(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("460x220")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("460x220")
        win.title(loc.get("about","About / Version"))
        text = f"{APP_NAME}\nVersion: {VERSION}\n\nDeveloper: Silly Noobie\n\nSome buttons may not work!\n\nCheck for updates online: Null, Updates aren't implemented yet."
        if CTK_AVAILABLE:
            ctk.CTkLabel(win, text=text, justify="left").pack(anchor="w", padx=12, pady=12)
            btn_frame = ctk.CTkFrame(win, fg_color="transparent")
            btn_frame.pack(fill="x", padx=12, pady=(0,12))
            ctk.CTkButton(btn_frame, text=loc.get("check_updates","Check for updates"), command=self.check_for_updates_online).pack(side="left")
            ctk.CTkButton(btn_frame, text="Close", command=win.destroy).pack(side="right")
        else:
            tk.Label(win, text=text, justify="left").pack(anchor="w", padx=12, pady=12)
            btn_frame = tk.Frame(win)
            btn_frame.pack(fill="x", padx=12, pady=(0,12))
            tk.Button(btn_frame, text=loc.get("check_updates","Check for updates"), command=self.check_for_updates_online).pack(side="left")
            tk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right")

    def check_for_updates_online(self):
        loc = get_locale()
        url = self.cfg.get("update_url","").strip()
        if not url:
            messagebox.showinfo("Update", "No update URL configured. Add one in Settings (Update check URL).")
            return

        def task():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{VERSION}"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode('utf-8').strip()
                remote_ver = body.splitlines()[0].strip()
                if remote_ver and remote_ver != VERSION:
                    message = f"{loc.get('update_available','Update available')}: {remote_ver}\n\n{body}"
                    messagebox.showinfo("Update", message)
                else:
                    messagebox.showinfo("Update", loc.get("up_to_date","You are up to date"))
            except urllib.error.URLError as e:
                messagebox.showerror("Update", f"{loc.get('update_check_failed','Update check failed')}: {e}")
            except Exception as e:
                messagebox.showerror("Update", f"{loc.get('update_check_failed','Update check failed')}: {e}")

        threading.Thread(target=task, daemon=True).start()


    # Local meta.xml structured editor

    def open_local_meta_editor(self):
        loc = get_locale()
        path = filedialog.askopenfilename(title=loc["open_file"], filetypes=[("meta.xml","meta.xml"),("XML files","*.xml"),("All files","*.*")])
        if not path:
            return
        self._open_meta_editor_structured(path, remote_name=os.path.basename(path), is_remote=False)

    def _open_meta_editor_structured(self, local_path, remote_name="meta.xml", is_remote=False):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("760x560")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("760x560")
        win.title(f"{loc.get('edit_meta','Edit')} {remote_name}")

        # Notebook or simple frames
        if CTK_AVAILABLE:
            nb = ctk.CTkTabview(win, width=740, height=500)
            nb.pack(fill="both", expand=True, padx=8, pady=8)
            nb.add("Fields")
            nb.add("Raw XML")
            frame_struct = nb.tab("Fields")
            frame_raw = nb.tab("Raw XML")
        else:
            nb = tk.Frame(win)
            nb.pack(fill="both", expand=True, padx=6, pady=6)
            frame_struct = tk.Frame(nb)
            frame_raw = tk.Frame(nb)
            frame_struct.pack(fill="both", expand=True)
            frame_raw.pack_forget()

        try:
            tree = ET.parse(local_path)
            root_elem = tree.getroot()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse XML: {e}")
            win.destroy()
            return

        def find_text(tag):
            el = root_elem.find(tag)
            return el.text if el is not None else ""

        def set_text(tag, text_val):
            el = root_elem.find(tag)
            if el is None:
                el = ET.SubElement(root_elem, tag)
            el.text = text_val

        fields = [
            (get_locale().get("edit_meta","Long name (EN)"), "longname_en"),
            ("Long name (FR)", "longname_fr"),
            ("Short name", "shortname"),
            ("Title version", "title_version"),
            ("Publisher", "publisher"),
        ]
        entries = {}
        for i, (lbl_text, tag) in enumerate(fields):
            if CTK_AVAILABLE:
                ctk.CTkLabel(frame_struct, text=lbl_text).grid(row=i, column=0, sticky="w", padx=8, pady=6)
                var = tk.StringVar(value=find_text(tag))
                ctk.CTkEntry(frame_struct, textvariable=var).grid(row=i, column=1, sticky="ew", padx=8, pady=6)
                entries[tag] = var
            else:
                tk.Label(frame_struct, text=lbl_text).grid(row=i, column=0, sticky="w", padx=8, pady=6)
                var = tk.StringVar(value=find_text(tag))
                tk.Entry(frame_struct, textvariable=var).grid(row=i, column=1, sticky="ew", padx=8, pady=6)
                entries[tag] = var
        try:
            frame_struct.grid_columnconfigure(1, weight=1)
        except Exception:
            pass

        raw_text = tk.Text(frame_raw, wrap="none")
        raw_text.pack(fill="both", expand=True, padx=8, pady=8)
        try:
            raw_str = ET.tostring(root_elem, encoding="unicode")
            raw_text.delete("1.0", tk.END)
            raw_text.insert("1.0", raw_str)
        except Exception as e:
            raw_text.insert("1.0", f"Failed to render raw XML: {e}")

        def save_all():
            for tag, var in entries.items():
                val = var.get()
                if val:
                    set_text(tag, val)
                else:
                    el = root_elem.find(tag)
                    if el is not None:
                        root_elem.remove(el)
            raw_current = raw_text.get("1.0", "end").strip()
            try:
                parsed = ET.fromstring(raw_current)
                root_elem.clear()
                for k, v in parsed.attrib.items():
                    root_elem.set(k, v)
                for child in parsed:
                    root_elem.append(child)
            except Exception:
                pass

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
            try:
                tree = ET.ElementTree(root_elem)
                tree.write(tmp.name, encoding="utf-8", xml_declaration=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to write XML: {e}")
                return

            if is_remote:
                try:
                    with open(tmp.name, "rb") as rf:
                        self.ftp.storbinary_from_fd("meta.xml", rf, progress_callback=None)
                    messagebox.showinfo("Saved", "meta.xml uploaded to remote.")
                    win.destroy()
                    os.unlink(tmp.name)
                    return
                except Exception as e:
                    messagebox.showerror("Upload Failed", str(e))
                    return
            else:
                save_path = filedialog.asksaveasfilename(defaultextension=".xml", initialfile=os.path.basename(local_path))
                if not save_path:
                    return
                try:
                    shutil.copy(tmp.name, save_path)
                    messagebox.showinfo("Saved", f"meta.xml saved to {save_path}")
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Save failed", str(e))
                finally:
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass

        if CTK_AVAILABLE:
            btnf = ctk.CTkFrame(win, fg_color="transparent")
            btnf.pack(fill="x", padx=8, pady=6)
            ctk.CTkButton(btnf, text=get_locale()["save"], command=save_all).pack(side="right", padx=6)
            ctk.CTkButton(btnf, text=get_locale()["cancel"], command=win.destroy).pack(side="right")
        else:
            btnf = tk.Frame(win)
            btnf.pack(fill="x", padx=8, pady=6)
            tk.Button(btnf, text=get_locale()["save"], command=save_all).pack(side="right", padx=6)
            tk.Button(btnf, text=get_locale()["cancel"], command=win.destroy).pack(side="right")
