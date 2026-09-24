import json
import os
from pathlib import Path
from cryptography.fernet import Fernet

DATA_DIR = Path("/data")
SETTINGS_FILE = DATA_DIR / "settings.json"
KEY_FILE = DATA_DIR / "secret.key"

DEFAULTS = {
    "ollama_url": os.getenv("OLLAMA_URL", "http://ollama:11434"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
    "whisper_model": os.getenv("WHISPER_MODEL", "small"),
    "whisper_device": os.getenv("WHISPER_DEVICE", "cpu"),
    "whisper_compute_type": os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
    "piper_url": os.getenv("PIPER_URL", "http://piper:5000"),
    "piper_voice": os.getenv("PIPER_VOICE", "pl_PL-mc_speech-medium"),
    "icp_instance": "",
    "icp_token_enc": "",
    "icp_board_column": "",
    "icp_priority": "normal",
    "audiosocket_host": "0.0.0.0",
    "audiosocket_port": int(os.getenv("AUDIOSOCKET_PORT", "9019")),
    "greeting": "Dzień dobry. Tu automatyczny asystent serwisu. Proszę opisać problem.",
    "system_prompt": (
        "Jesteś polskim asystentem helpdesku. Rozmawiasz krótko i konkretnie. "
        "Zbierz nazwę klienta lub firmy, opis problemu, zakres problemu, pilność "
        "oraz dane kontaktowe, jeżeli są potrzebne. Nie wymyślaj danych. "
        "Kiedy masz wystarczające informacje, ustaw done=true. "
        "Zawsze zwracaj wyłącznie poprawny JSON."
    ),
    "max_turns": int(os.getenv("MAX_TURNS", "8")),
    "silence_ms": int(os.getenv("SILENCE_MS", "900")),
}

def _fernet():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        KEY_FILE.write_bytes(Fernet.generate_key())
        KEY_FILE.chmod(0o600)
    return Fernet(KEY_FILE.read_bytes())

def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode() if value else ""

def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode()).decode()
    except Exception:
        return ""

def load_settings():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = DEFAULTS.copy()
    if SETTINGS_FILE.exists():
        try:
            data.update(json.loads(SETTINGS_FILE.read_text()))
        except Exception:
            pass
    return data

def save_settings(data):
    current = load_settings()
    current.update(data)
    SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2))
    SETTINGS_FILE.chmod(0o600)
    return current
