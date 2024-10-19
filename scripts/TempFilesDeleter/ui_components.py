from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, 
                             QLineEdit, QLabel, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import os

def create_settings_widget(parent, directories, move_to_trash, skip_errors, clear_recycle_bin, 
                           update_skip_errors, update_move_to_trash, update_clear_recycle_bin, 
                           update_directories, confirm_delete_directory, add_directory, reset_settings):
    settings_widget = QScrollArea()
    settings_widget.setWidgetResizable(True)
    settings_widget.setFrameShape(QFrame.Shape.NoFrame)
    
    settings_content = QWidget()
    settings_layout = QVBoxLayout(settings_content)

    skip_errors_checkbox = QCheckBox("Skip errors")
    skip_errors_checkbox.setObjectName("skip_errors_checkbox")
    skip_errors_checkbox.setChecked(skip_errors)
    skip_errors_checkbox.stateChanged.connect(update_skip_errors)
    settings_layout.addWidget(skip_errors_checkbox)

    move_to_trash_checkbox = QCheckBox("Move files to trash")
    move_to_trash_checkbox.setObjectName("move_to_trash_checkbox")
    move_to_trash_checkbox.setChecked(move_to_trash)
    move_to_trash_checkbox.stateChanged.connect(update_move_to_trash)
    settings_layout.addWidget(move_to_trash_checkbox)

    clear_recycle_bin_checkbox = QCheckBox("Clear recycle bin after")
    clear_recycle_bin_checkbox.setObjectName("clear_recycle_bin_checkbox")
    clear_recycle_bin_checkbox.setChecked(clear_recycle_bin)
    clear_recycle_bin_checkbox.stateChanged.connect(update_clear_recycle_bin)
    settings_layout.addWidget(clear_recycle_bin_checkbox)

    directories_header = QWidget()
    directories_header_layout = QHBoxLayout(directories_header)
    toggle_all_checkbox = QCheckBox("Toggle all Directories:")
    toggle_all_checkbox.setChecked(all(directories.values()))
    toggle_all_checkbox.stateChanged.connect(lambda state: toggle_all_directories(state, directories, directories_layout, update_directories))
    directories_header_layout.addWidget(toggle_all_checkbox)
    settings_layout.addWidget(directories_header)

    directories_layout = QVBoxLayout()
    for directory in directories:
        add_directory_to_layout(directory, directories, directories_layout, update_directories, confirm_delete_directory)
    settings_layout.addLayout(directories_layout)

    add_directory_layout = QHBoxLayout()
    new_directory_input = QLineEdit()
    add_button = QPushButton("Add")
    add_button.clicked.connect(lambda: add_directory(new_directory_input.text()))
    add_directory_layout.addWidget(new_directory_input)
    add_directory_layout.addWidget(add_button)
    settings_layout.addLayout(add_directory_layout)

    reset_button = QPushButton("Reset Settings")
    reset_button.clicked.connect(reset_settings)
    settings_layout.addWidget(reset_button)

    settings_layout.addStretch(1)
    settings_widget.setWidget(settings_content)
    
    return settings_widget, toggle_all_checkbox, directories_layout, new_directory_input

def add_directory_to_layout(directory, directories, directories_layout, update_directories, confirm_delete_directory):
    directory_widget = QWidget()
    directory_layout = QHBoxLayout(directory_widget)
    directory_layout.setContentsMargins(0, 0, 0, 0)

    delete_button = QPushButton()
    delete_button.setFixedSize(20, 20)
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "trash.png")
    if os.path.exists(icon_path):
        delete_button.setIcon(QIcon(icon_path))
    delete_button.setIconSize(QSize(16, 16))
    delete_button.clicked.connect(lambda: confirm_delete_directory(directory))
    delete_button.setStyleSheet("""
        QPushButton {
            background-color: #808080;
            border: none;
            border-radius: 10px;
        }
        QPushButton:hover {
            background-color: #FF0000;
        }
    """)
    directory_layout.addWidget(delete_button)

    checkbox = QCheckBox(directory)
    checkbox.setChecked(directories[directory])
    checkbox.stateChanged.connect(lambda state, dir=directory: update_directories(dir, state))
    directory_layout.addWidget(checkbox)

    directories_layout.addWidget(directory_widget)

def toggle_all_directories(state, directories, directories_layout, update_directories):
    checked = state == Qt.CheckState.Checked.value
    for i in range(directories_layout.count()):
        widget = directories_layout.itemAt(i).widget()
        if isinstance(widget, QWidget):
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(checked)
                directory = checkbox.text()
                directories[directory] = checked
                update_directories(directory, checked)
