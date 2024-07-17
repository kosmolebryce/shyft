from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QTextEdit, QPushButton, QSplitter)
from PyQt6.QtCore import Qt
from pathlib import Path

class ViewLogsWindow(QMainWindow):
    def __init__(self, log_dir, parent=None):
        super().__init__(parent)
        self.log_dir = Path(log_dir)
        self.setWindowTitle("View Logs")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.display_log_content)
        splitter.addWidget(self.file_list)

        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        splitter.addWidget(self.content_display)

        layout.addWidget(splitter)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.populate_file_list()

    def populate_file_list(self):
        log_files = sorted(self.log_dir.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)
        for file in log_files:
            self.file_list.addItem(file.name)

    def display_log_content(self, item):
        file_path = self.log_dir / item.text()
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            self.content_display.setPlainText(content)
        except Exception as e:
            self.content_display.setPlainText(f"Error reading file: {str(e)}")
