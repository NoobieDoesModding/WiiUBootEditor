import os
import json
import logging
from pathlib import Path
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from Info import USER_DIR, USER_CFG, DEFAULT_CFG
from Locales import LOCALES

# Setup logging
log_file = USER_DIR / "wiiu_boot_editor.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_cfg():
    try:
        if USER_CFG.exists():
            with open(USER_CFG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CFG.items():
                cfg.setdefault(k, v)
            return cfg
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
    cfg = DEFAULT_CFG.copy()
    # Set default icon if not set
    if "icon_path" not in cfg or not cfg["icon_path"]:
        cfg["icon_path"] = os.path.join(os.path.dirname(__file__), "Icon", "nintendo-wii-u.jpg")
    return cfg

def save_cfg(cfg):
    try:
        with open(USER_CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save config: {e}")

cfg = load_cfg()

def get_locale():
    return LOCALES.get(cfg.get("language", "English"), LOCALES["English"])

def convert_to_tga(src, dst, size, bits):
    if not PIL_AVAILABLE:
        raise ImportError("Pillow not available")
    try:
        img = Image.open(src).convert("RGBA" if bits == 32 else "RGB")
        img = img.resize(size, Image.LANCZOS)
        img.save(dst, format="TGA")
        logging.info(f"Converted {src} to TGA {dst}")
    except Exception as e:
        logging.error(f"Failed to convert to TGA: {e}")
        raise