import os
import requests
import json
import shutil

# Define the root directory for the application
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
SETTINGS_DIR = os.path.join(ROOT_DIR, "settings")
DEFAULT_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "DefaultSettings")
USER_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "UserSettings")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
TEMP_FILES_DELETER_DIR = os.path.join(SCRIPTS_DIR, "TempFilesDeleter")

# GitHub repository information
GITHUB_REPO = "Rieversed/Insomnia.cc"
GITHUB_BRANCH = "main"

def download_github_directory(repo, branch, path, local_dir):
    """
    Download all files from a GitHub directory.
    """
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url)
    if response.status_code == 200:
        contents = json.loads(response.text)
        for item in contents:
            if item['type'] == 'file':
                file_url = item['download_url']
                local_path = os.path.join(local_dir, item['name'])
                download_file(file_url, local_path)
            elif item['type'] == 'dir':
                new_local_dir = os.path.join(local_dir, item['name'])
                os.makedirs(new_local_dir, exist_ok=True)
                download_github_directory(repo, branch, item['path'], new_local_dir)

def download_file(url, local_path):
    """
    Download a single file from a URL.
    """
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {local_path}")
    else:
        print(f"Failed to download: {url}")

def update_files():
    """
    Update all files from the GitHub repository.
    """
    # Create necessary directories
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(DEFAULT_SETTINGS_DIR, exist_ok=True)
    os.makedirs(USER_SETTINGS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(TEMP_FILES_DELETER_DIR, exist_ok=True)

    # Update assets
    download_github_directory(GITHUB_REPO, GITHUB_BRANCH, "assets", ASSETS_DIR)

    # Update default settings
    download_github_directory(GITHUB_REPO, GITHUB_BRANCH, "DefaultSettings", DEFAULT_SETTINGS_DIR)

    # Update TempFilesDeleter scripts
    download_github_directory(GITHUB_REPO, GITHUB_BRANCH, "scripts/TempFilesDeleter", TEMP_FILES_DELETER_DIR)

    # Copy default settings to user settings if they don't exist
    for file in os.listdir(DEFAULT_SETTINGS_DIR):
        default_file_path = os.path.join(DEFAULT_SETTINGS_DIR, file)
        user_file_path = os.path.join(USER_SETTINGS_DIR, file)
        if not os.path.exists(user_file_path):
            shutil.copy2(default_file_path, user_file_path)
            print(f"Copied {file} to user settings")

if __name__ == "__main__":
    update_files()
