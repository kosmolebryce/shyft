from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QDialogButtonBox, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QValidator

class UppercaseValidator(QValidator):
    def validate(self, input, pos):
        return QValidator.State.Acceptable, input.upper(), pos

class EditShiftDialog(QDialog):
    submitted = pyqtSignal(dict)

    def __init__(self, shift_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Shift")
        self.shift_data = shift_data
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.fields = {
            "Date": QLineEdit(self.shift_data[1]),
            "Model ID": QLineEdit(self.shift_data[2]),
            "Project ID": QLineEdit(self.shift_data[3]),
            "In (hh:mm)": QLineEdit(self.shift_data[4]),
            "Out (hh:mm)": QLineEdit(self.shift_data[5]),
            "Hourly rate": QLineEdit(self.shift_data[7]),
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
