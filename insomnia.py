import sys
import os
import ctypes
import logging
from datetime import datetime
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QCheckBox, QLineEdit, QScrollArea,
                             QProgressBar, QMessageBox, QFrame, QMenu, QLabel, QStackedWidget)
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
        self.setFixedSize(800, 500)  # Increased from 700x400 to 800x500
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                border-radius: 10px;
            }
            QWidget#centralWidget {
                background-color: #1e1e1e;
                border-radius: 10px;
            }
        """)

        # Initialize directories
        self.directories = {}

        self.load_settings()

        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.create_title_bar()
        self.create_main_area()

        self.oldPos = self.pos()

        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.current_tab = "Home"  # Add this line to track the current tab

    def create_title_bar(self):
        self.title_bar = QWidget()
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 10, 10, 5)
        title_bar_layout.setSpacing(10)

        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            app_icon_label = QLabel()
            app_icon_label.setPixmap(QIcon(icon_path).pixmap(32, 32))
            title_bar_layout.addWidget(app_icon_label)

        self.title_label = QLabel("Insomnia")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 24px;")
        title_bar_layout.addWidget(self.title_label)

        title_bar_layout.addStretch()

        for button_data in [
            ("restart", "#00FF00", self.show_restart_menu),
            ("—", "#FFD700", self.showMinimized),
            ("×", "#FF0000", self.close)
        ]:
            button = QPushButton(button_data[0])
            button.setFixedSize(25, 25)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_data[1]};
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {button_data[1]}CC;
                }}
            """)
            if button_data[0] == "restart":
                restart_icon_path = os.path.join(ASSETS_DIR, "restart.png")
                if os.path.exists(restart_icon_path):
                    button.setIcon(QIcon(restart_icon_path))
                    button.setIconSize(QSize(16, 16))
                button.setText("")  # Remove text to show only icon
            button.clicked.connect(button_data[2])
            title_bar_layout.addWidget(button)

        self.layout.addWidget(self.title_bar)

    def create_main_area(self):
        main_area = QWidget()
        main_area_layout = QHBoxLayout(main_area)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        main_area_layout.setSpacing(0)

        self.create_sidebar()
        self.create_content_area()

        main_area_layout.addWidget(self.sidebar)
        main_area_layout.addWidget(self.content_area)

        self.layout.addWidget(main_area)

    def create_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 5, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_content = QWidget()
        sidebar_content.setStyleSheet("""
            background-color: #2e2e2e;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        """)
        sidebar_content_layout = QVBoxLayout(sidebar_content)
        sidebar_content_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_content_layout.setSpacing(0)

        buttons = ["Home", "Tweaks", "Temp Files", "More Apps", "Settings"]
        for button_text in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ffffff;
                    border: none;
                    text-align: left;
                    padding: 10px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #3e3e3e;
                    border-radius: 10px;
                }
            """)
            button.clicked.connect(lambda checked, text=button_text: self.switch_tab(text))
            sidebar_content_layout.addWidget(button)

        sidebar_content_layout.addStretch()
        sidebar_layout.addWidget(sidebar_content)

    def create_content_area(self):
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.stacked_widget = QStackedWidget()
        self.create_home_tab()
        self.create_tweaks_tab()
        self.create_temp_files_tab()
        self.create_more_apps_tab()
        self.create_settings_tab()

        content_layout.addWidget(self.stacked_widget)

    def create_home_tab(self):
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.addWidget(QLabel("Welcome to Insomnia"))
        # Add more widgets and content for the home tab
        self.stacked_widget.addWidget(home_widget)

    def create_tweaks_tab(self):
        tweaks_widget = QWidget()
        tweaks_layout = QVBoxLayout(tweaks_widget)
        tweaks_layout.addWidget(QLabel("Tweaks"))
        # Add more widgets and content for the tweaks tab
        self.stacked_widget.addWidget(tweaks_widget)

    def create_temp_files_tab(self):
        temp_files_widget = QWidget()
        self.temp_files_layout = QVBoxLayout(temp_files_widget)
        self.temp_files_layout.setContentsMargins(10, 10, 10, 10)
        self.temp_files_layout.setSpacing(10)

        self.button_container = QWidget()
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.main_button = QPushButton("Remove Temp Files")
        self.main_button.setFixedSize(350, 50)
        icon_path = os.path.join(ASSETS_DIR, "speedmeter.png")
        if os.path.exists(icon_path):
            self.main_button.setIcon(QIcon(icon_path))
            self.main_button.setIconSize(QSize(32, 32))
        self.main_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1e1e1e;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.main_button.clicked.connect(self.confirm_optimize)
        
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(50, 50)
        settings_icon_path = os.path.join(ASSETS_DIR, "settings.png")
        if os.path.exists(settings_icon_path):
            self.settings_button.setIcon(QIcon(settings_icon_path))
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.settings_button.clicked.connect(self.toggle_settings)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.main_button)
        button_layout.addWidget(self.settings_button)
        button_layout.addStretch(1)
        
        self.temp_files_layout.addWidget(self.button_container)
        
        self.settings_scroll_area = QScrollArea()
        self.settings_scroll_area.setWidgetResizable(True)
        self.settings_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #2e2e2e;
                width: 5px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #5e5e5e;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        
        self.settings_widget, self.toggle_all_checkbox, self.directories_layout, self.new_directory_input = create_settings_widget(
            self, self.directories, self.move_to_trash, self.skip_errors, self.clear_recycle_bin,
            self.update_skip_errors, self.update_move_to_trash, self.update_clear_recycle_bin,
            self.update_directories, self.confirm_delete_directory, self.add_directory, self.reset_temp_file_settings
        )
        settings_layout.addWidget(self.settings_widget)
        self.toggle_all_checkbox.stateChanged.connect(self.toggle_all_directories)
        
        # Add custom directory input
        custom_dir_layout = QHBoxLayout()
        self.custom_dir_input = QLineEdit()
        self.custom_dir_input.setPlaceholderText("Enter custom directory")
        add_custom_dir_button = QPushButton("Add")
        add_custom_dir_button.clicked.connect(self.add_custom_directory)
        custom_dir_layout.addWidget(self.custom_dir_input)
        custom_dir_layout.addWidget(add_custom_dir_button)
        settings_layout.addLayout(custom_dir_layout)
        
        # Add reset settings button
        reset_button = QPushButton("Reset Temp File Settings")
        reset_button.clicked.connect(self.reset_temp_file_settings)
        settings_layout.addWidget(reset_button)
        
        self.settings_scroll_area.setWidget(settings_content)
        self.settings_scroll_area.hide()
        self.temp_files_layout.addWidget(self.settings_scroll_area)
        
        self.stacked_widget.addWidget(temp_files_widget)

    def add_custom_directory(self):
        new_dir = self.custom_dir_input.text()
        if new_dir and new_dir not in self.directories:
            self.directories[new_dir] = True
            self.update_settings_widget()
            self.save_settings()
            self.custom_dir_input.clear()

    def create_more_apps_tab(self):
        more_apps_widget = QWidget()
        more_apps_layout = QVBoxLayout(more_apps_widget)
        more_apps_layout.addWidget(QLabel("More Apps"))
        # Add more widgets and content for the more apps tab
        self.stacked_widget.addWidget(more_apps_widget)

    def create_settings_tab(self):
        self.settings_widget, self.toggle_all_checkbox, self.directories_layout, self.new_directory_input = create_settings_widget(
            self, self.directories, self.move_to_trash, self.skip_errors, self.clear_recycle_bin,
            self.update_skip_errors, self.update_move_to_trash, self.update_clear_recycle_bin,
            self.update_directories, self.confirm_delete_directory, self.add_directory, self.reset_settings
        )
        self.toggle_all_checkbox.stateChanged.connect(self.toggle_all_directories)
        self.stacked_widget.addWidget(self.settings_widget)

    def switch_tab(self, tab_name):
        index_map = {
            "Home": 0,
            "Tweaks": 1,
            "Temp Files": 2,
            "More Apps": 3,
            "Settings": 4
        }
        self.stacked_widget.setCurrentIndex(index_map.get(tab_name, 0))
        self.current_tab = tab_name
        self.update_title()

    def update_title(self):
        self.title_label.setText(f"Insomnia / {self.current_tab}")

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
        self.optimize_thread = OptimizeThread(self.directories, self.move_to_trash, self.skip_errors)
        self.optimize_thread.progress.connect(self.update_progress)
        self.optimize_thread.error.connect(self.show_error)
        self.optimize_thread.finished.connect(self.optimization_finished)
        self.optimize_thread.start()

    def update_progress(self, value):
        bright_green = "#00FF00"  # Brighter green color
        self.main_button.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {bright_green}, stop:{value/100} {bright_green}, 
                    stop:{value/100 + 0.001} #ffffff, stop:1 #ffffff);
                color: #1e1e1e;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00DD00, stop:{value/100} #00DD00, 
                    stop:{value/100 + 0.001} #e0e0e0, stop:1 #e0e0e0);
            }}
        """)
        
        # Create a custom formatted text with the icon
        icon = self.main_button.icon()
        if not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            self.main_button.setIconSize(QSize(32, 32))
            self.main_button.setIcon(QIcon(pixmap))
        
        self.main_button.setText("Remove Temp Files")
        self.main_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def optimization_finished(self):
        self.main_button.setEnabled(True)
        self.main_button.setText("Remove Temp Files")
        self.main_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1e1e1e;
                border: none;
                padding: 10px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
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
        self.main_button.setGeometry(self.main_button.rect())

    def toggle_settings(self):
        if self.settings_scroll_area.isVisible():
            self.settings_scroll_area.hide()
        else:
            self.settings_scroll_area.show()
        
        self.settings_scroll_area.setFixedHeight(self.height() - self.button_container.height() - 40)

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

    def reset_temp_file_settings(self):
        reply = QMessageBox.question(
            self, 'Confirm Reset',
            "Are you sure you want to reset Temp File settings to default?",
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
            QMessageBox.information(self, "Settings Reset", "Temp File settings have been reset to default.")

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
