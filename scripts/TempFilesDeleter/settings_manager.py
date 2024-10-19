import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_DIR = os.path.join(ROOT_DIR, "settings")
DEFAULT_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "DefaultSettings")
USER_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "UserSettings")
USER_SETTINGS_FILE = os.path.join(USER_SETTINGS_DIR, "TempFileDSettings.json")
DEFAULT_SETTINGS_FILE = os.path.join(DEFAULT_SETTINGS_DIR, "TempFileDSettings.json")

def load_settings():
    if os.path.exists(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    else:
        settings = fetch_default_settings()
    
    return settings

def fetch_default_settings():
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        print("Successfully loaded default settings from file.")
    else:
        print("Default settings file not found. Using minimal default settings.")
        settings = {'directories': {"%TEMP%": True}, 'move_to_trash': True, 'skip_errors': False, 'clear_recycle_bin': False}
    
    # Save to user settings
    with open(USER_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    
    return settings

def save_settings(settings):
    with open(USER_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
