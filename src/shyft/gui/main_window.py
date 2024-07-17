from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView, QMessageBox, QHeaderView
from PyQt6.QtCore import Qt
from .dialogs.manual_entry_dialog import ManualEntryDialog
from .dialogs.edit_shift_dialog import EditShiftDialog
from .dialogs.autologger_dialog import AutologgerDialog
from .dialogs.view_logs_window import ViewLogsWindow
from .timer_window import TimerWindow
from ..models.shift_model import ShiftModel
from datetime import datetime
import json
from appdirs import user_data_dir
from pathlib import Path
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shyft")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        
        self.tree_view = QTreeView()
        self.layout.addWidget(self.tree_view)
        
        self.setup_model()
        self.setup_tree_view()
        self.setup_buttons()
        self.adjust_window_size()

        self.timer_window = None
        self.autologger_dialog = None
        self.view_logs_window = None
        
        app_name = "Shyft"
        app_author = "YourCompanyName"  # Replace with your company name
        self.data_dir = Path(user_data_dir(app_name, app_author))
        self.log_dir = self.data_dir / 'logs'

    def setup_model(self):
        self.shift_model = ShiftModel()
    
    def setup_tree_view(self):
        self.tree_view.setModel(self.shift_model)
        
        # Set equal width for all columns
        header = self.tree_view.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def setup_buttons(self):
        button_layout = QHBoxLayout()
        
        buttons = [
            ("Manual Entry", self.manual_entry),
            ("Edit Shift", self.edit_shift),
            ("Delete Shift", self.delete_shift),
            ("Refresh View", self.refresh_view),
            ("View Logs", self.view_logs),
            ("Autologger", self.autologger),
            ("Totals", self.calculate_totals)
        ]
        
        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            button_layout.addWidget(button)
        
        self.layout.addLayout(button_layout)
    
    def adjust_window_size(self):
        # Set a fixed width for each column
        column_width = 100
        num_columns = self.shift_model.columnCount()
        
        # Calculate total width (columns + some extra for margins and scroll bar)
        total_width = (column_width * num_columns) + 50
        
        # Set the window size
        self.setGeometry(100, 100, max(total_width, 800), 600)
    
    def manual_entry(self):
        dialog = ManualEntryDialog(self)
        dialog.submitted.connect(self.handle_manual_entry)
        dialog.exec()
    
    def handle_manual_entry(self, data):
        self.shift_model.add_shift(data)
        QMessageBox.information(self, "Success", "Shift added successfully!")
    
    def edit_shift(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "No Selection", "Please select a shift to edit.")
            return
        
        row = selected_indexes[0].row()
        shift_data = self.shift_model.shifts[row]
        
        dialog = EditShiftDialog(shift_data, self)
        dialog.submitted.connect(lambda data: self.handle_edit_shift(row, data))
        dialog.exec()

    def handle_edit_shift(self, row, data):
        self.shift_model.edit_shift(row, data)
        QMessageBox.information(self, "Success", "Shift updated successfully!")
    
    def delete_shift(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "No Selection", "Please select a shift to delete.")
            return
        
        row = selected_indexes[0].row()
        shift_id = self.shift_model.shifts[row][0]  # Assuming the ID is the first column
        
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this shift?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            deleted_shift = self.shift_model.delete_shift(row)
            if deleted_shift:
                # Delete associated .md file if it exists
                md_file_path = self.log_dir / f"{shift_id}.md"
                if md_file_path.exists():
                    os.remove(md_file_path)
                    print(f"Deleted associated file: {md_file_path}")
                
                QMessageBox.information(self, "Success", "Shift deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete shift.")
    
    def refresh_view(self):
        self.tree_view.reset()
        QMessageBox.information(self, "Refreshed", "View has been refreshed.")
   
    def view_logs(self):
        if not self.log_dir.exists():
            QMessageBox.information(self, "No Logs", "No log files found.")
            return

        if self.view_logs_window is None:
            self.view_logs_window = ViewLogsWindow(self.log_dir)
            self.view_logs_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.view_logs_window.destroyed.connect(self.on_view_logs_closed)
        
        self.view_logs_window.show()
        self.view_logs_window.activateWindow()

    def on_view_logs_closed(self):
        self.view_logs_window = None
    
    def show_timer(self):
        if self.timer_window is None:
            self.timer_window = TimerWindow()
            self.timer_window.closed.connect(self.on_timer_closed)
        self.timer_window.show()

    def on_timer_closed(self):
        self.timer_window = None

    def start_autologger(self):
        self.autologger_dialog = AutologgerDialog()
        self.autologger_dialog.collect_shared_data.connect(self.start_autologger_timer)
        self.autologger_dialog.submitted.connect(self.handle_autologger)
        self.autologger_dialog.rejected.connect(self.cancel_autologger)
        self.autologger_dialog.show()

    def start_autologger_timer(self, shared_data):
        self.timer_window = TimerWindow()
        self.timer_window.closed.connect(self.cancel_autologger)
        self.timer_window.show()
        self.timer_window.start()

    def autologger(self):
        if self.autologger_dialog is None:
            self.autologger_dialog = AutologgerDialog(self)
            self.autologger_dialog.submitted.connect(self.handle_autologger)
            self.autologger_dialog.finished.connect(self.on_autologger_closed)
        
        if self.timer_window is None:
            self.timer_window = TimerWindow()
            self.timer_window.closed.connect(self.on_timer_closed)
        
        self.timer_window.show()
        self.timer_window.start()
        self.autologger_dialog.show()

    def handle_autologger(self, data):
        try:
            if self.timer_window:
                self.timer_window.stop()
                duration = self.timer_window.elapsed_time.total_seconds() / 3600  # in hours

                hourly_rate = float(data['Hourly Rate'])
                gross_pay = duration * hourly_rate

                shift_data = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Model ID": data['Model ID'],
                    "Project ID": data['Project ID'],
                    "In (hh:mm)": (datetime.now() - self.timer_window.elapsed_time).strftime("%H:%M"),
                    "Out (hh:mm)": datetime.now().strftime("%H:%M"),
                    "Duration (hrs)": f"{duration:.2f}",
                    "Hourly rate": f"{hourly_rate:.2f}",
                    "Gross pay": f"{gross_pay:.2f}",
                    "Tasks completed": str(len(data['Tasks'])),
                    "Tasks": json.dumps(data['Tasks'])
                }

                shift_id = self.shift_model.add_shift(shift_data)
                QMessageBox.information(self, "Success", f"Autologger shift {shift_id} added successfully. {len(data['Tasks'])} tasks completed.")
            else:
                raise ValueError("Timer window is not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while handling autologger data: {str(e)}")
            print(f"Error in handle_autologger: {str(e)}")
        finally:
            self.close_timer()
            self.close_autologger()

    def cancel_autologger(self):
        if self.timer_window:
            self.timer_window.close()
            self.timer_window = None
        if self.autologger_dialog:
            self.autologger_dialog.reject()
            self.autologger_dialog = None
        QMessageBox.information(self, "Autologger Canceled", "The autologger process has been canceled.")


    def on_autologger_closed(self):
        self.close_timer()
        self.autologger_dialog = None

    def on_timer_closed(self):
        self.close_autologger()
        self.timer_window = None

    def close_timer(self):
        if self.timer_window:
            self.timer_window.close()
            self.timer_window = None

    def close_autologger(self):
        if self.autologger_dialog:
            self.autologger_dialog.close()
            self.autologger_dialog = None

    def update_autologger_duration(self):
        if self.autologger_start_time:
            duration = datetime.now() - self.autologger_start_time
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.setWindowTitle(f"Shyft - Autologger Running: {hours:02d}:{minutes:02d}:{seconds:02d}")   

    def calculate_totals(self):
        total_hours = self.shift_model.get_total_hours()
        total_pay = self.shift_model.get_total_pay()
        message = f"Total Hours: {total_hours:.2f}\nTotal Pay: ${total_pay:.2f}"
        QMessageBox.information(self, "Totals", message)
