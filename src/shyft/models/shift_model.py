from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from datetime import datetime, timedelta
import json
from pathlib import Path
from appdirs import user_data_dir

class ShiftModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.shifts = []
        self.headers = ["ID", "Date", "Model ID", "Project ID", "In (hh:mm)", 
                        "Out (hh:mm)", "Duration (hrs)", "Hourly rate", "Gross pay", "Tasks completed"]
        self.setup_data_directory()
        self.load_data()

    def setup_data_directory(self):
        app_name = "Shyft"
        app_author = "ENCLAIM" 
        data_dir = user_data_dir(app_name, app_author)
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        self.data_file = Path(data_dir) / 'shyft_data.json'

    def rowCount(self, parent=QModelIndex()):
        return len(self.shifts)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.shifts[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

   
    def add_shift(self, shift_data):
        shift_id = f"{len(self.shifts) + 1:04d}"
        shift = [
            shift_id,
            shift_data["Date"],
            shift_data["Model ID"].upper(),
            shift_data["Project ID"].upper(),
            shift_data["In (hh:mm)"],
            shift_data["Out (hh:mm)"],
            shift_data["Duration (hrs)"],
            shift_data["Hourly rate"],
            shift_data["Gross pay"],
            shift_data.get("Tasks completed", "N/A")
        ]

        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.shifts.append(shift)
        self.endInsertRows()
        self.save_data()
        return shift_id

    def get_total_hours(self):
        return sum(float(shift[6]) for shift in self.shifts)

    def get_total_pay(self):
        return sum(float(shift[8]) for shift in self.shifts)

    def edit_shift(self, row, shift_data):
        # Calculate duration
        time_in = datetime.strptime(shift_data["In (hh:mm)"], "%H:%M")
        time_out = datetime.strptime(shift_data["Out (hh:mm)"], "%H:%M")
        if time_out < time_in:
            time_out += timedelta(days=1)
        duration = (time_out - time_in).total_seconds() / 3600

        # Calculate gross pay
        hourly_rate = float(shift_data["Hourly rate"])
        gross_pay = duration * hourly_rate

        # Update shift entry
        self.shifts[row] = [
            self.shifts[row][0],  # Keep the original ID
            shift_data["Date"],
            shift_data["Model ID"].upper(),
            shift_data["Project ID"].upper(),
            shift_data["In (hh:mm)"],
            shift_data["Out (hh:mm)"],
            f"{duration:.2f}",
            f"{hourly_rate:.2f}",
            f"{gross_pay:.2f}"
        ]

        # Emit signal that data has changed
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
        self.save_data()
   
    def load_data(self):
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.shifts = []
                for shift in data:
                    if isinstance(shift, dict):
                        # If the shift is a dictionary, extract values based on headers
                        shift_data = [shift.get(header, '') for header in self.headers]
                        if 'Tasks' in shift:
                            shift_data[-1] = json.dumps(shift['Tasks'])
                    elif isinstance(shift, list):
                        # If the shift is already a list, use it directly
                        shift_data = shift
                    else:
                        # Skip invalid data
                        continue
                    self.shifts.append(shift_data)
        else:
            self.shifts = []

    def delete_shift(self, row):
        if 0 <= row < len(self.shifts):
            self.beginRemoveRows(QModelIndex(), row, row)
            deleted_shift = self.shifts.pop(row)
            self.endRemoveRows()
            self.save_data()
            return deleted_shift
        return None

    def save_data(self):
        data_to_save = []
        for shift in self.shifts:
            shift_dict = dict(zip(self.headers, shift))
            if 'Tasks' in shift_dict:
                shift_dict['Tasks'] = json.loads(shift_dict['Tasks'])
            data_to_save.append(shift_dict)
        
        with open(self.data_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)
