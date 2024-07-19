import json
import logging
import multiprocessing
import os
import platform
import re
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog, Text, colorchooser
import appdirs
import configparser

# Initialize application-specific directory paths
app_name = "Shyft"
app_author = "ENCLAIM"

# Determine application-specific directories
app_data_dir = appdirs.user_data_dir(app_name, app_author)
app_config_dir = appdirs.user_config_dir(app_name, app_author)
app_cache_dir = appdirs.user_cache_dir(app_name, app_author)

# Ensure directories exist
Path(app_data_dir).mkdir(parents=True, exist_ok=True)
Path(app_config_dir).mkdir(parents=True, exist_ok=True)
Path(app_cache_dir).mkdir(parents=True, exist_ok=True)

# Initialize logging
LOGS_DIR = Path(app_data_dir) / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOGS_DIR / "app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configuration and Paths setup
DATA_FILE_PATH = Path(app_data_dir) / "data.json"
CONFIG_FILE = Path(app_config_dir) / "config.ini"

# Read configuration file
config = configparser.ConfigParser()
if CONFIG_FILE.exists():
    config.read(CONFIG_FILE)
else:
    logger.warning(f"Configuration file {CONFIG_FILE} does not exist. Using default settings.")

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

logger.debug("Configuration and paths setup completed.")

# Modifier key
if platform.system() == "Darwin":
    modifier_key = "Command" # macOS
else:
    modifier_key = "Control"

def format_to_two_decimals(value):
    try:
        float_value = float(value)
        formatted_value = "{:.2f}".format(float_value)
        return formatted_value
    except ValueError:
        logger.error(f"ValueError: Unable to format value {value} to two decimals.")
        return value


def close_current_window(event):
    widget = event.widget
    if isinstance(widget, tk.Toplevel):
        widget.destroy()
    else:
        toplevel = widget.winfo_toplevel()
        if isinstance(toplevel, tk.Toplevel):
            toplevel.destroy()
    logger.debug("Closed current window.")


def minimize_window(event=None):
    widget = event.widget.winfo_toplevel()
    widget.iconify()
    logger.debug(f"Minimized window: {widget}")


class TimerWindow:
    def __init__(self, root, time_color="#A78C7B", bg_color="#FFBE98"):
        self.root = root
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILE)

        if not self.config.has_section("Window"):
            self.config.add_section("Window")
            self.custom_width = 200
            self.custom_height = 100
            logger.debug(
                "No 'Window' section found in config file, using default dimensions."
            )
        else:
            self.custom_width = self.config.getint("Window", "width", fallback=200)
            self.custom_height = self.config.getint("Window", "height", fallback=100)
            logger.debug(
                f"Loaded custom dimensions from config file: width={self.custom_width}, height={self.custom_height}"
            )

        self.root.title("Timer")
        self.root.geometry(f"{self.custom_width}x{self.custom_height}")
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
        self.timer_label.pack(expand=True, padx=0, pady=(5, 0))

        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill="x", padx=10, pady=(0, 5))

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

        self.update_timer_thread = threading.Thread(
            target=self.update_timer, daemon=True
        )
        self.update_timer_thread.start()
        logger.info("Timer window initialized.")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start(self):
        if not self.running:
            self.running = True
            self.last_time = datetime.now()
            logger.debug("Timer started.")

    def stop(self):
        if self.running:
            self.running = False
            self.elapsed_time += datetime.now() - self.last_time
            logger.debug("Timer stopped.")

    def reset(self):
        self.stop()
        self.elapsed_time = timedelta(0)
        self.update_label("00:00:00")
        logger.debug("Timer reset.")

    def update_label(self, text):
        if self.timer_label.winfo_exists():
            self.timer_label.config(text=text)

    def update_timer(self):
        while True:
            if self.running:
                current_time = datetime.now()
                delta = current_time - self.last_time
                elapsed = self.elapsed_time + delta
                self.root.after(
                    0, self.update_label, str(elapsed).split(".")[0].rjust(8, "0")
                )
            time.sleep(0.1)

    def on_close(self):
        self.running = False
        self.config.set("Window", "width", str(self.root.winfo_width()))
        self.config.set("Window", "height", str(self.root.winfo_height()))
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)
        logger.debug(
            f"Timer window dimensions saved: width={self.root.winfo_width()}, height={self.root.winfo_height()}"
        )
        self.root.after(0, self.root.destroy)
        logger.debug("Timer window closed.")


