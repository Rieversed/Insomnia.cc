from PyQt6.QtCore import QThread, pyqtSignal
import os
import shutil
import send2trash

class OptimizeThread(QThread):
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, directories, move_to_trash, skip_errors):
        super().__init__()
        self.directories = directories
        self.move_to_trash = move_to_trash
        self.skip_errors = skip_errors

    def run(self):
        total = len(self.directories)
        for i, (directory, enabled) in enumerate(self.directories.items()):
            if not enabled:
                continue
            expanded_path = os.path.expandvars(directory)
            if os.path.exists(expanded_path):
                try:
                    for item in os.listdir(expanded_path):
                        item_path = os.path.join(expanded_path, item)
                        try:
                            if self.move_to_trash:
                                send2trash.send2trash(item_path)
                            else:
                                if os.path.isfile(item_path):
                                    os.unlink(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                        except Exception as e:
                            if not self.skip_errors:
                                self.error.emit(f"Error deleting {item_path}: {str(e)}")
                            else:
                                try:
                                    if self.move_to_trash:
                                        send2trash.send2trash(item_path)
                                    else:
                                        if os.path.isfile(item_path):
                                            os.unlink(item_path)
                                        elif os.path.isdir(item_path):
                                            shutil.rmtree(item_path)
                                except:
                                    pass
                except Exception as e:
                    if not self.skip_errors:
                        self.error.emit(f"Error accessing {expanded_path}: {str(e)}")
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit()
