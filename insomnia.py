import sys
import os
import ctypes
import logging
from datetime import datetime
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QCheckBox, QLineEdit, QScrollArea,
                             QProgressBar, QMessageBox, QFrame, QMenu, QLabel)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent, QAction
import winshell
import subprocess
import requests

# Define the root directory for the application
ROOT_DIR = "C:/Insomnia.cc"
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
SETTINGS_DIR = os.path.join(ROOT_DIR, "settings")
DEFAULT_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "DefaultSettings")
USER_SETTINGS_DIR = os.path.join(SETTINGS_DIR, "UserSettings")
USER_SETTINGS_FILE = os.path.join(USER_SETTINGS_DIR, "TempFileDSettings.json")
DEFAULT_SETTINGS_FILE = os.path.join(DEFAULT_SETTINGS_DIR, "TempFileDSettings.json")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
ERROR_LOGS_DIR = os.path.join(LOGS_DIR, "errors")
OLD_LOGS_DIR = os.path.join(ERROR_LOGS_DIR, "old")

# Create necessary directories
os.makedirs(ROOT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(DEFAULT_SETTINGS_DIR, exist_ok=True)
os.makedirs(USER_SETTINGS_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(ERROR_LOGS_DIR, exist_ok=True)
os.makedirs(OLD_LOGS_DIR, exist_ok=True)

# Set up logging
def setup_logging():
    log_file = os.path.join(ERROR_LOGS_DIR, 'insomnia_error.log')
    logging.basicConfig(filename=log_file, level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Limit old log files to 5
    old_logs = sorted([f for f in os.listdir(OLD_LOGS_DIR) if f.startswith('insomnia_error_')], reverse=True)
    for old_log in old_logs[4:]:  # Keep only the 5 most recent logs
        os.remove(os.path.join(OLD_LOGS_DIR, old_log))

setup_logging()

def log_error(message):
    logging.error(message)
    current_log = os.path.join(ERROR_LOGS_DIR, 'insomnia_error.log')
    if os.path.exists(current_log) and os.path.getsize(current_log) > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        old_log_file = os.path.join(OLD_LOGS_DIR, f'insomnia_error_{timestamp}.log')
        shutil.move(current_log, old_log_file)
        setup_logging()  # Reset the log file

def check_for_updates():
    update_script_url = "https://raw.githubusercontent.com/Rieversed/Insomnia.cc/main/scripts/update_files.py"
    update_script_path = os.path.join(SCRIPTS_DIR, "update_files.py")
    
    try:
        response = requests.get(update_script_url)
        response.raise_for_status()
        with open(update_script_path, 'wb') as f:
            f.write(response.content)
        subprocess.run([sys.executable, update_script_path], check=True)
        print("Files updated successfully.")
    except Exception as e:
        print(f"Error updating files: {e}")

class InsomniaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insomnia")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #ffffff;
                color: #1e1e1e;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit, QListWidget, QProgressBar {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
            }
            QCheckBox {
                color: #ffffff;
            }
        """)

        self.central_widget = QWidget()
        self.central_widget.setObjectName("roundedCorners")
        self.central_widget.setStyleSheet("""
            #roundedCorners {
                background-color: #1e1e1e;
                border-radius: 10px;
            }
        """)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.create_title_bar()
        self.layout.addStretch(1)
        self.create_main_buttons()
        self.create_progress_bar()
        self.layout.addStretch(1)

        self.load_settings()
        self.create_settings_widget()
        self.settings_widget.hide()

        self.oldPos = self.pos()

        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(10)

        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            app_icon_label = QLabel()
            app_icon_label.setPixmap(QIcon(icon_path).pixmap(24, 24))
            title_bar_layout.addWidget(app_icon_label)

        title_label = QLabel("Insomnia")
        title_label.setStyleSheet("font-weight: bold; font-size: 24px;")
        title_bar_layout.addWidget(title_label)

        title_bar_layout.addStretch()

        restart_button = QPushButton()
        restart_button.setFixedSize(25, 25)
        restart_button.setStyleSheet("background-color: #00FF00; border-radius: 12px;")
        restart_icon_path = os.path.join(ASSETS_DIR, "restart.png")
        if os.path.exists(restart_icon_path):
            restart_button.setIcon(QIcon(restart_icon_path))
        restart_button.setIconSize(QSize(15, 15))
        restart_button.clicked.connect(self.show_restart_menu)
        title_bar_layout.addWidget(restart_button)

        minimize_button = QPushButton("—")
        minimize_button.setFixedSize(25, 25)
        minimize_button.setStyleSheet("background-color: #FFD700; border-radius: 12px; font-weight: bold;")
        minimize_button.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(minimize_button)

        close_button = QPushButton("×")
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet("background-color: #FF0000; border-radius: 12px; font-weight: bold;")
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)

        self.layout.addWidget(title_bar)

    def create_main_buttons(self):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.main_button = QPushButton("Remove Temp Files")
        self.main_button.setFixedSize(350, 50)
        icon_path = os.path.join(ASSETS_DIR, "speedmeter.png")
        if os.path.exists(icon_path):
            self.main_button.setIcon(QIcon(icon_path))
            self.main_button.setIconSize(QSize(32, 32))
        self.main_button.clicked.connect(self.confirm_optimize)
        
        self.progress_overlay = QProgressBar(self.main_button)
        self.progress_overlay.setTextVisible(False)
        self.progress_overlay.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border: none;
            }
            QProgressBar::chunk {
                background-color: rgba(0, 255, 0, 128);
            }
        """)
        self.progress_overlay.hide()
        
        button_layout.addWidget(self.main_button)

        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(50, 50)
        icon_path = os.path.join(ASSETS_DIR, "settings.png")
        if os.path.exists(icon_path):
            self.settings_button.setIcon(QIcon(icon_path))
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.clicked.connect(self.toggle_settings)
        button_layout.addWidget(self.settings_button)

        button_layout.addStretch(1)
        button_layout.insertStretch(0, 1)

        self.layout.addWidget(button_container)

    def create_progress_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

    def load_settings(self):
        settings = load_settings()
        self.directories = settings.get('directories', {})
        self.skip_errors = settings.get('skip_errors', False)
        self.move_to_trash = settings.get('move_to_trash', True)
        self.clear_recycle_bin = settings.get('clear_recycle_bin', False)

    def save_settings(self):
        settings = {
            'directories': self.directories,
            'skip_errors': self.skip_errors,
            'move_to_trash': self.move_to_trash,
            'clear_recycle_bin': self.clear_recycle_bin
        }
        save_settings(settings)

    def create_settings_widget(self):
        self.settings_widget, self.toggle_all_checkbox, self.directories_layout, self.new_directory_input = create_settings_widget(
            self, self.directories, self.move_to_trash, self.skip_errors, self.clear_recycle_bin,
            self.update_skip_errors, self.update_move_to_trash, self.update_clear_recycle_bin,
            self.update_directories, self.confirm_delete_directory, self.add_directory, self.reset_settings
        )
        self.toggle_all_checkbox.stateChanged.connect(self.toggle_all_directories)
        self.layout.addWidget(self.settings_widget)

    def update_skip_errors(self, state):
        self.skip_errors = state == Qt.CheckState.Checked.value
        self.save_settings()

    def update_move_to_trash(self, state):
        self.move_to_trash = state == Qt.CheckState.Checked.value
        self.save_settings()

    def update_clear_recycle_bin(self, state):
        self.clear_recycle_bin = state == Qt.CheckState.Checked.value
        self.save_settings()

    def update_directories(self, directory, state):
        self.directories[directory] = state == Qt.CheckState.Checked.value
        self.save_settings()

    def confirm_delete_directory(self, directory):
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Are you sure you want to delete the directory '{directory}' from settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_directory(directory)

    def delete_directory(self, directory):
        if directory in self.directories:
            del self.directories[directory]
            self.save_settings()
            self.update_settings_widget()

    def add_directory(self):
        new_directory = self.new_directory_input.text()
        if new_directory and new_directory not in self.directories:
            self.directories[new_directory] = True
            add_directory_to_layout(new_directory, self.directories, self.directories_layout, self.update_directories, self.confirm_delete_directory)
            self.new_directory_input.clear()
            self.save_settings()

    def confirm_optimize(self):
        reply = QMessageBox.question(
            self, 'Confirm Optimization',
            "Are you sure you want to delete files in the selected directories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.optimize()

    def optimize(self):
        self.main_button.setEnabled(False)
        self.progress_overlay.show()
        self.progress_overlay.setValue(0)
        self.optimize_thread = OptimizeThread(self.directories, self.move_to_trash, self.skip_errors)
        self.optimize_thread.progress.connect(self.update_progress)
        self.optimize_thread.error.connect(self.show_error)
        self.optimize_thread.finished.connect(self.optimization_finished)
        self.optimize_thread.start()

    def update_progress(self, value):
        self.progress_overlay.setValue(value)

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def optimization_finished(self):
        self.main_button.setEnabled(True)
        self.progress_overlay.hide()
        if self.move_to_trash and self.clear_recycle_bin:
            try:
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                QMessageBox.information(self, "Optimization Complete", "File cleanup has been completed and the recycle bin has been emptied.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"File cleanup completed, but there was an error emptying the recycle bin: {str(e)}")
        else:
            QMessageBox.information(self, "Optimization Complete", "File cleanup has been completed.")

    def show_restart_menu(self):
        menu = QMenu(self)
        restart_app_action = QAction("Restart App", self)
        restart_app_action.triggered.connect(self.restart_app)
        menu.addAction(restart_app_action)

        restart_computer_action = QAction("Restart Computer", self)
        restart_computer_action.triggered.connect(self.restart_computer)
        menu.addAction(restart_computer_action)

        menu.exec(self.mapToGlobal(self.sender().pos()))

    def restart_app(self):
        QApplication.quit()
        subprocess.Popen([sys.executable] + sys.argv)

    def restart_computer(self):
        os.system("shutdown /r /t 0")

    def reset_settings(self):
        reply = QMessageBox.question(
            self, 'Confirm Reset',
            "Are you sure you want to reset settings to default?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            default_settings = fetch_default_settings()
            self.directories = default_settings.get('directories', {})
            self.skip_errors = default_settings.get('skip_errors', False)
            self.move_to_trash = default_settings.get('move_to_trash', True)
            self.clear_recycle_bin = default_settings.get('clear_recycle_bin', False)
            self.save_settings()
            self.update_settings_widget()
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to default.")

    def update_settings_widget(self):
        skip_errors_checkbox = self.settings_widget.findChild(QCheckBox, "skip_errors_checkbox")
        if skip_errors_checkbox:
            skip_errors_checkbox.setChecked(self.skip_errors)

        move_to_trash_checkbox = self.settings_widget.findChild(QCheckBox, "move_to_trash_checkbox")
        if move_to_trash_checkbox:
            move_to_trash_checkbox.setChecked(self.move_to_trash)

        clear_recycle_bin_checkbox = self.settings_widget.findChild(QCheckBox, "clear_recycle_bin_checkbox")
        if clear_recycle_bin_checkbox:
            clear_recycle_bin_checkbox.setChecked(self.clear_recycle_bin)

        self.toggle_all_checkbox.setChecked(all(self.directories.values()))

        for i in reversed(range(self.directories_layout.count())):
            widget = self.directories_layout.itemAt(i).widget()
            if widget is not None:
                self.directories_layout.removeWidget(widget)
                widget.deleteLater()

        for directory, enabled in self.directories.items():
            add_directory_to_layout(directory, self.directories, self.directories_layout, self.update_directories, self.confirm_delete_directory)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.progress_overlay.setGeometry(self.main_button.rect())

    def toggle_settings(self):
        if self.settings_widget.isVisible():
            self.settings_widget.hide()
        else:
            self.settings_widget.show()

    def mousePressEvent(self, event: QMouseEvent):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def toggle_all_directories(self, state):
        checked = state == Qt.CheckState.Checked.value
        for directory in self.directories:
            self.directories[directory] = checked
        self.update_settings_widget()
        self.save_settings()

if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:
            check_for_updates()
            
            # Add this line to append the ROOT_DIR to sys.path
            sys.path.append(ROOT_DIR)
            
            # Move the imports here and wrap them in a try-except block
            try:
                from scripts.TempFilesDeleter.settings_manager import load_settings, save_settings, fetch_default_settings
                from scripts.TempFilesDeleter.optimize_thread import OptimizeThread
                from scripts.TempFilesDeleter.ui_components import create_settings_widget, add_directory_to_layout
            except ImportError as e:
                print(f"Error importing modules: {e}")
                print("Some modules might be missing. Please ensure all required files are present.")
                sys.exit(1)
            
            app = QApplication(sys.argv)
            window = InsomniaApp()
            window.show()
            sys.exit(app.exec())
    except Exception as e:
        log_error(f"Error in main execution: {str(e)}")
        QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}\nPlease check the log file in {ERROR_LOGS_DIR} for details.")
        sys.exit(1)