class IndependentAskString(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.result = None

        self.geometry("300x150")
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="20 20 20 0")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=prompt).pack(pady=(0, 10))
        self.entry = ttk.Entry(main_frame, width=40)
        self.entry.pack(pady=(0, 20))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.grid(row=0, column=0, padx=(0, 5), sticky='e')
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).grid(row=0, column=1, padx=(5, 0), sticky='w')

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Center the dialog on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

        # Bind Enter key to OK button
        self.bind('<Return>', lambda event: ok_button.invoke())

        self.entry.focus_set()
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        self.result = self.entry.get()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()                

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
        if not self.config.has_section("Theme"):
            self.config.add_section("Theme")
        if platform.system() == "Darwin":
            self.selected_theme = "aqua"
        else:
            self.selected_theme = "default"
        self.timer_topmost = self.config.getboolean(
            "Theme", "timer_topmost", fallback=False
        )
        self.timer_topmost_var = tk.BooleanVar(value=self.timer_topmost)
        self.configure_styles()
        self.data = {"data": {}}
        self.setup_menu()
        self.create_widgets()
        self.refresh_view()
        self.timer_window = None
        self.root.resizable(True, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.root.bind_all(f"<{modifier_key}-m>", minimize_window)
        logger.info("ShyftGUI initialized.")

    def toggle_timer_topmost(self):
        if self.timer_window:
            current_topmost_state = self.timer_window.root.attributes("-topmost")
            new_topmost_state = not current_topmost_state
            self.timer_window.root.attributes("-topmost", new_topmost_state)
            self.config.set("Theme", "timer_topmost", str(new_topmost_state))
            with open(CONFIG_FILE, "w") as config_file:
                self.config.write(config_file)
            self.timer_topmost_var.set(new_topmost_state)
            logger.debug(f"Timer topmost state set to {new_topmost_state}.")

    def on_quit(self, event=None):
        self.running = False
        self.root.destroy()
        logger.info("Application quit.")

    def configure_styles(self):
        self.style = ttk.Style(self.root)
        self.update_styles()
        self.style.theme_use(self.selected_theme)

    def update_styles(self):
        self.style.map(
            "Treeview",
            background=[("selected", "#FFBE98")],
            foreground=[("selected", "black")],
        )
        self.style.configure(
            "highlight.Treeview", background="#FFBE98", foreground="black"
        )

    def load_data(self):
        try:
            if self.data_file_path.exists():
                with open(self.data_file_path, "r") as f:
                    self.data = json.load(f)
            else:
                self.data = {"data": {}}
            logger.debug(f"Loaded data: {self.data}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            self.data = {"data": {}}
        except Exception as e:
            logger.error(f"Failed to load data file: {e}")
            self.data = {"data": {}}

    def save_data(self):
        try:
            with open(self.data_file_path, "w") as f:
                json.dump(self.data, f, indent=4)
            logger.debug("Data saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            messagebox.showerror("Error", f"Failed to save data: {e}")

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
        logger.info("Widgets created.")

    def refresh_view(self):
        self.load_data()
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Sort the data keys (shift IDs) in descending order
        sorted_keys = sorted(
            self.data["data"].keys(), key=lambda x: int(x), reverse=True
        )

        for id in sorted_keys:
            shift = self.data["data"][id]
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
                    shift.get("Tasks completed", "N/A"),
                ),
            )

        # Select the first item (most recent shift)
        first_item = self.tree.get_children()
        if first_item:
            self.tree.selection_set(first_item[0])
            self.tree.focus(first_item[0])

        logger.debug("Tree view populated with updated data.")

    def calculate_totals(self, event=None):
        logger.debug("Entering calculate_totals function")
        
        def create_totals_window():
            try:
                logger.debug("Starting to calculate totals")
                
                if not isinstance(self.data, dict) or "data" not in self.data:
                    raise ValueError("Invalid data structure")
                
                number_of_shifts = len(self.data["data"])
                logger.debug(f"Number of shifts: {number_of_shifts}")
                
                if number_of_shifts == 0:
                    raise ValueError("No shifts found in data")
                
                try:
                    total_hours_worked = sum(
                        float(shift["Duration (hrs)"]) for shift in self.data["data"].values()
                    )
                    logger.debug(f"Total hours worked: {total_hours_worked}")
                except (KeyError, ValueError) as e:
                    logger.error(f"Error calculating total hours: {str(e)}")
                    total_hours_worked = 0
                
                try:
                    total_gross_pay = sum(float(shift["Gross pay"]) for shift in self.data["data"].values())
                    logger.debug(f"Total gross pay: {total_gross_pay}")
                except (KeyError, ValueError) as e:
                    logger.error(f"Error calculating total gross pay: {str(e)}")
                    total_gross_pay = 0
                
                tax_liability = total_gross_pay * 0.27
                net_income = total_gross_pay - tax_liability
                
                logger.debug("Creating totals window")
                totals_window = tk.Toplevel(self.root)
                totals_window.title("Totals")
                totals_window.bind(f"<{modifier_key}-w>", close_current_window)
                totals_window.bind(f"<{modifier_key}-W>", close_current_window)

                columns = ("Description", "Value")
                totals_tree = ttk.Treeview(totals_window, columns=columns, show="headings")
                totals_tree.heading("Description", text="Description", anchor="w")
                totals_tree.heading("Value", text="Value", anchor="w")
                totals_tree.column("Description", anchor="w", width=200)
                totals_tree.column("Value", anchor="e", width=150)
                totals_tree.pack(expand=True, fill="both")

                totals_tree.insert("", "end", values=("Shifts Worked", number_of_shifts))
                totals_tree.insert("", "end", values=("Total Hours Worked", f"{total_hours_worked:.2f}"))
                totals_tree.insert("", "end", values=("Total Gross Pay", f"${total_gross_pay:.2f}"))
                totals_tree.insert("", "end", values=("Estimated Tax Liability (27%)", f"${tax_liability:.2f}"))
                totals_tree.insert("", "end", values=("Estimated Net Income", f"${net_income:.2f}"))

                def on_close():
                    totals_window.destroy()
                    self.root.focus_force()  # Return focus to the main window

                totals_window.protocol("WM_DELETE_WINDOW", on_close)
                totals_window.grab_set()
                logger.debug("Totals window displayed successfully")
                
            except Exception as e:
                logger.error(f"Error in calculate_totals: {str(e)}")
                messagebox.showerror("Error", f"An error occurred while calculating totals: {str(e)}")

        self.root.after(0, create_totals_window)
        logger.debug("Exiting calculate_totals function")
    
    def view_logs(self, event=None):
        logger.debug(f"Opening logs directory: {LOGS_DIR}")
        
        if not LOGS_DIR.exists():
            logger.warning(f"Logs directory does not exist: {LOGS_DIR}")
            messagebox.showinfo("No Logs", "No log files found.")
            return

        log_window = tk.Toplevel(self.root)
        log_window.geometry("480x640")
        log_window.title("View Logs")
        log_window.bind(f"<{modifier_key}-w>", close_current_window)
        log_window.bind(f"<{modifier_key}-W>", close_current_window)

        tree_frame = ttk.Frame(log_window)
        tree_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        log_tree = ttk.Treeview(
            tree_frame, columns=["Log Files"], show="headings", height=4
        )
        log_tree.heading("Log Files", text="Log Files")
        log_tree.column("Log Files", anchor="w")
        log_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)

        log_tree.tag_configure("highlight", background="#FFBE98")

        # Get all log files and sort them
        log_files = sorted(
            [
                f.name
                for f in LOGS_DIR.iterdir()
                if f.is_file() and f.suffix == '.md'
            ],
            key=lambda x: os.path.getmtime(LOGS_DIR / x),
            reverse=True
        )

        logger.debug(f"Found {len(log_files)} log files")

        for log_file in log_files:
            log_tree.insert("", "end", iid=log_file, values=[log_file])

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

                log_file_path = LOGS_DIR / selected_item[0]
                try:
                    with open(log_file_path, "r") as file:
                        content = file.read()
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert("1.0", content)
                except Exception as e:
                    logger.error(f"Error reading log file {log_file_path}: {str(e)}")
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert("1.0", f"Error reading log file: {str(e)}")

        log_tree.bind("<<TreeviewSelect>>", on_log_selection)

        def on_close():
            log_window.destroy()
            self.root.focus_force()  # Return focus to the main window

        log_window.protocol("WM_DELETE_WINDOW", on_close)
        logger.debug("Logs window displayed.")

        # Select the first item (most recent log) if available
        first_item = log_tree.get_children()
        if first_item:
            log_tree.selection_set(first_item[0])
            log_tree.focus(first_item[0])
            log_tree.event_generate("<<TreeviewSelect>>")

        # Make the log window active and set focus to the log tree
        log_window.lift()
        log_window.focus_force()
        log_tree.focus_set()

        # Wait for the window to be fully created and then set focus again
        log_window.update()
        log_tree.focus_set()
    def validate_time_format(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            logger.error(f"Invalid time format: {time_str}. Use HH:MM format.")
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
            logger.error("Invalid time format. Use HH:MM format.")
            raise ValueError("Invalid time format. Use HH:MM format.")

    def submit_action(self):
        try:
            self.validate_time_format(self.entries["In (hh:mm)"].get())
            self.validate_time_format(self.entries["Out (hh:mm)"].get())

            new_data = {field: self.entries[field].get() for field in self.fields}
            if any(v == "" for v in new_data.values()):
                messagebox.showerror("Error", "All fields must be filled out.")
                return

            new_id = max([int(x) for x in self.data["data"].keys()], default=0) + 1
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
                self.data["data"][formatted_id] = new_data
                self.save_data()
            self.root.after(
                0, self.populate_tree
            )  # This will refresh the tree and select the first item
            self.entries["window"].destroy()
            messagebox.showinfo("Success", "Shift logged successfully.")
            self.root.focus_force()
            logger.info("Shift logged successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            logger.error(f"Shift logging failed: {e}")
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
        logger.debug("Manual entry window displayed.")

    def edit_shift(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a shift to edit.")
            return
        selected_id = selected_item[0]
        shift = self.data["data"].get(selected_id)

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
            style="TButton",
        )

        def submit_and_close(event=None):
            self.submit_action_edit(window, entries, fields, selected_id)

        submit_button.pack(side=tk.RIGHT, padx=5)
        window.bind("<Return>", submit_and_close)  # Bind Enter key to submit
        entry_widgets["Date"].focus_set()  # Set focus to the Date Entry widget
        logger.debug("Edit shift window displayed.")

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
                self.data["data"][selected_id] = updated_data

            save_thread = threading.Thread(
                target=lambda: self.save_and_update_view(root)
            )
            save_thread.start()
            root.destroy()
            messagebox.showinfo("Success", "Data updated successfully.")
            self.root.focus_force()
            logger.info("Shift edited successfully.")
        except Exception as e:
            messagebox.showerror("Error", "Failed to update shift. Error: " + str(e))
            logger.error(f"Failed to update shift: {e}")

    def save_and_update_view(self, window):
        try:
            self.save_data()
            self.root.after(0, self.populate_tree)
            window.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error", "Failed to save and update view. Error: " + str(e)
            )
            logger.error(f"Failed to save and update view: {e}")

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
            try:
                # Delete from data structure
                del self.data["data"][selected_id]
                self.save_data()

                # Delete associated .md file
                md_file_path = LOGS_DIR / f"{selected_id}.md"
                if md_file_path.exists():
                    os.remove(md_file_path)
                    logger.info(f"Associated .md file for shift {selected_id} deleted.")
                else:
                    logger.warning(f"No .md file found for shift {selected_id}.")

                self.populate_tree()
                self.root.focus_force()
                logger.info(f"Shift {selected_id} deleted.")
            except KeyError:
                messagebox.showerror(
                    "Error", f"Shift with ID {selected_id} not found in the data."
                )
                logger.error(
                    f"Failed to delete shift {selected_id}: Shift not found in data."
                )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"An error occurred while deleting the shift: {str(e)}"
                )
                logger.error(f"Failed to delete shift {selected_id}: {str(e)}")

    def save_data_and_update_view(self, notes_window):
        try:
            self.save_data()
            self.populate_tree()
            notes_window.destroy()

            if self.timer_window:
                self.timer_window.reset()
                self.timer_window.on_close()
                self.timer_window = None
                self.enable_theme_menu()
                self.disable_topmost_menu()

            self.root.focus_force()
            logger.info("Data saved and view updated.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to log shift: {str(e)}")
            logger.error(f"Failed to log shift: {e}")

    def reinitialize_timer_window(self):
        if self.timer_window:
            self.timer_window.on_close()
            self.timer_window = TimerWindow(
                tk.Toplevel(self.root),
                time_color=self.time_color,
                bg_color=self.bg_color,
            )
            self.timer_window.start()
            topmost_state = self.config.getboolean(
                "Theme", "timer_topmost", fallback=False
            )
            self.timer_window.root.attributes("-topmost", topmost_state)
            logger.info("Timer window reinitialized with new settings.")

    def choose_time_color(self):
        if self.timer_window:
            response = messagebox.askyesno(
                "Restart Timer Required",
                "Changing the timer color requires restarting the timer. Do you want to proceed?",
            )
            if not response:
                return
        logger.debug("Entering choose_time_color.")
        color_code = colorchooser.askcolor(title="Choose Stopclock Timestring Color")[1]
        if color_code:
            self.time_color = color_code
            self.save_config()
            if self.timer_window:
                self.reinitialize_timer_window()

    def choose_bg_color(self):
        if self.timer_window:
            response = messagebox.askyesno(
                "Restart Timer Required",
                "Changing the background color requires restarting the timer. Do you want to proceed?",
            )
            if not response:
                return
        logger.debug("Entering choose_bg_color.")
        color_code = colorchooser.askcolor(title="Choose Stopclock Background Color")[1]
        if color_code:
            self.bg_color = color_code
            self.save_config()
            if self.timer_window:
                self.reinitialize_timer_window()

    def choose_btn_text_color(self):
        if self.timer_window:
            response = messagebox.askyesno(
                "Restart Timer Required",
                "Changing the button text color requires restarting the timer. Do you want to proceed?",
            )
            if not response:
                return
        logger.debug("Entering choose_btn_text_color.")
        color_code = colorchooser.askcolor(title="Choose Stopclock Button Text Color")[
            1
        ]
        if color_code:
            self.btn_text_color = color_code
            self.save_config()
            if self.timer_window:
                self.reinitialize_timer_window()

    def save_config(self):
        if not self.config.has_section("Colors"):
            self.config.add_section("Colors")
        if not self.config.has_section("Window"):
            self.config.add_section("Window")
        self.config.set("Colors", "time_color", self.time_color)
        self.config.set("Colors", "bg_color", self.bg_color)
        self.config.set("Colors", "btn_text_color", self.btn_text_color)
        if self.timer_window:
            self.config.set(
                "Window", "width", str(self.timer_window.root.winfo_width())
            )
            self.config.set(
                "Window", "height", str(self.timer_window.root.winfo_height())
            )
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)
        self.update_styles()
        messagebox.showinfo("Settings Saved", "New settings have been applied.")
        logger.info("Configuration saved.")

    def autologger(self, event=None):
        self.collected_data = []

        # Collect shared data for the shift
        shared_data = self.collect_shared_data()
        if shared_data is None:  # User cancelled
            return

        self.attempt_task(shared_data)

    def collect_shared_data(self):
        shared_fields = [
            ("Model ID", str.upper),
            ("Project ID", str.upper),
            ("Hourly Rate of Pay", float),
        ]

        shared_data = {}
        for field, transform in shared_fields:
            response = simpledialog.askstring(field, f"Enter {field}", parent=self.root)
            if response is None:  # User clicked cancel
                return None
            try:
                shared_data[field] = transform(response)
            except ValueError:
                messagebox.showerror("Error", f"Invalid input for {field}")
                return None

        return shared_data

    def create_justification_window(self, shared_data):
        justification_window = tk.Toplevel(self.root)
        justification_window.title("Rank and Justification")
        justification_window.geometry("400x400")
        justification_window.protocol("WM_DELETE_WINDOW", lambda: self.on_justification_close(justification_window))

        # Bind modifier_key + w to close/cancel
        justification_window.bind(f"<{modifier_key}-w>", lambda event: self.on_justification_close(justification_window))
        justification_window.bind(f"<{modifier_key}-W>", lambda event: self.on_justification_close(justification_window))

        # Main frame to hold all components
        main_frame = ttk.Frame(justification_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a frame for task-specific data fields
        task_data_frame = ttk.Frame(main_frame)
        task_data_frame.pack(fill=tk.BOTH, expand=True)
        
        task_fields = [
            ("Platform ID", str),
            ("Permalink", str),
            ("Response #1 ID", str),
            ("Response #2 ID", str)
        ]

        # Dictionary to store entry widgets
        task_entries = {}

        # Add labels and entry widgets to the grid
        for i, (field, transform) in enumerate(task_fields):
            label = ttk.Label(task_data_frame, text=f"Enter {field}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(task_data_frame)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
            task_entries[field] = entry

        # Make the columns expand dynamically
        task_data_frame.columnconfigure(0, weight=1)
        task_data_frame.columnconfigure(1, weight=1)

        # Add a separator (divider) here
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # Rank selection
        rank_frame = ttk.Frame(main_frame)
        rank_frame.pack(fill=tk.X)
        rank_var = tk.StringVar()
        rank_options = [
            "(1) is much better than (2).",
            "(1) is slightly better than (2).",
            "The responses are of equal quality.",
            "(2) is slightly better than (1).",
            "(2) is much better than (1).",
            "Task rejected for containing unratable content."]
            
        ttk.Label(rank_frame, text="Rank:").pack(side=tk.LEFT)
        rank_dropdown = ttk.Combobox(rank_frame, textvariable=rank_var, values=rank_options, state="readonly", width=40)
        rank_dropdown.pack(side=tk.LEFT, expand=True, fill=tk.X)
        rank_dropdown.set(rank_options[0])

        # Justification text box
        justification_frame = ttk.Frame(main_frame)
        justification_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)
        ttk.Label(justification_frame, text="Justification:").pack()
        justification_text = Text(justification_frame, wrap=tk.WORD, height=8)
        justification_text.pack(fill=tk.BOTH, expand=True)

        def submit_data():
            justification_window.result = shared_data.copy()
            for field, entry in task_entries.items():
                try:
                    justification_window.result[field] = entry.get()
                except ValueError:
                    messagebox.showerror("Error", f"Invalid input for {field}")
                    return
            justification_window.result['Rank'] = rank_var.get()
            justification_window.result['Justification'] = justification_text.get("1.0", tk.END).strip()
            justification_window.destroy()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        ttk.Button(button_frame, text="Submit", command=submit_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=lambda: self.on_justification_close(justification_window)).pack(side=tk.LEFT, padx=5)

        # Center the window on the screen
        justification_window.update_idletasks()
        width = justification_window.winfo_width()
        height = justification_window.winfo_height()
        x = (justification_window.winfo_screenwidth() // 2) - (width // 2)
        y = (justification_window.winfo_screenheight() // 2) - (height // 2)
        justification_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        justification_window.focus_set()
        return justification_window
    
    def on_justification_close(self, window):
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel? This will end the current shift logging process."):
            window.result = None  # Set result to None to indicate cancellation
            window.destroy()
        # If 'No' is selected, do nothing and keep the window open

    def ask_attempt_another(self, shared_data):
        response = messagebox.askyesno(
            "Attempt Another Task", "Would you like to attempt another task?"
        )
        if response:
            self.attempt_task(shared_data)
        else:
            self.finish_logging()

    def attempt_task(self, shared_data):
        # Start the timer if it's not already running
        if self.timer_window is None or not tk.Toplevel.winfo_exists(self.timer_window.root):
            timer_window = tk.Toplevel(self.root)
            self.timer_window = TimerWindow(timer_window, time_color=self.time_color, bg_color=self.bg_color)
            self.timer_window.start()
            topmost_state = self.config.getboolean("Theme", "timer_topmost", fallback=False)
            self.timer_window.root.attributes("-topmost", topmost_state)
            self.disable_theme_menu()
            self.enable_topmost_menu()

        # Create justification window
        justification_window = self.create_justification_window(shared_data)
        self.root.wait_window(justification_window)

        # Check the result after the justification window is closed
        if hasattr(justification_window, 'result') and justification_window.result is not None:
            self.collected_data.append(justification_window.result)
            self.ask_attempt_another(shared_data)
        else:
            self.finish_logging(cancel=True)

    def finish_logging(self, cancel=False):
        if cancel or not self.collected_data:
            if self.timer_window and tk.Toplevel.winfo_exists(self.timer_window.root):
                self.timer_window.reset()
                self.timer_window.on_close()
                self.timer_window = None
                self.enable_theme_menu()
                self.disable_topmost_menu()
            if cancel:
                messagebox.showinfo("Cancelled", "Autologger process cancelled.")
        else:
            self.log_shift()

    def log_shift(self):
        if self.timer_window and tk.Toplevel.winfo_exists(self.timer_window.root):
            self.timer_window.stop()
            elapsed_time = self.timer_window.elapsed_time

            seconds_in_a_minute = 60
            whole_minutes = elapsed_time.total_seconds() // seconds_in_a_minute
            duration_hrs = whole_minutes / 60

            gross_pay = duration_hrs * self.collected_data[0]["Hourly Rate of Pay"]

            new_id = max([int(x) for x in self.data["data"].keys()], default=0) + 1
            formatted_id = self.format_id(new_id)

            if not LOGS_DIR.exists():
                LOGS_DIR.mkdir(parents=True, exist_ok=True)

            log_file_path = LOGS_DIR / f"{formatted_id}.md"
            with open(log_file_path, "w") as file:
                file.write(f"# `{formatted_id}.md`\n\n----\n\n\n")
                for i, task in enumerate(self.collected_data, start=1):
                    file.write(
                        f"{i}. `{task['Platform ID']}`\n\n"
                    )  # Use Platform ID as identifier
                    file.write("[Permalink]\n")
                    file.write(f"{task['Permalink']}\n\n")
                    file.write("[Response IDs]\n")
                    file.write(f"1. `{task['Response #1 ID']}`\n")
                    file.write(f"2. `{task['Response #2 ID']}`\n\n")
                    file.write("[Rank]\n")
                    file.write(f"{task['Rank']}\n\n")
                    file.write("[Justification]\n")
                    file.write(f"{task['Justification']}\n\n")
                    if i < len(self.collected_data):
                        file.write("\n")

            lock = threading.Lock()

            with lock:
                self.data["data"][formatted_id] = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Model ID": self.collected_data[0]["Model ID"],
                    "Project ID": self.collected_data[0]["Project ID"],
                    "In (hh:mm)": (datetime.now() - elapsed_time).strftime("%H:%M"),
                    "Out (hh:mm)": datetime.now().strftime("%H:%M"),
                    "Duration (hrs)": f"{duration_hrs:.2f}",
                    "Hourly rate": f"{self.collected_data[0]['Hourly Rate of Pay']:.2f}",
                    "Gross pay": f"{gross_pay:.2f}",
                    "Tasks completed": len(self.collected_data),
                }
                self.save_data()
                self.root.after(0, self.populate_tree)  # Schedule GUI refresh

            messagebox.showinfo(
                "Success",
                f"Shift logged successfully. {len(self.collected_data)} tasks completed.",
            )
            logger.info(
                f"Shift logged successfully. {len(self.collected_data)} tasks completed."
            )
        else:
            messagebox.showerror("Error", "Timer is not running.")
            logger.error("Failed to log shift: Timer is not running.")

        if self.timer_window and tk.Toplevel.winfo_exists(self.timer_window.root):
            self.timer_window.reset()
            self.timer_window.on_close()
            self.timer_window = None
            self.enable_theme_menu()
            self.disable_topmost_menu()

    def format_id(self, id):
        return f"{id:04d}"

    def change_theme(self, theme_name):
        self.style.theme_use(theme_name)
        self.config.set("Theme", "selected", theme_name)
        with open(CONFIG_FILE, "w") as config_file:
            self.config.write(config_file)
        logger.debug(f"Theme selection <{theme_name}> saved to `config.ini`.")

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
        self.setup_settings_menu()
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
    logger.info("Application started.")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
