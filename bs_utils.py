import os
import re
import json
import threading
from datetime import datetime

# Kredensial & konfigurasi build (diambil dari environment variable)
USERNAME = os.getenv("BROWSERSTACK_USERNAME")
ACCESS_KEY = os.getenv("BROWSERSTACK_ACCESS_KEY")

# Build name dipakai supaya tiap run Jenkins jadi 1 build terpisah di
# BrowserStack. Di Jenkins kita set lewat env BUILD_NAME.
BUILD_NAME = os.getenv("BUILD_NAME", datetime.now().strftime("Local Run %Y-%m-%d %H:%M:%S"))
PROJECT_NAME = os.getenv("BROWSERSTACK_PROJECT", "Mobile Compatibility Testing")

HUB_URL = "https://hub.browserstack.com/wd/hub"

# Folder output hasil per-device (dibaca oleh generate_report.py)
RESULTS_DIR = os.getenv("RESULTS_DIR", "results")


def require_credentials():
    """Pastikan kredensial tersedia, kalau tidak hentikan dengan pesan jelas."""
    if not USERNAME or not ACCESS_KEY:
        raise SystemExit(
            "ERROR: BROWSERSTACK_USERNAME / BROWSERSTACK_ACCESS_KEY belum di-set.\n"
            "Set dulu environment variable-nya, contoh:\n"
            "  export BROWSERSTACK_USERNAME='xxx'\n"
            "  export BROWSERSTACK_ACCESS_KEY='yyy'\n"
            "Di Jenkins ini di-inject otomatis lewat credentials binding."
        )


def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


class ResultRecorder:
    """Merekam hasil test tiap device ke file JSON terpisah (thread-safe)."""

    def __init__(self, suite_name, app_id):
        self.suite_name = suite_name
        self.app_id = app_id
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, device_name, platform_version, status,
               started_at, ended_at, error=None, session_id=None,
               public_url=None):
        record = {
            "suite": self.suite_name,
            "app_id": self.app_id,
            "build_name": BUILD_NAME,
            "device_name": device_name,
            "platform_name": "Android",
            "platform_version": platform_version,
            "status": status,  # "passed" | "failed"
            "started_at": started_at.isoformat(timespec="seconds"),
            "ended_at": ended_at.isoformat(timespec="seconds"),
            "duration_seconds": round((ended_at - started_at).total_seconds(), 1),
            "error": (str(error)[:500] if error else None),
            "session_id": session_id,
            "public_url": public_url,
        }
        filename = f"{_slug(self.suite_name)}__{_slug(device_name)}.json"
        path = os.path.join(RESULTS_DIR, filename)
        # Tiap device file sendiri, tapi tetap kunci untuk aman.
        with self._lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
        return path


def get_session_meta(driver):
    """Best-effort ambil session_id & public dashboard URL dari BrowserStack."""
    session_id = None
    public_url = None
    try:
        session_id = driver.session_id
    except Exception:
        pass
    try:
        details = driver.execute_script('browserstack_executor: {"action": "getSessionDetails"}')
        if isinstance(details, str):
            details = json.loads(details)
        if isinstance(details, dict):
            public_url = details.get("public_url") or details.get("browser_url")
    except Exception:
        pass
    return session_id, public_url
