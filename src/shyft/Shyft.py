import configparser
import datetime
import json
import multiprocessing
import os
import platform
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog, Text, colorchooser

# Configuration and Paths setup
if platform.system() == "Darwin":
    APP_SUPPORT_DIR = Path(os.path.expanduser("~/Library/Application Support/Shyft"))
elif platform.system() == "Windows":
    APP_SUPPORT_DIR = Path("C:\\ProgramData\\Shyft")
else:
    APP_SUPPORT_DIR = Path(os.path.expanduser("~/.shyft"))

APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE_PATH = APP_SUPPORT_DIR / "data.json"
LOGS_DIR = APP_SUPPORT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_SUPPORT_DIR / "config.ini"

DEFAULT_SHIFT_STRUCTURE = {
    "Date": "",
    "Model ID": "",
    "Project ID": "",
    "In (hh:mm)": "",
    "Out (hh:mm)": "",
    "Duration (hrs)": "",
    "Hourly rate": "",
    "Gross pay": "",
}


def get_modifier_key(event):
    if platform.system() == "Darwin":
        return "Command"
    else:
        return "Control"


modifier_key = get_modifier_key(event=None)


def format_to_two_decimals(value):
    try:
        float_value = float(value)
        formatted_value = "{:.2f}".format(float_value)
        return formatted_value
    except ValueError:
        return value


def close_current_window(event):
    widget = event.widget
    if isinstance(widget, tk.Toplevel):
        widget.destroy()
    else:
        toplevel = widget.winfo_toplevel()
        if isinstance(toplevel, tk.Toplevel):
            toplevel.destroy()


def minimize_window(event=None):
    widget = event.widget.winfo_toplevel()
    widget.iconify()


class TimerWindow:
    def __init__(self, root, time_color="#A78C7B", bg_color="#FFBE98"):
        self.root = root
        self.root.title("Timer")
        if platform.system() == "Darwin":
            self.root.geometry("140x70")
        else:
            self.root.geometry("200x85")
        self.root.configure(bg=bg_color)
        self.elapsed_time = timedelta(0)
        self.running = False
        self.last_time = None
        self.time_color = time_color
        self.bg_color = bg_color
        self.timer_label = tk.Label(
            self.root,
            text="00:00:00",
            font=("Helvetica Neue", 32, "bold"),
            fg=self.time_color,
            bg=self.bg_color,
        )
        self.timer_label.pack(padx=5, pady=0)

        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill="x", pady=0)

        button_font = ("Helvetica", 10)
        self.start_button = tk.Button(
            button_frame,
            text="Start",
            command=self.start,
            bg=self.bg_color,
            fg=self.time_color,
            highlightbackground=self.bg_color,
            highlightthickness=0,
            bd=0,
            font=button_font,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=2)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop,
            bg=self.bg_color,
            fg=self.time_color,
            highlightbackground=self.bg_color,
            highlightthickness=0,
            bd=0,
            font=button_font,
        )
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.reset_button = tk.Button(
            button_frame,
            text="Reset",
            command=self.reset,
            bg=self.bg_color,
            fg=self.time_color,
            highlightbackground=self.bg_color,
            highlightthickness=0,
            bd=0,
            font=button_font,
        )
        self.reset_button.grid(row=0, column=2, sticky="ew", padx=2)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        self.update_timer_thread = threading.Thread(target=self.update_timer)
        self.update_timer_thread.daemon = True
        self.update_timer_thread.start()

    def start(self):
        if not self.running:
            self.running = True
            self.last_time = datetime.now()

    def stop(self):
        if self.running:
            self.running = False
            self.elapsed_time += datetime.now() - self.last_time

    def reset(self) -> None:
        self.stop()
        self.elapsed_time = timedelta(0)
        self.timer_label.config(text="00:00:00")

    def update_timer(self):
        while True:
            try:
                if self.running and self.timer_label.winfo_exists():
                    current_time = datetime.now()
                    delta = current_time - self.last_time
                    elapsed = self.elapsed_time + delta
                    self.root.after(
                        0,
                        lambda: self.timer_label.config(
                            text=str(elapsed).split(".")[0].rjust(8, "0")
                        ),
                    )
                time.sleep(0.1)
            except tk.TclError as e:
                print(f"Error updating label: {e}")
                break


class ShyftGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Shyft")
        self.time_color = "#A78C7B"
        self.bg_color = "#FFBE98"
        self.btn_text_color = "#A78C7B"
        self.data_file_path = DATA_FILE_PATH
        self.root.configure(bg=self.bg_color)
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILE)
        if platform.system() == "Darwin":
            self.selected_theme = "aqua"
        else:
            self.selected_theme = "default"
        self.timer_topmost = False
        self.timer_topmost_var = tk.BooleanVar(value=self.timer_topmost)
        self.configure_styles()
        self.data = {}
        self.setup_menu()
        self.create_widgets()
        self.refresh_view()
        self.timer_window = None
        self.root.resizable(True, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.root.bind_all(f"<{modifier_key}-m>", minimize_window)

    def toggle_timer_topmost(self):
        if self.timer_window:
            current_topmost_state = self.timer_window.root.attributes("-topmost")
            new_topmost_state = not current_topmost_state
            self.timer_window.root.attributes("-topmost", new_topmost_state)
        self.config.set("Theme", "timer_topmost", str(new_topmost_state))
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)

    def on_quit(self, event=None):
        self.running = False
        self.root.destroy()

    def configure_styles(self):
        self.style = ttk.Style(self.root)
        self.update_styles()
        self.style.theme_use(self.selected_theme)

    def update_styles(self):
        # self.style.configure("TEntry", background="white")
        # self.style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
        # self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), foreground="black", background="#ccc")
        self.style.map(
            "Treeview",
            background=[("selected", "#FFBE98")],
            foreground=[("selected", "black")],
        )
        self.style.configure(
            "highlight.Treeview", background="#FFBE98", foreground="black"
        )

    def load_data(self):
        current_working_directory = os.getcwd()
        if current_working_directory != APP_SUPPORT_DIR:
            os.chdir(APP_SUPPORT_DIR)
        try:
            if self.data_file_path.exists():
                with self.data_file_path.open("r") as f:
                    self.data = json.load(f).get("data", {})
                    for key in self.data:
                        for k in DEFAULT_SHIFT_STRUCTURE:
                            self.data[key].setdefault(k, "")
                print(f"Loaded data: {self.data}")
            else:
                self.data = {}
                print("Data file does not exist. Initialized with empty data.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            self.data = {}
        except Exception as e:
            print(f"Failed to load data file: {e}")
            self.data = {}

    def save_data(self):
        current_working_directory = os.getcwd()
        if current_working_directory != APP_SUPPORT_DIR:
            os.chdir(APP_SUPPORT_DIR)
        try:
            with self.data_file_path.open("w") as f:
                json.dump({"data": self.data}, f, indent=4)
            self.config.set("Theme", "selected", self.selected_theme)
            with open(CONFIG_FILE, "w") as config_file:
                self.config.write(config_file)
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    def create_widgets(self):
        self.tree = ttk.Treeview(
            self.root,
            columns=(
                "ID",
                "Date",
                "Model ID",
                "Project ID",
                "In (hh:mm)",
                "Out (hh:mm)",
                "Duration (hrs)",
                "Hourly rate",
                "Gross pay",
            ),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, anchor="w", width=100)
        self.tree.pack(expand=True, fill="both")

        button_frame = ttk.Frame(self.root, style="TFrame")
        button_frame.pack(side="bottom", fill="both", expand=True)

        ttk.Button(
            button_frame,
            text="Manual Entry",
            command=self.manual_entry,
            style="TButton",
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame, text="Edit Shift", command=self.edit_shift, style="TButton"
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame,
            text="Delete Shift",
            command=self.delete_shift,
            style="TButton",
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame,
            text="Refresh View",
            command=self.refresh_view,
            style="TButton",
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame, text="View Logs", command=self.view_logs, style="TButton"
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame, text="Autologger", command=self.autologger, style="TButton"
        ).pack(side="left", expand=True)
        ttk.Button(
            button_frame, text="Totals", command=self.calculate_totals, style="TButton"
        ).pack(side="left", expand=True)

    def refresh_view(self):
        self.load_data()
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for id, shift in self.data.items():
            self.tree.insert(
                "",
                "end",
                iid=id,
                values=(
                    id,
                    shift.get("Date", "N/A"),
                    shift.get("Model ID", "N/A"),
                    shift.get("Project ID", "N/A"),
                    shift.get("In (hh:mm)", "N/A"),
                    shift.get("Out (hh:mm)", "N/A"),
                    shift.get("Duration (hrs)", "N/A"),
                    shift.get("Hourly rate", "N/A"),
                    shift.get("Gross pay", "N/A"),
                ),
            )
    
        # Select the first item in the tree view
        first_item = self.tree.get_children()
        if first_item:
            self.tree.selection_set(first_item[0])
            self.tree.focus(first_item[0])

    def calculate_totals(self, event=None):
        number_of_shifts = len(self.data.values())
        total_hours_worked = sum(
            float(shift["Duration (hrs)"]) for shift in self.data.values()
        )
        total_gross_pay = sum(float(shift["Gross pay"]) for shift in self.data.values())
        tax_liability = total_gross_pay * 0.27
        net_income = total_gross_pay - tax_liability

        totals_window = tk.Toplevel(self.root)
        totals_window.title("Totals")
        totals_window.bind(f"<{modifier_key}-w>", close_current_window)
        totals_window.bind(f"<{modifier_key}-W>", close_current_window)

        columns = ("Description", "Value")
        totals_tree = ttk.Treeview(totals_window, columns=columns, show="headings")
        totals_tree.heading("Description", text="Description", anchor="w")
        totals_tree.heading("Value", text="Value", anchor="w")
        totals_tree.column("Description", anchor="w", width=200)
        totals_tree.column("Value", anchor="e", width=50)
        totals_tree.pack(expand=True, fill="both")

        totals_tree.insert("", "end", values=("Shifts Worked", number_of_shifts))
        totals_tree.insert(
            "", "end", values=("Total Hours Worked", f"{total_hours_worked:.2f}")
        )
        totals_tree.insert(
            "", "end", values=("Total Gross Pay", f"${total_gross_pay:.2f}")
        )
        totals_tree.insert(
            "", "end", values=("Estimated Tax Liability (27%)", f"${tax_liability:.2f}")
        )
        totals_tree.insert(
            "", "end", values=("Estimated Net Income", f"${net_income:.2f}")
        )

        def on_close():
            totals_window.destroy()
            self.root.focus_force()  # Return focus to the main window

        totals_window.protocol("WM_DELETE_WINDOW", on_close)
        totals_window.grab_set()
        totals_window.wait_window()

    def view_logs(self, event=None):
        os.chdir(LOGS_DIR)
        log_window = tk.Toplevel(self.root)
        log_window.title("View Logs")
        log_window.geometry("480x640")
        log_window.bind("<Command-w>", close_current_window)
        log_window.bind("<Command-W>", close_current_window)

        tree_frame = ttk.Frame(log_window)
        tree_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        log_tree = ttk.Treeview(
            tree_frame, columns=["Log Files"], show="headings", height=4
        )
        log_tree.heading("Log Files", text="Log Files")
        log_tree.column("Log Files", anchor="w")
        log_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)

        log_tree.tag_configure("highlight", background="#FFBE98")

        log_files = sorted(
            [
                f
                for f in os.scandir(LOGS_DIR)
                if f.is_file() and not f.name.startswith(".")
            ],
            key=lambda x: x.name,
        )
        for log_file in log_files:
            log_tree.insert("", "end", iid=log_file.name, values=[log_file.name])

        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        text_widget = Text(text_frame, wrap="word")
        text_widget.pack(fill=tk.BOTH, expand=True)

        def on_log_selection(event):
            for item in log_tree.get_children():
                log_tree.item(item, tags=())

            selected_item = log_tree.selection()
            if selected_item:
                log_tree.item(selected_item[0], tags=("highlight",))

                log_file_path = os.path.join(LOGS_DIR, selected_item[0])
                with open(log_file_path, "r") as file:
                    content = file.read()
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)

        log_tree.bind("<<TreeviewSelect>>", on_log_selection)

        def on_close():
            log_window.destroy()
            self.root.focus_force()  # Return focus to the main window

        log_window.protocol("WM_DELETE_WINDOW", on_close)

    def validate_time_format(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format.")

    def calculate_duration(self, start, end):
        try:
            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            duration = (end_dt - start_dt).total_seconds() / 3600.0
            return duration
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format.")

    def submit_action(self):
        try:
            self.validate_time_format(self.entries["In (hh:mm)"].get())
            self.validate_time_format(self.entries["Out (hh:mm)"].get())

            new_data = {field: self.entries[field].get() for field in self.fields}
            if any(v == "" for v in new_data.values()):
                messagebox.showerror("Error", "All fields must be filled out.")
                return

            new_id = max([int(x) for x in self.data.keys()], default=0) + 1
            formatted_id = self.format_id(new_id)

            duration_hrs = self.calculate_duration(
                new_data["In (hh:mm)"], new_data["Out (hh:mm)"]
            )
            new_data["Duration (hrs)"] = "{:.2f}".format(duration_hrs)

            try:
                hourly_rate = float(new_data["Hourly rate"])
                new_data["Hourly rate"] = "{:.2f}".format(hourly_rate)
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Invalid input for 'Hourly rate'. Please enter a numerical value.",
                )
                return

            gross_pay = hourly_rate * duration_hrs
            new_data["Gross pay"] = "{:.2f}".format(gross_pay)

            lock = threading.Lock()
            with lock:
                self.data[formatted_id] = new_data
                self.save_data()
            self.root.after(0, self.populate_tree)  # This will refresh the tree and select the first item
            self.entries["window"].destroy()
            messagebox.showinfo("Success", "Shift logged successfully.")
            self.root.focus_force()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        self.refresh_view()  # This will call populate_tree again, ensuring the first item is selected

    def manual_entry(self, event=None):
        window = tk.Toplevel(self.root)
        window.title("Manual Entry")
        window.bind(f"<{modifier_key}-w>", close_current_window)
        window.bind(f"<{modifier_key}-W>", close_current_window)

        self.entries = {}
        self.fields = [
            "Date",
            "Model ID",
            "Project ID",
            "In (hh:mm)",
            "Out (hh:mm)",
            "Hourly rate",
        ]
        uppercase_fields = ["Project ID", "Model ID"]

        for field in self.fields:
            row = ttk.Frame(window, style="TFrame")
            label = ttk.Label(row, width=20, text=field, anchor="w", style="TLabel")
            entry_var = tk.StringVar()
            entry = ttk.Entry(row, textvariable=entry_var, style="TEntry")
            if field in uppercase_fields:
                entry_var.trace_add(
                    "write", lambda *_, var=entry_var: var.set(var.get().upper())
                )
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            self.entries[field] = entry

        self.entries["window"] = window

        cancel_button = ttk.Button(
            window, text="Cancel", command=window.destroy, style="TButton"
        )
        cancel_button.pack(side=tk.LEFT, padx=5, expand=True)

        def submit_and_close(event=None):
            self.submit_action()

        submit_button = ttk.Button(
            window, text="Submit", command=submit_and_close, style="TButton"
        )
        submit_button.pack(side=tk.RIGHT, padx=5, expand=True)

        window.bind("<Return>", submit_and_close)  # Bind Enter key to submit
        self.entries[self.fields[0]].focus_set()

    def edit_shift(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a shift to edit.")
            return
        selected_id = selected_item[0]
        shift = self.data.get(selected_id)

        window = tk.Toplevel(self.root)
        window.title("Edit Shift")
        window.bind(f"<{modifier_key}-w>", close_current_window)
        window.bind(f"<{modifier_key}-W>", close_current_window)

        entries = {}
        entry_widgets = {}  # New dictionary to store Entry widgets
        fields = [
            "Date",
            "Model ID",
            "Project ID",
            "In (hh:mm)",
            "Out (hh:mm)",
            "Duration (hrs)",
            "Hourly rate",
            "Gross pay",
        ]
        uppercase_fields = ["Project ID", "Model ID"]

        for field in fields:
            row = ttk.Frame(window, style="TFrame")
            label = ttk.Label(row, width=15, text=field, anchor="w", style="TLabel")
            entry_var = tk.StringVar(value=str(shift.get(field, "")))
            entry = ttk.Entry(row, textvariable=entry_var, style="TEntry")
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries[field] = entry_var
            entry_widgets[field] = entry  # Store the Entry widget

        for field in uppercase_fields:
            entry_var = entries[field]
            entry_var.trace_add(
                "write", lambda *args, var=entry_var: var.set(var.get().upper())
            )

        entries["Date"].trace_add(
            "write", lambda *args: entry_widgets["Date"].focus_set()
        )

        cancel_button = ttk.Button(
            window, text="Cancel", command=window.destroy, style="TButton"
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

        submit_button = ttk.Button(
            window,
            text="Submit",
            command=lambda: self.submit_action_edit(
                window, entries, fields, selected_id
            ),
            style="TButton"
        )

        def submit_and_close(event=None):
            self.submit_action_edit(window, entries, fields, selected_id)

        submit_button.pack(side=tk.RIGHT, padx=5)
        window.bind("<Return>", submit_and_close)  # Bind Enter key to submit
        entry_widgets["Date"].focus_set()  # Set focus to the Date Entry widget

    def submit_action_edit(self, root, entries, fields, selected_id):
        try:
            updated_data = {field: entries[field].get() for field in fields}
            if any(v == "" for v in updated_data.values()):
                messagebox.showerror("Error", "All fields must be filled out.")
                return

            updated_data["Hourly rate"] = f"{float(updated_data['Hourly rate']):.2f}"
            updated_data["Gross pay"] = f"{float(updated_data['Gross pay']):.2f}"

            lock = threading.Lock()
            with lock:
                self.data[selected_id] = updated_data

            save_thread = threading.Thread(
                target=lambda: self.save_and_update_view(root)
            )
            save_thread.start()
            root.destroy()
            messagebox.showinfo("Success", "Data updated successfully.")
            self.root.focus_force()
        except Exception as e:
            messagebox.showerror("Error", "Failed to update shift. Error: " + str(e))

    def save_and_update_view(self, window):
        try:
            self.save_data()
            self.root.after(0, self.populate_tree)
            window.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error", "Failed to save and update view. Error: " + str(e)
            )

    def delete_shift(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a shift to delete.")
            return
        selected_id = selected_item[0]
        response = messagebox.askyesno(
            "Confirm Delete", "Are you sure you want to delete the selected shift?"
        )
        if response:
            del self.data[selected_id]
            self.save_data()
            self.populate_tree()
            self.root.focus_force()

    def save_data_and_update_view(self, notes_window):
        try:
            self.save_data()
            self.populate_tree()
            notes_window.destroy()

            if self.timer_window:
                self.timer_window.reset()
                self.timer_window.root.destroy()
                self.timer_window = None
                self.enable_theme_menu()
                self.disable_topmost_menu()

            self.root.focus_force()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to log shift: {str(e)}")

    def choose_time_color(self):
        print("Entering choose_time_color")
        color_code = colorchooser.askcolor(title="Choose Stopclock Timestring Color")[1]
        if color_code:
            self.time_color = color_code
            self.save_config()

    def choose_bg_color(self):
        print("Entering choose_bg_color")
        color_code = colorchooser.askcolor(title="Choose Stopclock Background Color")[1]
        if color_code:
            self.bg_color = color_code
            self.save_config()

    def choose_btn_text_color(self):
        print("Entering choose_btn_text_color")
        color_code = colorchooser.askcolor(title="Choose Stopclock Button Text Color")[
            1
        ]
        if color_code:
            self.btn_text_color = color_code
            self.save_config()

    def save_config(self):
        if not self.config.has_section("Colors"):
            self.config.add_section("Colors")
        self.config.set("Colors", "time_color", self.time_color)
        self.config.set("Colors", "bg_color", self.bg_color)
        self.config.set("Colors", "btn_text_color", self.btn_text_color)
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)
        self.update_styles()
        messagebox.showinfo("Settings Saved", "New settings have been applied.")

    def autologger(self, event=None):
        model_id_response = simpledialog.askstring(
            "Model ID", "Enter Model ID", parent=self.root
        )
        if not model_id_response:
            return None
        model_id = model_id_response.upper()

        project_id_response = simpledialog.askstring(
            "Project ID", "Enter Project ID", parent=self.root
        )
        if not project_id_response:
            return None
        project_id = project_id_response.upper()

        hourly_rate = simpledialog.askstring(
            "Hourly rate", "Enter Hourly Rate", parent=self.root
        )
        try:
            hourly_rate = float(hourly_rate)
        except (TypeError, ValueError):
            if not hourly_rate:
                return
            else:
                messagebox.showerror(
                    "Error", "Invalid hourly rate; please enter a numeric value."
                )
                return None

        notes_window = tk.Toplevel(self.root)
        notes_window.title("Notes - Autologger")
        if platform.system() == "Darwin":
            notes_window.geometry("400x400")
        else:
            notes_window.geometry("450x450")

        text = Text(
            notes_window,
            wrap=tk.WORD,
            height=1,
        )
        text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        button_frame = tk.Frame(notes_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        def insert_divider():
            divider = "_" * 50 + "\n"
            text.insert(tk.INSERT, divider)

        if self.timer_window is None or not tk.Toplevel.winfo_exists(
            self.timer_window.root
        ):
            timer_window = tk.Toplevel(self.root)
            self.timer_window = TimerWindow(
                timer_window, time_color=self.time_color, bg_color=self.bg_color
            )
            self.timer_window.start()
            topmost_state = self.config.getboolean("Theme", "timer_topmost")
            self.timer_window.root.attributes("-topmost", topmost_state)
            self.disable_theme_menu()
            self.enable_topmost_menu()

        def submit_notes():
            if self.timer_window:
                self.timer_window.stop()
                elapsed_time = self.timer_window.elapsed_time

                seconds_in_a_minute = 60
                whole_minutes = elapsed_time.total_seconds() // seconds_in_a_minute
                duration_hrs = whole_minutes / 60

                gross_pay = duration_hrs * hourly_rate

                new_id = max([int(x) for x in self.data.keys()], default=0) + 1
                formatted_id = self.format_id(new_id)

                if not LOGS_DIR.exists():
                    LOGS_DIR.mkdir(parents=True, exist_ok=True)

                log_file_path = LOGS_DIR / f"{formatted_id}.md"
                with open(log_file_path, "w") as file:
                    file.write(text.get("1.0", tk.END))

                lock = threading.Lock()

                with lock:
                    self.data[formatted_id] = {
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Model ID": model_id,
                        "Project ID": project_id,
                        "In (hh:mm)": (datetime.now() - elapsed_time).strftime("%H:%M"),
                        "Out (hh:mm)": datetime.now().strftime("%H:%M"),
                        "Duration (hrs)": f"{duration_hrs:.2f}",
                        "Hourly rate": f"{hourly_rate:.2f}",
                        "Gross pay": f"{gross_pay:.2f}",
                    }
                    save_thread = threading.Thread(
                        target=lambda: self.save_data_and_update_view(notes_window)
                    )
                    save_thread.start()
                messagebox.showinfo("Success", "Shift logged successfully.")
            else:
                messagebox.showerror("Error", "Timer is not running.")

        tk.Button(
            button_frame,
            text="Submit",
            command=submit_notes,
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Button(
            button_frame,
            text="Cancel",
            command=lambda: [notes_window.destroy(), self.timer_window.root.destroy()],
        ).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            button_frame,
            text="Insert Divider",
            command=insert_divider,
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def format_id(self, id):
        return f"{id:04d}"

    def change_theme(self, theme_name):
        self.style.theme_use(theme_name)
        self.config.set("Theme", "selected", theme_name)
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)
        print(f"Theme selection <{theme_name}> saved to `config.ini`.")

    def enable_topmost_menu(self):
        self.view_menu.entryconfig("Timer Always on Top", state="normal")

    def disable_topmost_menu(self):
        self.view_menu.entryconfig("Timer Always on Top", state="disabled")

    def disable_theme_menu(self):
        self.menu_bar.entryconfig("Theme", state="disabled")

    def enable_theme_menu(self):
        self.menu_bar.entryconfig("Theme", state="normal")

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.setup_theme_menu()
        self.setup_view_menu()
        self.root.config(menu=self.menu_bar)

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.setup_theme_menu()
        self.setup_view_menu()
        self.setup_settings_menu()  # New method to set up Settings menu
        self.root.config(menu=self.menu_bar)

    def setup_theme_menu(self):
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(
            label="Default", command=lambda: self.change_theme("default")
        )
        self.theme_menu.add_command(
            label="Classic", command=lambda: self.change_theme("classic")
        )
        self.theme_menu.add_command(
            label="Alt", command=lambda: self.change_theme("alt")
        )
        self.theme_menu.add_command(
            label="Clam", command=lambda: self.change_theme("clam")
        )
        if platform.system() == "Darwin":
            self.theme_menu.add_command(
                label="Aqua", command=lambda: self.change_theme("aqua")
            )
        self.menu_bar.add_cascade(label="Theme", menu=self.theme_menu)

    def setup_view_menu(self):
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_checkbutton(
            label="Timer Always on Top",
            command=self.toggle_timer_topmost,
            variable=self.timer_topmost_var,
        )
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

    def setup_settings_menu(self):
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(
            label="Stopclock Timestring Color", command=self.choose_time_color
        )
        self.settings_menu.add_command(
            label="Stopclock Background Color", command=self.choose_bg_color
        )
        self.settings_menu.add_command(
            label="Stopclock Button Text Color", command=self.choose_btn_text_color
        )
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)


def run_tkinter_app():
    root = tk.Tk()
    style = ttk.Style()
    app = ShyftGUI(root)
    app.setup_menu()
    root.bind(f"<{modifier_key}-a>", app.autologger)
    root.bind(f"<{modifier_key}-d>", app.delete_shift)
    root.bind(f"<{modifier_key}-e>", app.edit_shift)
    root.bind(f"<{modifier_key}-n>", app.manual_entry)
    root.bind(f"<{modifier_key}-l>", app.view_logs)
    root.bind(f"<{modifier_key}-t>", app.calculate_totals)
    root.bind(f"<{modifier_key}-A>", app.autologger)
    root.bind(f"<{modifier_key}-D>", app.delete_shift)
    root.bind(f"<{modifier_key}-E>", app.edit_shift)
    root.bind(f"<{modifier_key}-N>", app.manual_entry)
    root.bind(f"<{modifier_key}-L>", app.view_logs)
    root.bind(f"<{modifier_key}-T>", app.calculate_totals)
    root.bind_all(f"<{modifier_key}-Q>", app.on_quit)
    root.bind_all(f"<{modifier_key}-q>", app.on_quit)

    root.mainloop()


def main():
    process = multiprocessing.Process(target=run_tkinter_app)
    process.start()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
