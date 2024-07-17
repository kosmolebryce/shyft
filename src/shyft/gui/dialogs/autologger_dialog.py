import os
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLineEdit, QPushButton, QComboBox, QTextEdit, 
                             QLabel, QDialogButtonBox, QMessageBox, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QValidator
from appdirs import user_data_dir

class UppercaseValidator(QValidator):
    def validate(self, input, pos):
        return QValidator.State.Acceptable, input.upper(), pos


class AutologgerDialog(QDialog):
    submitted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autologger")
        self.setMinimumWidth(500)
        self.collected_data = []
        self.setup_ui()
        self.setup_log_directory()

    def setup_log_directory(self):
        app_name = "Shyft"
        app_author = "ENCLAIM"  
        data_dir = user_data_dir(app_name, app_author)
        self.log_dir = Path(data_dir) / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Shared data form
        shared_grid = QGridLayout()
        shared_grid.setColumnStretch(1, 1)  # Make the second column (fields) stretch
        self.model_id = QLineEdit()
        self.model_id.setValidator(UppercaseValidator())
        self.project_id = QLineEdit()
        self.project_id.setValidator(UppercaseValidator())
        self.hourly_rate = QLineEdit()

        shared_grid.addWidget(QLabel("Model ID:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        shared_grid.addWidget(self.model_id, 0, 1)
        shared_grid.addWidget(QLabel("Project ID:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        shared_grid.addWidget(self.project_id, 1, 1)
        shared_grid.addWidget(QLabel("Hourly Rate of Pay:"), 2, 0, Qt.AlignmentFlag.AlignLeft)
        shared_grid.addWidget(self.hourly_rate, 2, 1)
        main_layout.addLayout(shared_grid)

        # Task data form
        task_grid = QGridLayout()
        task_grid.setColumnStretch(1, 1)  # Make the second column (fields) stretch
        self.platform_id = QLineEdit()
        self.permalink = QLineEdit()
        self.response1_id = QLineEdit()
        self.response2_id = QLineEdit()

        task_grid.addWidget(QLabel("Platform ID:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        task_grid.addWidget(self.platform_id, 0, 1)
        task_grid.addWidget(QLabel("Permalink:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        task_grid.addWidget(self.permalink, 1, 1)
        task_grid.addWidget(QLabel("Response #1 ID:"), 2, 0, Qt.AlignmentFlag.AlignLeft)
        task_grid.addWidget(self.response1_id, 2, 1)
        task_grid.addWidget(QLabel("Response #2 ID:"), 3, 0, Qt.AlignmentFlag.AlignLeft)
        task_grid.addWidget(self.response2_id, 3, 1)
        main_layout.addLayout(task_grid)

        # Rank selection
        rank_layout = QHBoxLayout()
        rank_layout.addWidget(QLabel("Rank:"), 0, Qt.AlignmentFlag.AlignLeft)
        self.rank_combo = QComboBox()
        self.rank_combo.addItems([
            "(1) is much better than (2)",
            "(1) is slightly better than (2)",
            "The responses are of equal quality",
            "(2) is slightly better than (1)",
            "(2) is much better than (1)",
            "Task rejected for containing sensitive content"
        ])
        self.rank_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        rank_layout.addWidget(self.rank_combo, 1)
        main_layout.addLayout(rank_layout)

        # Justification
        main_layout.addWidget(QLabel("Justification:"), 0, Qt.AlignmentFlag.AlignLeft)
        self.justification = QTextEdit()
        self.justification.setMinimumHeight(100)
        main_layout.addWidget(self.justification)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        self.finish_button = QPushButton("Finish Logging")
        self.finish_button.clicked.connect(self.finish_logging)
        button_layout.addWidget(self.add_task_button)
        button_layout.addWidget(self.finish_button)
        main_layout.addLayout(button_layout)

        # Set size policies for expanding widgets
        for widget in [self.model_id, self.project_id, self.hourly_rate, 
                       self.platform_id, self.permalink, self.response1_id, 
                       self.response2_id, self.rank_combo, self.justification]:
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def add_task(self):
        task_data = {
            "Platform ID": self.platform_id.text(),
            "Permalink": self.permalink.text(),
            "Response #1 ID": self.response1_id.text(),
            "Response #2 ID": self.response2_id.text(),
            "Rank": self.rank_combo.currentText(),
            "Justification": self.justification.toPlainText()
        }
        if not all(task_data.values()):
            QMessageBox.warning(self, "Incomplete Data", "Please fill in all fields.")
            return
        self.collected_data.append(task_data)
        self.clear_task_fields()
        QMessageBox.information(self, "Task Added", "Task has been added successfully.")

    def clear_task_fields(self):
        self.platform_id.clear()
        self.permalink.clear()
        self.response1_id.clear()
        self.response2_id.clear()
        self.rank_combo.setCurrentIndex(0)
        self.justification.clear()

    def finish_logging(self):
        if not self.collected_data:
            QMessageBox.warning(self, "No Tasks", "Please add at least one task before finishing.")
            return
        try:
            data = {
                "Model ID": self.model_id.text(),
                "Project ID": self.project_id.text(),
                "Hourly Rate": self.hourly_rate.text(),
                "Tasks": self.collected_data
            }
            self.save_tasks_to_markdown(data)
            self.submitted.emit(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while finishing logging: {str(e)}")
            print(f"Error in finish_logging: {str(e)}")

    def save_tasks_to_markdown(self, data):
        for i, task in enumerate(data['Tasks'], start=1):
            task_id = f"{len(os.listdir(self.log_dir)) + 1:04d}"
            file_path = self.log_dir / f"{task_id}.md"
            
            content = f"""# `{task_id}.md`

----

{i}. `{task['Platform ID']}`

[Permalink]
{task['Permalink']}

[Response IDs]
1. `{task['Response #1 ID']}`
2. `{task['Response #2 ID']}`

[Rank]
{task['Rank']}

[Justification]
{task['Justification']}

"""
            with open(file_path, 'w') as f:
                f.write(content)

        print(f"Task data saved to {self.log_dir}")
