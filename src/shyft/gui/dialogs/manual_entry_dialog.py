from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QDialogButtonBox, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QValidator

class UppercaseValidator(QValidator):
    def validate(self, input, pos):
        return QValidator.State.Acceptable, input.upper(), pos

class ManualEntryDialog(QDialog):
    submitted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Entry")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.fields = {
            "Date": QLineEdit(),
            "Model ID": QLineEdit(),
            "Project ID": QLineEdit(),
            "In (hh:mm)": QLineEdit(),
            "Out (hh:mm)": QLineEdit(),
            "Hourly rate": QLineEdit(),
        }

        # Set uppercase validator for Model ID and Project ID
        uppercase_validator = UppercaseValidator()
        self.fields["Model ID"].setValidator(uppercase_validator)
        self.fields["Project ID"].setValidator(uppercase_validator)

        for label, widget in self.fields.items():
            form_layout.addRow(label, widget)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        button_layout.insertStretch(0)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def accept(self):
        data = {field: widget.text() for field, widget in self.fields.items()}
        self.submitted.emit(data)
        super().accept()
