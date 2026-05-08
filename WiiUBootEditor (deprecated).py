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

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except Exception as e:
    # Friendly warning; fallback to builtin tkinter
    print("Warning: customtkinter not installed or failed to import. Falling back to tkinter. (Install with `pip install customtkinter` for the modern UI.)")
    CTK_AVAILABLE = False

# ---------------------------
# Configuration
# ---------------------------
APP_NAME = "WiiU Boot Editor"
VERSION = "1.1.0-experimental"
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

ver. 1.1.0 experimental 2:

- More testing soon.
 -------------------
 Planned features (not guaranteed):
 - Multi file project.
 (basically means that the app will be cut in several different file with a main one, and the others will be imported as modules, to make the code more readable and maintainable)


"""

# ---------------------------
# Localization (same as original)
# ---------------------------
LOCALES = {
    "English": {
        "settings": "Settings",
        "credits": "Credits",
        "tga_header": "TGA Conversion:",
        "ftp_header": "FTP Manager:",
        "edit_meta": "Edit meta.xml",
        "download": "Download",
        "upload": "Upload",
        "save": "Save",
        "cancel": "Cancel",
        "done": "Done",
        "settings_saved": "Settings saved.",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "host": "Host:",
        "user": "User:",
        "password": "Password:",
        "remote": "Remote",
        "local": "Local",
        "preview": "Preview",
        "open_file": "Open file",
        "select_file": "Select a file",
        "speed": "Speed:",
        "about": "About / Version",
        "check_updates": "Check for updates",
        "update_available": "Update available",
        "up_to_date": "You are up to date",
        "update_check_failed": "Update check failed",
        "filename": "Filename",
        "filesize": "Size",
        "filetype": "Type",
        "modified": "Modified",
        "permissions": "Permissions",
        "quick_connect": "Quickconnect",
        "status": "Status:",
        "remote_directory": "Remote directory:",
        "local_directory": "Local directory:",
        "message_log": "Message log"
    },
    "French": {
        "settings": "Paramètres",
        "credits": "Crédits",
        "tga_header": "Conversion TGA :",
        "ftp_header": "Gestion FTP :",
        "edit_meta": "Éditer meta.xml",
        "download": "Télécharger",
        "upload": "Uploader",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "done": "Terminé",
        "settings_saved": "Paramètres enregistrés.",
        "connect": "Se connecter",
        "disconnect": "Déconnecter",
        "host": "Hôte :",
        "user": "Utilisateur :",
        "password": "Mot de passe :",
        "remote": "Distant",
        "local": "Local",
        "preview": "Aperçu",
        "open_file": "Ouvrir le fichier",
        "select_file": "Sélectionnez un fichier",
        "speed": "Vitesse :",
        "about": "À propos / Version",
        "check_updates": "Vérifier les mises à jour",
        "update_available": "Mise à jour disponible",
        "up_to_date": "À jour",
        "update_check_failed": "Échec de la vérification",
        "filename": "Nom du fichier",
        "filesize": "Taille",
        "filetype": "Type",
        "modified": "Modifié",
        "permissions": "Permissions",
        "quick_connect": "Connexion rapide",
        "status": "Statut :",
        "remote_directory": "Répertoire distant :",
        "local_directory": "Répertoire local :",
        "message_log": "Journal des messages"
    },
    "Arabic": {
        "settings": "الإعدادات",
        "credits": "المساهمون",
        "tga_header": "تحويل TGA:",
        "ftp_header": "مدير FTP:",
        "edit_meta": "تعديل meta.xml",
        "download": "تحميل",
        "upload": "رفع",
        "save": "حفظ",
        "cancel": "إلغاء",
        "done": "تم",
        "settings_saved": "تم حفظ الإعدادات.",
        "connect": "اتصال",
        "disconnect": "قطع الاتصال",
        "host": "المضيف:",
        "user": "المستخدم:",
        "password": "كلمة المرور:",
        "remote": "بعيد",
        "local": "محلي",
        "preview": "معاينة",
        "open_file": "فتح الملف",
        "select_file": "اختر ملفًا",
        "speed": "السرعة:",
        "about": "حول / الإصدار",
        "check_updates": "تحقق من التحديثات",
        "update_available": "تحديث متاح",
        "up_to_date": "أنت على آخر إصدار",
        "update_check_failed": "فشل فحص التحديث",
        "filename": "اسم الملف",
        "filesize": "الحجم",
        "filetype": "النوع",
        "modified": "معدل",
        "permissions": "الصلاحيات",
        "quick_connect": "اتصال سريع",
        "status": "الحالة:",
        "remote_directory": "المجلد البعيد:",
        "local_directory": "المجلد المحلي:",
        "message_log": "سجل الرسائل"
    },
    "Russian": {
        "settings": "Настройки",
        "credits": "Авторы",
        "tga_header": "Конвертация TGA:",
        "ftp_header": "FTP менеджер:",
        "edit_meta": "Редактировать meta.xml",
        "download": "Скачать",
        "upload": "Загрузить",
        "save": "Сохранить",
        "cancel": "Отмена",
        "done": "Готово",
        "settings_saved": "Настройки сохранены.",
        "connect": "Подключиться",
        "disconnect": "Отключиться",
        "host": "Хост:",
        "user": "Пользователь:",
        "password": "Пароль:",
        "remote": "Удалённый",
        "local": "Локальный",
        "preview": "Предпросмотр",
        "open_file": "Открыть файл",
        "select_file": "Выберите файл",
        "speed": "Скорость:",
        "about": "О приложении / Версия",
        "check_updates": "Проверить обновления",
        "update_available": "Доступно обновление",
        "up_to_date": "У вас последняя версия",
        "update_check_failed": "Ошибка проверки обновлений",
        "filename": "Имя файла",
        "filesize": "Размер",
        "filetype": "Тип",
        "modified": "Изменён",
        "permissions": "Права",
        "quick_connect": "Быстрое подключение",
        "status": "Статус:",
        "remote_directory": "Удалённая папка:",
        "local_directory": "Локальная папка:",
        "message_log": "Журнал сообщений"
    },
    "Portuguese": {
        "settings": "Configurações",
        "credits": "Créditos",
        "tga_header": "Conversão TGA:",
        "ftp_header": "Gerenciador FTP:",
        "edit_meta": "Editar meta.xml",
        "download": "Baixar",
        "upload": "Enviar",
        "save": "Salvar",
        "cancel": "Cancelar",
        "done": "Concluído",
        "settings_saved": "Configurações salvas.",
        "connect": "Conectar",
        "disconnect": "Desconectar",
        "host": "Host:",
        "user": "Usuário:",
        "password": "Senha:",
        "remote": "Remoto",
        "local": "Local",
        "preview": "Pré-visualização",
        "open_file": "Abrir arquivo",
        "select_file": "Selecione um arquivo",
        "speed": "Velocidade:",
        "about": "Sobre / Versão",
        "check_updates": "Verificar atualizações",
        "update_available": "Atualização disponível",
        "up_to_date": "Você está atualizado",
        "update_check_failed": "Falha na verificação",
        "filename": "Nome do arquivo",
        "filesize": "Tamanho",
        "filetype": "Tipo",
        "modified": "Modificado",
        "permissions": "Permissões",
        "quick_connect": "Conexão rápida",
        "status": "Status:",
        "remote_directory": "Diretório remoto:",
        "local_directory": "Diretório local:",
        "message_log": "Log de mensagens"
    },
    "Polish": {
        "settings": "Ustawienia",
        "credits": "Współtwórcy",
        "tga_header": "Konwersja TGA:",
        "ftp_header": "Menedżer FTP:",
        "edit_meta": "Edytuj meta.xml",
        "download": "Pobierz",
        "upload": "Wyślij",
        "save": "Zapisz",
        "cancel": "Anuluj",
        "done": "Gotowe",
        "settings_saved": "Ustawienia zapisane.",
        "connect": "Połącz",
        "disconnect": "Rozłącz",
        "host": "Host:",
        "user": "Użytkownik:",
        "password": "Hasło:",
        "remote": "Zdalny",
        "local": "Lokalny",
        "preview": "Podgląd",
        "open_file": "Otwórz plik",
        "select_file": "Wybierz plik",
        "speed": "Prędkość:",
        "about": "O programie / Wersja",
        "check_updates": "Sprawdź aktualizacje",
        "update_available": "Dostępna aktualizacja",
        "up_to_date": "Posiadasz najnowszą wersję",
        "update_check_failed": "Błąd sprawdzania aktualizacji",
        "filename": "Nazwa pliku",
        "filesize": "Rozmiar",
        "filetype": "Typ",
        "modified": "Zmodyfikowano",
        "permissions": "Uprawnienia",
        "quick_connect": "Szybkie łączenie",
        "status": "Status:",
        "remote_directory": "Zdalny katalog:",
        "local_directory": "Lokalny katalog:",
        "message_log": "Dziennik wiadomości"
    },
        "Glujp": {
        "settings": "SGlujpbGUgbG9n",
        "credits": "CGlujpbGUgbG9n",
        "tga_header": "TGA CGlujpbGUgbG9n:",
        "ftp_header": "FTP MGlujpbGUgbG9n:",
        "edit_meta": "EGlujpbGUgbG9n meta.xml",
        "download": "DGlujpbGUgbG9n",
        "upload": "UGlujpbGUgbG9n",
        "save": "SGlujpbGUgbG9n",
        "cancel": "CGlujpbGUgbG9n",
        "done": "DGlujpbGUgbG9n",
        "settings_saved": "SGlujpbGUgbG9n.",
        "connect": "CoGlujpbGUgbG9n",
        "disconnect": "DGlujpbGUgbG9n",
        "host": "HGlujpbGUgbG9n:",
        "user": "UGlujpbGUgbG9n:",
        "password": "PGlujpbGUgbG9n:",
        "remote": "RGlujpbGUgbG9n",
        "local": "LGlujpbGUgbG9n",
        "preview": "PGlujpbGUgbG9n",
        "open_file": "OGlujpbGUgbG9n",
        "select_file": "SGlujpbGUgbG9n",
        "speed": "SGlujpbGUgbG9n:",
        "about": "AGlujpbGUgbG9n / VGlujpbGUgbG9n",
        "check_updates": "CGlujpbGUgbG9n",
        "update_available": "UGlujpbGUgbG9n",
        "up_to_date": "YGlujpbGUgbG9n",
        "update_check_failed": "UGlujpbGUgbG9n",
        "filename": "FGlujpbGUgbG9n",
        "filesize": "SGlujpbGUgbG9n",
        "filetype": "TGlujpbGUgbG9n",
        "modified": "MGlujpbGUgbG9n",
        "permissions": "PGlujpbGUgbG9n",
        "quick_connect": "QGlujpbGUgbG9n",
        "status": "SGlujpbGUgbG9n:",
        "remote_directory": "RGlujpbGUgbG9n:",
        "local_directory": "LGlujpbGUgbG9n:",
        "message_log": "MGlujpbGUgbG9n"
    }
}

def load_cfg():
    try:
        if USER_CFG.exists():
            with open(USER_CFG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CFG.items():
                cfg.setdefault(k, v)
            return cfg
    except Exception:
        pass
    return DEFAULT_CFG.copy()

def save_cfg(cfg):
    try:
        with open(USER_CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Failed to save config:", e)

cfg = load_cfg()

def get_locale():
    return LOCALES.get(cfg.get("language", "English"), LOCALES["English"])

# ---------------------------
# Utilities
# ---------------------------
def convert_to_tga(src, dst, size, bits):
    img = Image.open(src).convert("RGBA" if bits == 32 else "RGB")
    img = img.resize(size, Image.LANCZOS)
    img.save(dst, format="TGA")

def human_size(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ---------------------------
# FTP wrapper
# ---------------------------
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

# ---------------------------
# Main Application (CustomTkinter)
# ---------------------------
class ModernCTkApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.ftp = FTPClient()
        self.progress_win = None
        self.progress_var = tk.DoubleVar(value=0.0)
        self.speed_var = tk.StringVar(value="")
        self.preview_img_ref = None
        self.current_local_dir = os.path.expanduser("~")
        self.current_remote_dir = "/"

        # rainbow animation params
        self._rainbow_active = cfg.get("rainbow", False)
        self._rainbow_h = 0.0
        self._rainbow_job = None

        # Setup CTk defaults or warn
        if CTK_AVAILABLE:
            try:
                ctk.set_appearance_mode(cfg.get("appearance", "Dark"))
                try:
                    ctk.set_default_color_theme(cfg.get("accent", "blue"))
                except Exception:
                    pass
            except Exception:
                # In rare cases setting appearance may fail; fallback gracefully
                print("Warning: customtkinter appearance config failed; continuing with default.")
        else:
            print("Using standard tkinter UI (customtkinter unavailable).")

        # Attempt to set icon
        icon_path = cfg.get("icon_path", "") or ""
        if icon_path and os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
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
            self.btn_credits = ctk.CTkButton(left_w, text=get_locale()["credits"], command=self.open_credits, **btn_style)
            self.btn_credits.pack(fill="x", pady=6, padx=12)
            self.btn_meta = ctk.CTkButton(left_w, text=get_locale()["edit_meta"], command=self.open_local_meta_editor, **btn_style)
            self.btn_meta.pack(fill="x", pady=6, padx=12)
            # New: Update Log and About buttons
            self.btn_updatelog = ctk.CTkButton(left_w, text="Update Log", command=self.show_update_log, **btn_style)
            self.btn_updatelog.pack(fill="x", pady=6, padx=12)
            self.btn_about = ctk.CTkButton(left_w, text=get_locale().get("about","About / Version"), command=self.open_about, **btn_style)
            self.btn_about.pack(fill="x", pady=6, padx=12)
            ctk.CTkLabel(left_w, text=get_locale()["tga_header"], anchor="w").pack(fill="x", pady=(12,4), padx=12)
            ctk.CTkButton(left_w, text="Import iconTex (128x128, 32b)", command=lambda: self.import_img((128,128),32), **btn_style).pack(fill="x", pady=4, padx=12)
            ctk.CTkButton(left_w, text="Import bootDrcTex (854x480, 24b)", command=lambda: self.import_img((854,480),24), **btn_style).pack(fill="x", pady=4, padx=12)
            ctk.CTkButton(left_w, text="Import bootTvTex (1280x720, 24b)", command=lambda: self.import_img((1280,720),24), **btn_style).pack(fill="x", pady=4, padx=12)
            ctk.CTkButton(left_w, text="Import bootLogoTex (170x42, 32b)", command=lambda: self.import_img((170,42),32), **btn_style).pack(fill="x", pady=4, padx=12)
            ctk.CTkLabel(left_w, text=get_locale()["ftp_header"], anchor="w").pack(fill="x", pady=(16,4), padx=12)
            ctk.CTkButton(left_w, text="Open FTP Browser", command=self.open_ftp_browser, **btn_style).pack(fill="x", pady=(4,12), padx=12)
            # New: WiiU file browser button
            ctk.CTkButton(left_w, text="Open WiiU files (.szs, .params)", command=self.open_wiiu_files, **btn_style).pack(fill="x", pady=(0,12), padx=12)
            # Models button (new)
            ctk.CTkButton(left_w, text="Models", command=self.open_models_window, **btn_style).pack(fill="x", pady=(0,12), padx=12)
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

        # ---------- Right panel (main) ----------
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
            welcome = ctk.CTkLabel(main_area, text="Welcome — use the left panel to select actions (FTP, TGA, meta.xml).", justify="center")
            welcome.pack(expand=True, fill="both", padx=24, pady=24)
        else:
            topbar = tk.Frame(right_w, bg="#ffffff")
            topbar.pack(fill="x", padx=8, pady=(8,4))
            self.status_label = tk.Label(topbar, text=f"{APP_NAME} — ready", anchor="w")
            self.status_label.pack(side="left")
            self.accent_bar = tk.Frame(right_w, height=4, bg="#0078d7")
            self.accent_bar.pack(fill="x", padx=8, pady=(0,8))
            main_area = tk.Frame(right_w, bg="#fff")
            main_area.pack(fill="both", expand=True, padx=8, pady=8)
            welcome = tk.Label(main_area, text="Welcome — use the left panel to select actions (FTP, TGA, meta.xml).", justify="center")
            welcome.pack(expand=True, fill="both", padx=12, pady=12)

    # -------------------------
    # Language application
    # -------------------------
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
        except Exception:
            pass

    # -------------------------
    # Rainbow accent animation
    # -------------------------
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
            ctk.set_default_color_theme(cfg.get("accent", "blue"))
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

    # -------------------------
    # TGA import
    # -------------------------
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

    # -------------------------
    # Settings
    # -------------------------
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
            appearance_var = ctk.StringVar(value=cfg.get("appearance","Dark"))
            appearance_combo = ctk.CTkOptionMenu(frm, values=["Light","Dark"], variable=appearance_var)
            appearance_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Accent (preset):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
            accent_var = ctk.StringVar(value=cfg.get("accent","blue"))
            accent_combo = ctk.CTkOptionMenu(frm, values=["blue","green","dark-blue","white","red","purple"], variable=accent_var)
            accent_combo.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Rainbow RGB:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
            rainbow_var = ctk.BooleanVar(value=cfg.get("rainbow", False))
            rainbow_switch = ctk.CTkSwitch(frm, text="", variable=rainbow_var)
            rainbow_switch.grid(row=2, column=1, sticky="w", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Language:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
            lang_var = ctk.StringVar(value=cfg.get("language","English"))
            lang_combo = ctk.CTkOptionMenu(frm, values=list(LOCALES.keys()), variable=lang_var)
            lang_combo.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

            ctk.CTkLabel(frm, text="Icon (.ico):").grid(row=4, column=0, sticky="w", padx=6, pady=6)
            icon_var = ctk.StringVar(value=cfg.get("icon_path",""))
            icon_entry = ctk.CTkEntry(frm, textvariable=icon_var)
            icon_entry.grid(row=4, column=1, sticky="ew", padx=6, pady=6)
            def pick_icon_cb():
                p = filedialog.askopenfilename(filetypes=[("ICO","*.ico"),("All files","*.*")])
                if p:
                    icon_var.set(p)
            ctk.CTkButton(frm, text="Browse...", command=pick_icon_cb).grid(row=4, column=2, padx=6, pady=6)

            # update URL field
            ctk.CTkLabel(frm, text="Update check URL:").grid(row=5, column=0, sticky="w", padx=6, pady=6)
            update_url_var = ctk.StringVar(value=cfg.get("update_url",""))
            ctk.CTkEntry(frm, textvariable=update_url_var).grid(row=5, column=1, sticky="ew", padx=6, pady=6)

            frm.grid_columnconfigure(1, weight=1)
            btn_frame = ctk.CTkFrame(win, fg_color="transparent")
            btn_frame.pack(fill="x", padx=12, pady=(0,12))
            def on_save():
                cfg["appearance"] = appearance_var.get()
                cfg["accent"] = accent_var.get()
                cfg["rainbow"] = bool(rainbow_var.get())
                cfg["language"] = lang_var.get()
                cfg["icon_path"] = icon_var.get() or ""
                cfg["update_url"] = update_url_var.get() or ""
                save_cfg(cfg)
                # apply appearance & accent & rainbow
                try:
                    ctk.set_appearance_mode(cfg["appearance"])
                except Exception:
                    pass
                try:
                    ctk.set_default_color_theme(cfg["accent"])
                except Exception:
                    pass
                if cfg["rainbow"]:
                    self.start_rainbow()
                else:
                    self.stop_rainbow()
                if cfg["icon_path"] and os.path.exists(cfg["icon_path"]):
                    try:
                        self.root.iconbitmap(cfg["icon_path"])
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
            appearance_var = tk.StringVar(value=cfg.get("appearance","Dark"))
            tk.OptionMenu(frm, appearance_var, "Light", "Dark").grid(row=0, column=1, sticky="ew", padx=6, pady=6)
            tk.Label(frm, text="Accent (preset):").grid(row=1, column=0, sticky="w", padx=6, pady=6)
            accent_var = tk.StringVar(value=cfg.get("accent","blue"))
            tk.OptionMenu(frm, accent_var, "blue", "green", "red", "purple").grid(row=1, column=1, sticky="ew", padx=6, pady=6)
            tk.Label(frm, text="Rainbow RGB:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
            rainbow_var = tk.BooleanVar(value=cfg.get("rainbow",False))
            tk.Checkbutton(frm, variable=rainbow_var).grid(row=2, column=1, sticky="w", padx=6, pady=6)
            tk.Label(frm, text="Language:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
            lang_var = tk.StringVar(value=cfg.get("language","English"))
            tk.OptionMenu(frm, lang_var, *list(LOCALES.keys())).grid(row=3, column=1, sticky="ew", padx=6, pady=6)
            tk.Label(frm, text="Icon (.ico):").grid(row=4, column=0, sticky="w", padx=6, pady=6)
            icon_var = tk.StringVar(value=cfg.get("icon_path",""))
            tk.Entry(frm, textvariable=icon_var).grid(row=4, column=1, sticky="ew", padx=6, pady=6)
            def pick_icon_cb():
                p = filedialog.askopenfilename(filetypes=[("ICO","*.ico"),("All files","*.*")])
                if p:
                    icon_var.set(p)
            tk.Button(frm, text="Browse...", command=pick_icon_cb).grid(row=4, column=2, padx=6, pady=6)

            tk.Label(frm, text="Update check URL:").grid(row=5, column=0, sticky="w", padx=6, pady=6)
            update_url_var = tk.StringVar(value=cfg.get("update_url",""))
            tk.Entry(frm, textvariable=update_url_var).grid(row=5, column=1, sticky="ew", padx=6, pady=6)

            frm.grid_columnconfigure(1, weight=1)
            btn_frame = tk.Frame(win)
            btn_frame.pack(fill="x", padx=8, pady=(0,8))
            def on_save():
                cfg["appearance"] = appearance_var.get()
                cfg["accent"] = accent_var.get()
                cfg["rainbow"] = bool(rainbow_var.get())
                cfg["language"] = lang_var.get()
                cfg["icon_path"] = icon_var.get() or ""
                cfg["update_url"] = update_url_var.get() or ""
                save_cfg(cfg)
                if cfg["icon_path"] and os.path.exists(cfg["icon_path"]):
                    try:
                        self.root.iconbitmap(cfg["icon_path"])
                    except Exception:
                        pass
                self.apply_language()
                messagebox.showinfo(loc["save"], loc["settings_saved"])
                win.destroy()
            tk.Button(btn_frame, text=loc["save"], command=on_save).pack(side="right", padx=8)
            tk.Button(btn_frame, text=loc["cancel"], command=win.destroy).pack(side="right", padx=8)

    # -------------------------
    # Credits
    # -------------------------
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

    # -------------------------
    # Update Log viewer
    # -------------------------
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

    # -------------------------
    # About / Version and online update check
    # -------------------------
    def open_about(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("460x220")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("460x220")
        win.title(loc.get("about","About / Version"))
        text = f"{APP_NAME}\nVersion: {VERSION}\n\nPrimary Developer: Noobie\n\nSome buttons may not work!\n\nCheck for updates online: Null, Updates aren't implemented yet."
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
        url = cfg.get("update_url","").strip()
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

    # -------------------------
    # Local meta.xml structured editor
    # -------------------------
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

    # -------------------------
    # FTP Browser (FileZilla-like interface)
    # -------------------------
    def open_ftp_browser(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("1200x700")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("1200x700")
        win.title("FTP Browser - FileZilla Style")
        win.transient(self.root)

        # Create main paned window for resizable panels
        paned_main = ttk.PanedWindow(win, orient=tk.VERTICAL)
        paned_main.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Top section: Connection bar
        if CTK_AVAILABLE:
            connection_frame = ctk.CTkFrame(paned_main)
        else:
            connection_frame = ttk.Frame(paned_main)
        
        paned_main.add(connection_frame, weight=0)

        # Quick connect bar
        if CTK_AVAILABLE:
            quick_connect_frame = ctk.CTkFrame(connection_frame)
            quick_connect_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ctk.CTkLabel(quick_connect_frame, text=loc["host"]).grid(row=0, column=0, padx=2, pady=2, sticky="w")
            host_entry = ctk.CTkEntry(quick_connect_frame, width=120)
            host_entry.grid(row=0, column=1, padx=2, pady=2)
            
            ctk.CTkLabel(quick_connect_frame, text=loc["user"]).grid(row=0, column=2, padx=2, pady=2, sticky="w")
            user_entry = ctk.CTkEntry(quick_connect_frame, width=100)
            user_entry.grid(row=0, column=3, padx=2, pady=2)
            
            ctk.CTkLabel(quick_connect_frame, text=loc["password"]).grid(row=0, column=4, padx=2, pady=2, sticky="w")
            pwd_entry = ctk.CTkEntry(quick_connect_frame, width=100, show="*")
            pwd_entry.grid(row=0, column=5, padx=2, pady=2)
            
            connect_btn = ctk.CTkButton(quick_connect_frame, text=loc["connect"], width=80,
                                      command=lambda: threading.Thread(target=self._ftp_connect_and_populate, 
                                                                      args=(host_entry.get(), user_entry.get(), pwd_entry.get(), win), 
                                                                      daemon=True).start())
            connect_btn.grid(row=0, column=6, padx=2, pady=2)
            
            disconnect_btn = ctk.CTkButton(quick_connect_frame, text=loc["disconnect"], width=80,
                                         command=self._ftp_disconnect)
            disconnect_btn.grid(row=0, column=7, padx=2, pady=2)
            
            # Status label
            status_label = ctk.CTkLabel(quick_connect_frame, text=loc["status"] + " Not connected")
            status_label.grid(row=0, column=8, padx=10, pady=2, sticky="w")
        else:
            quick_connect_frame = ttk.Frame(connection_frame)
            quick_connect_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(quick_connect_frame, text=loc["host"]).grid(row=0, column=0, padx=2, pady=2, sticky="w")
            host_entry = ttk.Entry(quick_connect_frame, width=15)
            host_entry.grid(row=0, column=1, padx=2, pady=2)
            
            ttk.Label(quick_connect_frame, text=loc["user"]).grid(row=0, column=2, padx=2, pady=2, sticky="w")
            user_entry = ttk.Entry(quick_connect_frame, width=12)
            user_entry.grid(row=0, column=3, padx=2, pady=2)
            
            ttk.Label(quick_connect_frame, text=loc["password"]).grid(row=0, column=4, padx=2, pady=2, sticky="w")
            pwd_entry = ttk.Entry(quick_connect_frame, width=12, show="*")
            pwd_entry.grid(row=0, column=5, padx=2, pady=2)
            
            connect_btn = ttk.Button(quick_connect_frame, text=loc["connect"], width=10,
                                   command=lambda: threading.Thread(target=self._ftp_connect_and_populate, 
                                                                   args=(host_entry.get(), user_entry.get(), pwd_entry.get(), win), 
                                                                   daemon=True).start())
            connect_btn.grid(row=0, column=6, padx=2, pady=2)
            
            disconnect_btn = ttk.Button(quick_connect_frame, text=loc["disconnect"], width=10,
                                      command=self._ftp_disconnect)
            disconnect_btn.grid(row=0, column=7, padx=2, pady=2)
            
            # Status label
            status_label = ttk.Label(quick_connect_frame, text=loc["status"] + " Not connected")
            status_label.grid(row=0, column=8, padx=10, pady=2, sticky="w")

        # Middle section: Local and Remote file browsers
        middle_paned = ttk.PanedWindow(paned_main, orient=tk.HORIZONTAL)
        paned_main.add(middle_paned, weight=1)

        # Local file browser
        if CTK_AVAILABLE:
            local_frame = ctk.CTkFrame(middle_paned)
        else:
            local_frame = ttk.Frame(middle_paned)
        
        middle_paned.add(local_frame, weight=1)

        # Local directory header
        if CTK_AVAILABLE:
            local_header = ctk.CTkFrame(local_frame)
            local_header.pack(fill=tk.X, padx=2, pady=2)
            ctk.CTkLabel(local_header, text=loc["local_directory"]).pack(side=tk.LEFT, padx=5, pady=2)
            
            local_dir_entry = ctk.CTkEntry(local_header)
            local_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
            local_dir_entry.insert(0, self.current_local_dir)
            
            local_refresh_btn = ctk.CTkButton(local_header, text="↻", width=30,
                                            command=lambda: self._refresh_local_browser(local_tree, local_dir_entry))
            local_refresh_btn.pack(side=tk.RIGHT, padx=2, pady=2)
            
            local_up_btn = ctk.CTkButton(local_header, text="↑", width=30,
                                       command=lambda: self._local_up_directory(local_tree, local_dir_entry))
            local_up_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        else:
            local_header = ttk.Frame(local_frame)
            local_header.pack(fill=tk.X, padx=2, pady=2)
            ttk.Label(local_header, text=loc["local_directory"]).pack(side=tk.LEFT, padx=5, pady=2)
            
            local_dir_entry = ttk.Entry(local_header)
            local_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
            local_dir_entry.insert(0, self.current_local_dir)
            
            local_refresh_btn = ttk.Button(local_header, text="↻", width=3,
                                         command=lambda: self._refresh_local_browser(local_tree, local_dir_entry))
            local_refresh_btn.pack(side=tk.RIGHT, padx=2, pady=2)
            
            local_up_btn = ttk.Button(local_header, text="↑", width=3,
                                    command=lambda: self._local_up_directory(local_tree, local_dir_entry))
            local_up_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Local file tree
        local_tree_frame = ttk.Frame(local_frame)
        local_tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        local_tree = ttk.Treeview(local_tree_frame, columns=("size", "type", "modified"), show="tree headings")
        local_tree.heading("#0", text=loc["filename"])
        local_tree.heading("size", text=loc["filesize"])
        local_tree.heading("type", text=loc["filetype"])
        local_tree.heading("modified", text=loc["modified"])
        
        local_tree.column("#0", width=200)
        local_tree.column("size", width=80)
        local_tree.column("type", width=80)
        local_tree.column("modified", width=120)

        local_tree_scroll = ttk.Scrollbar(local_tree_frame, orient=tk.VERTICAL, command=local_tree.yview)
        local_tree.configure(yscrollcommand=local_tree_scroll.set)
        local_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        local_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        local_tree.bind("<Double-1>", lambda e: self._local_on_double(local_tree, local_dir_entry))

        # Remote file browser
        if CTK_AVAILABLE:
            remote_frame = ctk.CTkFrame(middle_paned)
        else:
            remote_frame = ttk.Frame(middle_paned)
        
        middle_paned.add(remote_frame, weight=1)

        # Remote directory header
        if CTK_AVAILABLE:
            remote_header = ctk.CTkFrame(remote_frame)
            remote_header.pack(fill=tk.X, padx=2, pady=2)
            ctk.CTkLabel(remote_header, text=loc["remote_directory"]).pack(side=tk.LEFT, padx=5, pady=2)
            
            remote_dir_entry = ctk.CTkEntry(remote_header)
            remote_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
            remote_dir_entry.insert(0, "/")
            
            remote_refresh_btn = ctk.CTkButton(remote_header, text="↻", width=30,
                                             command=lambda: self._refresh_remote_browser(remote_tree, remote_dir_entry))
            remote_refresh_btn.pack(side=tk.RIGHT, padx=2, pady=2)
            
            remote_up_btn = ctk.CTkButton(remote_header, text="↑", width=30,
                                        command=lambda: self._remote_up_directory(remote_tree, remote_dir_entry))
            remote_up_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        else:
            remote_header = ttk.Frame(remote_frame)
            remote_header.pack(fill=tk.X, padx=2, pady=2)
            ttk.Label(remote_header, text=loc["remote_directory"]).pack(side=tk.LEFT, padx=5, pady=2)
            
            remote_dir_entry = ttk.Entry(remote_header)
            remote_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
            remote_dir_entry.insert(0, "/")
            
            remote_refresh_btn = ttk.Button(remote_header, text="↻", width=3,
                                          command=lambda: self._refresh_remote_browser(remote_tree, remote_dir_entry))
            remote_refresh_btn.pack(side=tk.RIGHT, padx=2, pady=2)
            
            remote_up_btn = ttk.Button(remote_header, text="↑", width=3,
                                     command=lambda: self._remote_up_directory(remote_tree, remote_dir_entry))
            remote_up_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Remote file tree
        remote_tree_frame = ttk.Frame(remote_frame)
        remote_tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        remote_tree = ttk.Treeview(remote_tree_frame, columns=("size", "type", "modified", "permissions"), show="tree headings")
        remote_tree.heading("#0", text=loc["filename"])
        remote_tree.heading("size", text=loc["filesize"])
        remote_tree.heading("type", text=loc["filetype"])
        remote_tree.heading("modified", text=loc["modified"])
        remote_tree.heading("permissions", text=loc["permissions"])
        
        remote_tree.column("#0", width=200)
        remote_tree.column("size", width=80)
        remote_tree.column("type", width=80)
        remote_tree.column("modified", width=120)
        remote_tree.column("permissions", width=80)

        remote_tree_scroll = ttk.Scrollbar(remote_tree_frame, orient=tk.VERTICAL, command=remote_tree.yview)
        remote_tree.configure(yscrollcommand=remote_tree_scroll.set)
        remote_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        remote_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        remote_tree.bind("<Double-1>", lambda e: self._remote_on_double(remote_tree, remote_dir_entry))

        # Bottom section: Message log and transfer queue
        if CTK_AVAILABLE:
            bottom_frame = ctk.CTkFrame(paned_main)
        else:
            bottom_frame = ttk.Frame(paned_main)
        
        paned_main.add(bottom_frame, weight=0)

        # Message log
        if CTK_AVAILABLE:
            log_label = ctk.CTkLabel(bottom_frame, text=loc["message_log"])
            log_label.pack(anchor="w", padx=5, pady=2)
        else:
            log_label = ttk.Label(bottom_frame, text=loc["message_log"])
            log_label.pack(anchor="w", padx=5, pady=2)

        log_text = tk.Text(bottom_frame, height=6, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Button bar
        if CTK_AVAILABLE:
            button_frame = ctk.CTkFrame(win)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ctk.CTkButton(button_frame, text="⬆ Upload", command=lambda: self.ftp_upload_filezilla(local_tree, remote_tree)).pack(side=tk.LEFT, padx=2)
            ctk.CTkButton(button_frame, text="⬇ Download", command=lambda: self.ftp_download_filezilla(local_tree, remote_tree)).pack(side=tk.LEFT, padx=2)
            ctk.CTkButton(button_frame, text="↻ Refresh Local", command=lambda: self._refresh_local_browser(local_tree, local_dir_entry)).pack(side=tk.LEFT, padx=2)
            ctk.CTkButton(button_frame, text="↻ Refresh Remote", command=lambda: self._refresh_remote_browser(remote_tree, remote_dir_entry)).pack(side=tk.LEFT, padx=2)
            ctk.CTkButton(button_frame, text=loc["edit_meta"], command=lambda: self._ftp_open_meta_if_selected_filezilla(remote_tree)).pack(side=tk.LEFT, padx=2)
            ctk.CTkButton(button_frame, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=2)
        else:
            button_frame = ttk.Frame(win)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Button(button_frame, text="⬆ Upload", command=lambda: self.ftp_upload_filezilla(local_tree, remote_tree)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="⬇ Download", command=lambda: self.ftp_download_filezilla(local_tree, remote_tree)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="↻ Refresh Local", command=lambda: self._refresh_local_browser(local_tree, local_dir_entry)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="↻ Refresh Remote", command=lambda: self._refresh_remote_browser(remote_tree, remote_dir_entry)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text=loc["edit_meta"], command=lambda: self._ftp_open_meta_if_selected_filezilla(remote_tree)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=2)

        # Store references
        self.ftp_win = win
        self.ftp_host_entry = host_entry
        self.ftp_user_entry = user_entry
        self.ftp_pwd_entry = pwd_entry
        self.ftp_status_label = status_label
        self.ftp_log_text = log_text
        self.local_tree = local_tree
        self.remote_tree = remote_tree
        self.local_dir_entry = local_dir_entry
        self.remote_dir_entry = remote_dir_entry

        # Populate local browser initially
        self._refresh_local_browser(local_tree, local_dir_entry)

    def _refresh_local_browser(self, tree, dir_entry):
        path = dir_entry.get()
        if not os.path.exists(path):
            path = os.path.expanduser("~")
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, path)
        
        self.current_local_dir = path
        
        tree.delete(*tree.get_children())
        
        # Add parent directory entry
        if path != os.path.dirname(path):  # Not root
            tree.insert("", "end", text="..", values=("", "Directory", "", ""))
        
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    tree.insert("", "end", text=item, values=("", "Directory", 
                                                            time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(full_path))), ""))
                else:
                    size = human_size(os.path.getsize(full_path))
                    ext = os.path.splitext(item)[1].lower()
                    file_type = "File"
                    if ext in [".txt", ".xml", ".json", ".yaml", ".yml"]:
                        file_type = "Text"
                    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tga"]:
                        file_type = "Image"
                    elif ext in [".py", ".c", ".cpp", ".h", ".java"]:
                        file_type = "Code"
                    
                    tree.insert("", "end", text=item, values=(size, file_type, 
                                                            time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(full_path))), ""))
        except PermissionError:
            self._log_message("Permission denied accessing: " + path)

    def _local_up_directory(self, tree, dir_entry):
        current = dir_entry.get()
        parent = os.path.dirname(current)
        if parent and os.path.exists(parent):
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, parent)
            self._refresh_local_browser(tree, dir_entry)

    def _local_on_double(self, tree, dir_entry):
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        name = item["text"]
        
        if name == "..":
            self._local_up_directory(tree, dir_entry)
        else:
            current_path = dir_entry.get()
            new_path = os.path.join(current_path, name)
            
            if os.path.isdir(new_path):
                dir_entry.delete(0, tk.END)
                dir_entry.insert(0, new_path)
                self._refresh_local_browser(tree, dir_entry)

    def _refresh_remote_browser(self, tree, dir_entry):
        if not self.ftp.connected:
            self._log_message("Not connected to FTP server")
            return
        
        path = dir_entry.get()
        
        try:
            self.ftp.cwd(path)
            items = []
            try:
                self.ftp.ftp.retrlines("MLSD", items.append)
                
                tree.delete(*tree.get_children())
                
                # Add parent directory
                if path != "/":
                    tree.insert("", "end", text="..", values=("", "Directory", "", ""))
                
                for line in items:
                    parts = line.split(";")
                    name = parts[-1].strip()
                    
                    # Parse facts
                    facts = {}
                    for part in parts[:-1]:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            facts[key.strip()] = value.strip()
                    
                    if "type" in facts:
                        if facts["type"] == "dir":
                            tree.insert("", "end", text=name, values=("", "Directory", 
                                                                    facts.get("modify", ""), facts.get("perm", "")))
                        else:
                            size = human_size(int(facts.get("size", 0)))
                            ext = os.path.splitext(name)[1].lower()
                            file_type = "File"
                            if ext in [".txt", ".xml", ".json", ".yaml", ".yml"]:
                                file_type = "Text"
                            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tga"]:
                                file_type = "Image"
                            
                            tree.insert("", "end", text=name, values=(size, file_type, 
                                                                    facts.get("modify", ""), facts.get("perm", "")))
            except Exception:
                # Fallback to NLST if MLSD not supported
                names = self.ftp.nlst()
                tree.delete(*tree.get_children())
                
                if path != "/":
                    tree.insert("", "end", text="..", values=("", "Directory", "", ""))
                
                for name in names:
                    try:
                        size = self.ftp.size(name)
                        if size == 0:
                            tree.insert("", "end", text=name, values=("", "Directory", "", ""))
                        else:
                            size_str = human_size(size)
                            ext = os.path.splitext(name)[1].lower()
                            file_type = "File"
                            if ext in [".txt", ".xml", ".json", ".yaml", ".yml"]:
                                file_type = "Text"
                            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tga"]:
                                file_type = "Image"
                            
                            tree.insert("", "end", text=name, values=(size_str, file_type, "", ""))
                    except:
                        tree.insert("", "end", text=name, values=("", "Directory", "", ""))
            
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, self.ftp.pwd())
            self.current_remote_dir = self.ftp.pwd()
            
        except Exception as e:
            self._log_message(f"Error refreshing remote browser: {str(e)}")

    def _remote_up_directory(self, tree, dir_entry):
        if not self.ftp.connected:
            return
        
        current = dir_entry.get()
        if current == "/":
            return
        
        parent = "/".join(current.split("/")[:-1])
        if not parent:
            parent = "/"
        
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, parent)
        self._refresh_remote_browser(tree, dir_entry)

    def _remote_on_double(self, tree, dir_entry):
        if not self.ftp.connected:
            return
        
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        name = item["text"]
        
        if name == "..":
            self._remote_up_directory(tree, dir_entry)
        else:
            try:
                # Try to change to directory
                self.ftp.cwd(name)
                self._refresh_remote_browser(tree, dir_entry)
            except:
                # If it's a file, download it
                if messagebox.askyesno("Download", f"Download '{name}'?"):
                    self.ftp_download_filezilla(self.local_tree, self.remote_tree)

    def _log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.ftp_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.ftp_log_text.see(tk.END)

    def _ftp_connect_and_populate(self, host, user, pwd, win):
        try:
            self._log_message(f"Connecting to {host}...")
            self.ftp.connect(host, user or "anonymous", pwd or "", 
                           port=cfg.get("ftp_port",21), timeout=cfg.get("timeout",30), 
                           passive=cfg.get("ftp_passive", True))
            self.ftp_status_label.configure(text=f"{get_locale()['status']} Connected to {host}")
            self._log_message(f"Connected to {host}")
            self._refresh_remote_browser(self.remote_tree, self.remote_dir_entry)
        except Exception as e:
            self._log_message(f"Connection failed: {str(e)}")
            messagebox.showerror("FTP Error", str(e))

    def _ftp_disconnect(self):
        if self.ftp.connected:
            self.ftp.disconnect()
            self.ftp_status_label.configure(text=f"{get_locale()['status']} Not connected")
            self._log_message("Disconnected from server")
            self.remote_tree.delete(*self.remote_tree.get_children())

    def ftp_upload_filezilla(self, local_tree, remote_tree):
        if not self.ftp.connected:
            messagebox.showwarning("FTP", "Not connected to FTP server.")
            return
        
        local_selection = local_tree.selection()
        if not local_selection:
            messagebox.showwarning("Select", "Select a local file to upload.")
            return
        
        item = local_tree.item(local_selection[0])
        name = item["text"]
        
        if name == "..":
            messagebox.showwarning("Select", "Cannot upload parent directory.")
            return
        
        local_path = os.path.join(self.current_local_dir, name)
        
        if os.path.isdir(local_path):
            messagebox.showwarning("Upload", "Directory upload not supported yet.")
            return
        
        self._show_progress(f"Uploading {name}")
        self.progress_var.set(0)
        self.speed_var.set(f"{get_locale().get('speed','Speed:')} 0 KB/s")

        def progress_cb(done, total, speed):
            pct = (done / total * 100) if total else 0
            self.progress_var.set(pct)
            self.speed_var.set(f"{get_locale().get('speed','Speed:')} {speed/1024:.1f} KB/s")
            try:
                if self.progress_window:
                    self.progress_window.update_idletasks()
            except Exception:
                pass

        def task():
            try:
                with open(local_path, "rb") as fd:
                    self.ftp.storbinary_from_fd(name, fd, progress_callback=progress_cb)
                self._log_message(f"Uploaded: {name}")
                self._refresh_remote_browser(self.remote_tree, self.remote_dir_entry)
                messagebox.showinfo("Done", "Upload complete.")
            except Exception as e:
                self._log_message(f"Upload failed: {str(e)}")
                messagebox.showerror("Upload Error", str(e))
            finally:
                try:
                    if getattr(self, "progress_window", None):
                        self.progress_window.destroy()
                        self.progress_window = None
                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()

    def ftp_download_filezilla(self, local_tree, remote_tree):
        if not self.ftp.connected:
            messagebox.showwarning("FTP", "Not connected to FTP server.")
            return
        
        remote_selection = remote_tree.selection()
        if not remote_selection:
            messagebox.showwarning("Select", "Select a remote file to download.")
            return
        
        item = remote_tree.item(remote_selection[0])
        name = item["text"]
        
        if name == "..":
            messagebox.showwarning("Select", "Cannot download parent directory.")
            return
        
        local_path = os.path.join(self.current_local_dir, name)
        
        self._show_progress(f"Downloading {name}")
        self.progress_var.set(0)
        self.speed_var.set(f"{get_locale().get('speed','Speed:')} 0 KB/s")

        def progress_cb(done, total, speed):
            pct = (done / total * 100) if total else 0
            self.progress_var.set(pct)
            self.speed_var.set(f"{get_locale().get('speed','Speed:')} {speed/1024:.1f} KB/s")
            try:
                if self.progress_window:
                    self.progress_window.update_idletasks()
            except Exception:
                pass

        def task():
            try:
                with open(local_path, "wb") as f:
                    self.ftp.retrbinary_to_fd(name, f, progress_callback=progress_cb)
                self._log_message(f"Downloaded: {name}")
                self._refresh_local_browser(self.local_tree, self.local_dir_entry)
                messagebox.showinfo("Done", "Download complete.")
            except Exception as e:
                self._log_message(f"Download failed: {str(e)}")
                messagebox.showerror("Download Error", str(e))
            finally:
                try:
                    if getattr(self, "progress_window", None):
                        self.progress_window.destroy()
                        self.progress_window = None
                except Exception:
                    pass

        threading.Thread(target=task, daemon=True).start()

    def _ftp_open_meta_if_selected_filezilla(self, remote_tree):
        if not self.ftp.connected:
            messagebox.showwarning("FTP", "Not connected to FTP server.")
            return
        
        remote_selection = remote_tree.selection()
        if not remote_selection:
            messagebox.showwarning("Select", "Select a remote file.")
            return
        
        item = remote_tree.item(remote_selection[0])
        name = item["text"]
        
        if name.lower() != "meta.xml":
            messagebox.showinfo("Info", "Select meta.xml to edit.")
            return
        
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
            with open(tmp.name, "wb") as f:
                self.ftp.retrbinary(f"RETR meta.xml", f.write)
            self._open_meta_editor_structured(tmp.name, remote_name="meta.xml", is_remote=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open meta.xml: {e}")

    # -------------------------
    # Simple text viewer
    # -------------------------
    def _open_text_viewer(self, path, title="File"):
        win = tk.Toplevel(self.root)
        win.title(title)
        txt = tk.Text(win, wrap="none")
        txt.pack(fill="both", expand=True)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                txt.insert("1.0", f.read())
        except Exception as e:
            txt.insert("1.0", f"Failed to open: {e}")

    # -------------------------
    # Download / Upload with progress UI
    # -------------------------
    def _show_progress(self, title):
        if hasattr(self, "progress_window") and getattr(self, "progress_window", None):
            try:
                self.progress_window.destroy()
            except Exception:
                pass
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("420x120")
            ctk.CTkLabel(win, text=title).pack(pady=6)
            pb = ctk.CTkProgressBar(win, variable=self.progress_var)
            pb.set(0)
            pb.pack(fill="x", padx=12, pady=8)
            ctk.CTkLabel(win, textvariable=self.speed_var).pack()
        else:
            win = tk.Toplevel(self.root)
            win.geometry("420x120")
            tk.Label(win, text=title).pack(pady=6)
            try:
                from tkinter.ttk import Progressbar
                pb = Progressbar(win, variable=self.progress_var, maximum=100)
                pb.pack(fill="x", padx=12, pady=8)
            except Exception:
                pass
            tk.Label(win, textvariable=self.speed_var).pack()
        self.progress_window = win

    # -------------------------
    # WiiU file selector (.szs, .params)
    # -------------------------
    def open_wiiu_files(self):
        loc = get_locale()
        files = filedialog.askopenfilenames(title=loc.get("select_file", "Select a file"),
                                            filetypes=[("WiiU files", "*.szs *.params"), ("All files", "*.*")])
        if not files:
            return
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("520x320")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("520x320")
        win.title("WiiU Files")
        listbox = tk.Listbox(win)
        listbox.pack(fill="both", expand=True, padx=8, pady=8)
        for f in files:
            listbox.insert("end", f)
        def open_selected():
            sel = listbox.curselection()
            if not sel:
                return
            path = listbox.get(sel[0])
            try:
                size = os.path.getsize(path)
                if size < 200_000:
                    self._open_text_viewer(path, title=os.path.basename(path))
                else:
                    messagebox.showinfo("File", f"File selected: {path}\nSize: {human_size(size)} (too large to display)")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        if CTK_AVAILABLE:
            ctk.CTkButton(win, text="Open selected", command=open_selected).pack(side="left", padx=8, pady=(0,8))
            ctk.CTkButton(win, text="Close", command=win.destroy).pack(side="right", padx=8, pady=(0,8))
        else:
            tk.Button(win, text="Open selected", command=open_selected).pack(side="left", padx=8, pady=(0,8))
            tk.Button(win, text="Close", command=win.destroy).pack(side="right", padx=8, pady=(0,8))

    # -------------------------
    # Models / BFRES / BYAML / PACK tools (new)
    # -------------------------
    def open_models_window(self):
        loc = get_locale()
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.geometry("520x320")
        else:
            win = tk.Toplevel(self.root)
            win.geometry("520x320")
        win.title("Models & Packs")
        win.transient(self.root)

        if CTK_AVAILABLE:
            frm = ctk.CTkFrame(win)
            frm.pack(fill="both", expand=True, padx=12, pady=12)
            ctk.CTkLabel(frm, text="BYAML, BFRES and PACK utilities", anchor="w").pack(padx=6, pady=(0,8))
            ctk.CTkButton(frm, text="BYAML → YAML", command=lambda: threading.Thread(target=self.on_byaml_to_yaml, daemon=True).start()).pack(fill="x", pady=6)
            ctk.CTkButton(frm, text="YAML → BYAML", command=lambda: threading.Thread(target=self.on_yaml_to_byaml, daemon=True).start()).pack(fill="x", pady=6)
            ctk.CTkButton(frm, text="BFRES → OBJ/GLTF (Blender preferred)", command=lambda: threading.Thread(target=self.on_bfres_to_obj, daemon=True).start()).pack(fill="x", pady=6)
            ctk.CTkButton(frm, text="Open BFRES Viewer (OBJ/BFRES)", command=lambda: threading.Thread(target=self.on_open_bfres_viewer, daemon=True).start()).pack(fill="x", pady=6)
            ctk.CTkButton(frm, text="Open PACK Editor (SARC/Yaz0)", command=lambda: threading.Thread(target=self.on_open_pack_editor, daemon=True).start()).pack(fill="x", pady=6)
            ctk.CTkButton(frm, text="Close", command=win.destroy).pack(side="right", pady=(8,0))
        else:
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True, padx=8, pady=8)
            tk.Label(frm, text="BYAML, BFRES and PACK utilities", anchor="w").pack(padx=6, pady=(0,8))
            tk.Button(frm, text="BYAML → YAML", command=lambda: threading.Thread(target=self.on_byaml_to_yaml, daemon=True).start()).pack(fill="x", pady=6)
            tk.Button(frm, text="YAML → BYAML", command=lambda: threading.Thread(target=self.on_yaml_to_byaml, daemon=True).start()).pack(fill="x", pady=6)
            tk.Button(frm, text="BFRES → OBJ/GLTF (Blender preferred)", command=lambda: threading.Thread(target=self.on_bfres_to_obj, daemon=True).start()).pack(fill="x", pady=6)
            tk.Button(frm, text="Open BFRES Viewer (OBJ/BFRES)", command=lambda: threading.Thread(target=self.on_open_bfres_viewer, daemon=True).start()).pack(fill="x", pady=6)
            tk.Button(frm, text="Open PACK Editor (SARC/Yaz0)", command=lambda: threading.Thread(target=self.on_open_pack_editor, daemon=True).start()).pack(fill="x", pady=6)
            tk.Button(frm, text="Close", command=win.destroy).pack(side="right", pady=(8,0))

    # BYAML ↔ YAML conversions (delegated to helper CLI)
    def on_byaml_to_yaml(self):
        path = filedialog.askopenfilename(title="Open BYAML/BYML", filetypes=[("BYML files","*.byml;*.byaml;*.byml.bin"),("All","*.*")])
        if not path:
            return
        out = filedialog.asksaveasfilename(title="Save YAML", defaultextension=".yaml", filetypes=[("YAML","*.yaml;*.yml")])
        if not out:
            return
        try:
            script = os.path.join(os.path.dirname(__file__), "byaml_converter.py")
            if not os.path.exists(script):
                messagebox.showerror("BYAML → YAML", "byaml_converter.py not found next to main.py")
                return
            cmd = [sys.executable, script, "to-yaml", path, out]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                messagebox.showinfo("BYAML → YAML", f"Converted to YAML: {out}")
            else:
                messagebox.showerror("BYAML → YAML", f"Failed:\n{proc.stderr}")
        except Exception as e:
            messagebox.showerror("BYAML → YAML", str(e))

    def on_yaml_to_byaml(self):
        path = filedialog.askopenfilename(title="Open YAML", filetypes=[("YAML","*.yaml;*.yml")])
        if not path:
            return
        out = filedialog.asksaveasfilename(title="Save BYML/BYAML", defaultextension=".byml", filetypes=[("BYML","*.byml;*.byaml")])
        if not out:
            return
        try:
            script = os.path.join(os.path.dirname(__file__), "byaml_converter.py")
            if not os.path.exists(script):
                messagebox.showerror("YAML → BYAML", "byaml_converter.py not found next to main.py")
                return
            cmd = [sys.executable, script, "from-yaml", path, out]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                messagebox.showinfo("YAML → BYAML", f"Wrote BYML: {out}")
            else:
                messagebox.showerror("YAML → BYAML", f"Failed:\n{proc.stderr}")
        except Exception as e:
            messagebox.showerror("YAML → BYAML", str(e))

    # BFRES -> OBJ/GLTF export (delegated to helper scripts)
    def on_bfres_to_obj(self):
        path = filedialog.askopenfilename(title="Open BFRES", filetypes=[("BFRES","*.bfres"),("All","*.*")])
        if not path:
            return
        out = filedialog.asksaveasfilename(title="Export OBJ/GLTF", defaultextension=".obj", filetypes=[("OBJ","*.obj"),("glTF","*.gltf;*.glb")])
        if not out:
            return
        try:
            # Prefer Blender wrapper if present (more robust). Fallback to bfres_basic.
            blender_wrapper = os.path.join(os.path.dirname(__file__), "bfres_wrapper.py")
            basic_converter = os.path.join(os.path.dirname(__file__), "bfres_basic.py")
            if os.path.exists(blender_wrapper):
                cmd = [sys.executable, blender_wrapper, "--input", path, "--output", out]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    messagebox.showinfo("BFRES → OBJ", f"Exported using Blender wrapper to {out}")
                    return
                # fallthrough if wrapper failed
            if os.path.exists(basic_converter):
                cmd = [sys.executable, basic_converter, path, out]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    messagebox.showinfo("BFRES → OBJ", f"Exported (basic) to {out}")
                else:
                    messagebox.showerror("BFRES → OBJ", f"Failed:\n{proc.stderr}\n{proc.stdout}")
            else:
                messagebox.showerror("BFRES → OBJ", "No converter found (bfres_wrapper.py or bfres_basic.py missing).")
        except Exception as e:
            messagebox.showerror("BFRES → OBJ", str(e))

    # BFRES viewer (launches external viewer)
    def on_open_bfres_viewer(self):
        path = filedialog.askopenfilename(title="Open model (OBJ or BFRES)", filetypes=[("OBJ","*.obj"),("BFRES","*.bfres"),("All","*.*")])
        if not path:
            return
        viewer = os.path.join(os.path.dirname(__file__), "bfres_viewer.py")
        if not os.path.exists(viewer):
            messagebox.showerror("Viewer", "bfres_viewer.py not found in project folder.")
            return
        try:
            cmd = [sys.executable, viewer, path]
            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen(cmd)
        except Exception as e:
            messagebox.showerror("Viewer", str(e))

    # PACK editor (SARC/Yaz0) - launches external pack_editor.py
    def on_open_pack_editor(self):
        path = filedialog.askopenfilename(title="Open PACK/SARC/Yaz0", filetypes=[("PACK/SARC/Yaz0 files","*.pack;*.sarc;*.szs;*.yaz0;*.szs"),("All","*.*")])
        if not path:
            return
        editor = os.path.join(os.path.dirname(__file__), "pack_editor.py")
        if not os.path.exists(editor):
            messagebox.showerror("Pack Editor", "pack_editor.py not found next to main.py")
            return
        try:
            cmd = [sys.executable, editor, path]
            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen(cmd)
        except Exception as e:
            messagebox.showerror("Pack Editor", str(e))

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

    app = ModernCTkApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
