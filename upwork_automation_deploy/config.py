import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "gmail_user": "dummy.upwork.bot@gmail.com",
    "drive_folder_id": "DUMMY_FOLDER_ID",
    "auto_reply": True,
    "confidence_threshold": 0.5,
    "check_interval": "5 minutes",
    "default_reply": "Thank you for your message. Our team will get back to you shortly.",
    "upwork_email_identifier": "upwork.com",
    "dummy_mode": True
}

class Config:
    def __init__(self):
        self._data = self._load()

    def _load(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        return DEFAULT_CONFIG.copy()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def update(self, updates: dict):
        self._data.update(updates)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self._data, f, indent=2)

    def is_dummy_mode(self):
        return self._data.get('dummy_mode', True)
