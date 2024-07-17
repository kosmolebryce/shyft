from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase
from datetime import timedelta
import os

class TimerWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, time_color="#A78C7B", bg_color="#FFBE98"):
        super().__init__()
        self.setWindowTitle("Timer")
        self.setGeometry(100, 100, 200, 150)
        self.setStyleSheet(f"background-color: {bg_color};")

        self.elapsed_time = timedelta(0)
        self.running = False
        self.time_color = time_color
        self.bg_color = bg_color

        # Load the custom font
        self.load_custom_font()

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(100)  # Update every 100 ms

    def load_custom_font(self):
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'MonaspaceKryptonVarVF[wght,wdth,slnt].ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.custom_font = QFont(font_families[0])
        else:
            self.custom_font = QFont("Courier")  # Fallback to a default monospace font

    def setup_ui(self):
        layout = QVBoxLayout()

        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(self.custom_font)
        self.time_label.setStyleSheet(f"color: {self.time_color}; font-size: 32px; font-weight: bold;")
        self.time_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.time_label)

        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        button_layout.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def start(self):
        self.running = True

    def closeEvent(self, event):
        self.stop()
        self.closed.emit()
        super().closeEvent(event)

    def stop(self):
        if self.running:
            self.running = False
            self.timer.stop()

    def reset(self):
        self.stop()
        self.elapsed_time = timedelta(0)
        self.update_label()

    def update_timer(self):
        if self.running:
            self.elapsed_time += timedelta(milliseconds=100)
            self.update_label()

    def update_label(self):
        hours, remainder = divmod(self.elapsed_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
