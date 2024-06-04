import datetime
import json
import os

# Set the environment variable to ignore Dark Mode
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['NSRequiresAquaSystemAppearance'] = '1'

import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog, Text, Button, colorchooser

"""
Shyft (v0.1.0)
> a shift-logging application designed to help contractors track and manage their service records
"""

# ENVIRONMENT

def ensure_directory(path):
    if path.exists():
        if not path.is_dir():
            raise NotADirectoryError(f"'{path}' exists and is not a directory.")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")


# Get the user's home directory
HOME = Path.home()

# Define the path to the 'app_data' directory
APP_DATA_DIR = HOME / 'app_data'

# Ensure the 'app_data' directory exists
ensure_directory(APP_DATA_DIR)

# Define the path to the 'Shyft' directory inside 'app_data'
SHYFT_DATA_DIR = APP_DATA_DIR / 'Shyft'

# Ensure the 'Shyft' directory exists
ensure_directory(SHYFT_DATA_DIR)

# Define the path to the 'logs' directory inside 'Shyft'
LOGS_DIR = SHYFT_DATA_DIR / 'logs'

# Ensure the 'logs' directory exists
ensure_directory(LOGS_DIR)

DEFAULT_SHIFT_STRUCTURE = {
    "Date": "",
    "Project ID": "",
    "Model ID": "",
    "In (hh:mm)": "",
    "Out (hh:mm)": "",
    "Duration (hrs)": "",
    "Hourly rate": "",
    "Gross pay": "",
}

class TimerWindow:
    def __init__(self, master, time_color="#A78C7B", bg_color="#FFBE98"):
        self.master = master
        self.master.title("Timer")
        self.master.geometry("140x70")  # Set the desired size of the timer window
        self.master.configure(bg=bg_color)  # Set background color of the master frame
        self.master.attributes('-topmost', True)
        self.elapsed_time = timedelta(0)
        self.running = False
        self.last_time = None

        self.time_color = time_color
        self.bg_color = bg_color

        # Timer display label with monospaced Helvetica font
        self.timer_label = tk.Label(
            self.master, 
            text="00:00:00", 
            font=("Helvetica Neue", 32, "bold"),  # Adjust font to use monospaced variant
            fg=self.time_color, 
            bg=self.bg_color
        )
        self.timer_label.pack(padx=5, pady=0)

        # Control buttons directly inside the master frame
        button_frame = tk.Frame(self.master, bg=self.bg_color)
        button_frame.pack(fill="x", pady=0)

        button_font = ("Helvetica", 10)

        self.start_button = tk.Button(button_frame, text="Start", command=self.start, bg=self.bg_color, fg="#A78C7B", highlightbackground=self.bg_color, highlightthickness=0, bd=0, font=button_font)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=2)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop, bg=self.bg_color, fg="#A78C7B", highlightbackground=self.bg_color, highlightthickness=0, bd=0, font=button_font)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.reset_button = tk.Button(button_frame, text="Reset", command=self.reset, bg=self.bg_color, fg="#A78C7B", highlightbackground=self.bg_color, highlightthickness=0, bd=0, font=button_font)
        self.reset_button.grid(row=0, column=2, sticky="ew", padx=2)

        # Configure grid to make buttons expand evenly
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        # Update the timer every 100ms
        self.update_timer()

    def start(self):
        if not self.running:
            self.running = True
            self.last_time = datetime.now()

    def stop(self):
        if self.running:
            self.running = False
            self.elapsed_time += datetime.now() - self.last_time

    def reset(self):
        self.stop()
        self.elapsed_time = timedelta(0)
        self.timer_label.config(text="00:00:00")

    def update_timer(self):
        if self.running:
            current_time = datetime.now()
            delta = current_time - self.last_time
            elapsed = self.elapsed_time + delta
            self.timer_label.config(text=str(elapsed).split('.')[0].rjust(8, "0"))
        self.master.after(100, self.update_timer)


class ShyftGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Shyft")
        self.time_color = "#A78C7B"
        self.bg_color = "#FFBE98"
        self.btn_text_color = "#A78C7B"
        self.master.configure(bg=self.bg_color)
        self.configure_styles()
        self.data_file_path = SHYFT_DATA_DIR / "data.json"
        self.data = {}
        self.load_data()
        self.create_widgets()
        self.refresh_view()
        self.timer_window = None
        self.master.resizable(True, False)

    def configure_styles(self):
        self.style = ttk.Style(self.master)
        self.update_styles()

    def update_styles(self):
        # Always use light mode colors
        self.style.configure(
            "TButton",
            foreground="#FFA74F",
            background="#F2E8DA",
            font=("Helvetica", 12),
        )
        self.style.configure(
            "TLabel",
            # foreground="black",
            # background="white",
            font=("Helvetica", 12, "bold"),
        )
        self.style.configure(
            "TEntry", 
            foreground="black", 
            background="white", 
            font=("Helvetica", 12)
        )
        self.style.configure(
            "Treeview", 
            background="white", 
            fieldbackground="white", 
            foreground="black"
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Helvetica", 10, "bold"),
            foreground="black",
            background="gray",
        )
        self.style.map(
            "Treeview",
            background=[('selected', '#FFBE98')],
            foreground=[('selected', 'black')]
        )
        self.style.configure(
            "highlight.Treeview", background='#FFBE98', foreground="black"
        )


    def load_data(self):
        try:
            if self.data_file_path.exists():
                with self.data_file_path.open('r') as f:
                    self.data = json.load(f).get("data", {})
                    # Ensure all shifts have the expected keys
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
        try:
            with self.data_file_path.open('w') as f:
                json.dump({"data": self.data}, f, indent=4)
            messagebox.showinfo("Success", "Data updated successfully.")
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    def create_widgets(self):
        self.tree = ttk.Treeview(
            self.master,
            columns=(
                "ID",
                "Date",
                "Project ID",
                "Model ID",
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

        button_frame = ttk.Frame(self.master, style="TFrame")
        button_frame.pack(ipady=5, fill="both", expand=True)

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
        ttk.Button(button_frame, text="Totals", command=self.calculate_totals, style="TButton").pack(
            side="left", expand=True
        )

        # Add settings button_frame
        ttk.Button(button_frame, text="Settings", command=self.open_settings, style="TButton").pack(side="left", expand=True)

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
                    shift.get("Project ID", "N/A"),
                    shift.get("Model ID", "N/A"),
                    shift.get("In (hh:mm)", "N/A"),
                    shift.get("Out (hh:mm)", "N/A"),
                    shift.get("Duration (hrs)", "N/A"),
                    shift.get("Hourly rate", "N/A"),
                    shift.get("Gross pay", "N/A"),
                ),
            )

    def calculate_totals(self):
        number_of_shifts = len(self.data.values())
        total_hours_worked = sum(
            float(shift["Duration (hrs)"]) for shift in self.data.values()
        )
        total_gross_pay = sum(float(shift["Gross pay"]) for shift in self.data.values())
        tax_liability = total_gross_pay * 0.27
        net_income = total_gross_pay - tax_liability

        # Display these totals in a pop-up window or directly on the GUI
        totals_window = tk.Toplevel(self.master)
        totals_window.title("Totals")

        columns = ("Description", "Value")
        totals_tree = ttk.Treeview(totals_window, columns=columns, show="headings")
        totals_tree.heading("Description", text="Description", anchor="w")
        totals_tree.heading("Value", text="Value", anchor="w")
        totals_tree.column("Description", anchor="w", width=200)
        totals_tree.column("Value", anchor="e", width=100)
        totals_tree.pack(expand=True, fill="both")

        totals_tree.insert("", "end", values=("Shifts Worked", number_of_shifts))
        totals_tree.insert("", "end", values=("Total Hours Worked", f"{total_hours_worked:.2f}"))
        totals_tree.insert("", "end", values=("Total Gross Pay", f"${total_gross_pay:.2f}"))
        totals_tree.insert("", "end", values=("Estimated Tax Liability (27%)", f"${tax_liability:.2f}"))
        totals_tree.insert("", "end", values=("Estimated Net Income", f"${net_income:.2f}"))

    def view_logs(self):
        os.chdir(LOGS_DIR)
        log_window = tk.Toplevel(self.master)
        log_window.title("View Logs")
        log_window.geometry("480x640")
    
        # Create a frame for the TreeView
        tree_frame = ttk.Frame(log_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # Set up the TreeView
        log_tree = ttk.Treeview(tree_frame, columns=["Log Files"], show="headings", style="Treeview")
        log_tree.heading("Log Files", text="Log Files")
        log_tree.column("Log Files", anchor="w", width=100)
        log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Configure tag for selected items
        log_tree.tag_configure('highlight', background='#FFBE98')
    
        # Populate the TreeView with log files, excluding hidden files
        log_files = sorted(
            [f for f in LOGS_DIR.iterdir() if f.is_file() and not f.name.startswith('.')],
            key=lambda x: x.name
        )
        for log_file in log_files:
            log_tree.insert("", "end", iid=log_file.name, values=[log_file.name])
    
        # Create a frame for the Text widget to display the log content
        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget = Text(text_frame, wrap="word")
        text_widget.pack(fill=tk.BOTH, expand=True)
    
        def on_log_selection(event):
            # Remove highlight from all items
            for item in log_tree.get_children():
                log_tree.item(item, tags=())
    
            # Highlight selected item
            selected_item = log_tree.selection()
            if selected_item:
                log_tree.item(selected_item, tags=('highlight',))
    
                log_file_path = os.path.join(LOGS_DIR, selected_item[0])
                with open(log_file_path, "r") as file:
                    content = file.read()
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
    
        log_tree.bind("<<TreeviewSelect>>", on_log_selection)
    
    def manual_entry(self):
        window = tk.Toplevel(self.master)
        window.title("Manual Shift Entry")
        entries = {}
        fields = [
            "Date",
            "Project ID",
            "Model ID",
            "In (hh:mm)",
            "Out (hh:mm)",
            "Hourly rate",
        ]
        uppercase_fields = ["Project ID", "Model ID"]  # Fields to convert to uppercase

        for field in fields:
            row = ttk.Frame(window, style="TFrame")
            label = ttk.Label(row, width=15, text=field, anchor="w", style="TLabel")
            entry_var = tk.StringVar()
            entry = ttk.Entry(row, textvariable=entry_var, style="TEntry")
            if field in uppercase_fields:
                entry_var.trace_add(
                    "write", lambda *args, var=entry_var: var.set(var.get().upper())
                )
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries[field] = entry

        # Button Frame
        button_frame = ttk.Frame(window, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=window.destroy, style="TButton")
        cancel_button.pack(side=tk.LEFT, padx=5)

        submit_button = ttk.Button(
            button_frame, text="Submit", command=lambda: submit_action(), style="TButton"
        )
        submit_button.pack(side=tk.RIGHT, padx=5)

        def submit_action():
            try:
                # Validate time format for StartTime and EndTime
                validate_time_format(entries["In (hh:mm)"].get())
                validate_time_format(entries["Out (hh:mm)"].get())

                new_data = {field: entries[field].get() for field in fields}
                if any(v == "" for v in new_data.values()):
                    messagebox.showerror("Error", "All fields must be filled out.")
                    return

                # Generate a new ID and format it
                new_id = max([int(x) for x in self.data.keys()], default=0) + 1
                formatted_id = self.format_id(new_id)  # Format the new ID

                # Calculate duration based on 'StartTime' and 'EndTime'
                duration_hrs = calculate_duration(
                    new_data["In (hh:mm)"], new_data["Out (hh:mm)"]
                )
                new_data["Duration (hrs)"] = "{:.2f}".format(duration_hrs)
                gross_pay = float(new_data["Hourly rate"]) * duration_hrs
                new_data["Gross pay"] = "{:.2f}".format(gross_pay)

                self.data[formatted_id] = new_data
                self.save_data()
                self.populate_tree()
                window.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        def calculate_duration(start, end):
            """Calculate the duration in hours between two HH:MM formatted times."""
            try:
                start_dt = datetime.strptime(start, "%H:%M")
                end_dt = datetime.strptime(end, "%H:%M")
                # Handle scenario where end time is past midnight
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                duration = (end_dt - start_dt).total_seconds() / 3600.0
                return duration
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM format.")

        def validate_time_format(time_str):
            """Check if the time string is in HH:MM format."""
            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM format.")

    def edit_shift(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a shift to edit.")
            return
        selected_id = selected_item[0]
        shift = self.data.get(selected_id)

        window = tk.Toplevel(self.master)
        window.title("Edit Shift")
        entries = {}
        fields = [
            "Date",
            "Project ID",
            "Model ID",
            "In (hh:mm)",
            "Out (hh:mm)",
            "Duration (hrs)",
            "Hourly rate",
            "Gross pay",
        ]
        uppercase_fields = ["Project ID", "Model ID"]  # Fields to convert to uppercase

        # First, create all entries without the uppercase transformation
        for field in fields:
            row = ttk.Frame(window, style="TFrame")
            label = ttk.Label(row, width=15, text=field, anchor="w", style="TLabel")
            entry_var = tk.StringVar(value=shift.get(field, ""))
            entry = ttk.Entry(row, textvariable=entry_var, style="TEntry")
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries[field] = entry_var  # Store the StringVar, not the Entry widget

        # Apply uppercase transformation where necessary
        for field in uppercase_fields:
            entry_var = entries[field]
            entry_var.trace_add(
                "write", lambda *args, var=entry_var: var.set(var.get().upper())
            )

        # Button Frame
        button_frame = ttk.Frame(window, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=window.destroy, style="TButton")
        cancel_button.pack(side=tk.LEFT, padx=5)

        submit_button = ttk.Button(
            button_frame, text="Submit", command=lambda: submit_action(), style="TButton"
        )
        submit_button.pack(side=tk.RIGHT, padx=5)

        def submit_action():
            try:
                updated_data = {field: entries[field].get() for field in fields}
                if any(v == "" for v in updated_data.values()):
                    messagebox.showerror("Error", "All fields must be filled out.")
                    return

                self.data[selected_id] = updated_data
                self.save_data()
                self.populate_tree()
                window.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Error", "Failed to update shift. Error: " + str(e)
                )

    def delete_shift(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a shift to delete.")
            return
        selected_id = selected_item[0]
        response = messagebox.askyesno(
            "Confirm Delete", "Are you sure you want to delete this shift?"
        )
        if response:
            del self.data[selected_id]
            self.save_data()
            self.populate_tree()

    def open_settings(self):
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("140x160")  # Set an appropriate size for the settings window

        def choose_color(variable, button):
            color_code = colorchooser.askcolor(title="Choose Color")[1]
            if color_code:
                variable.set(color_code)
                button.configure(background=color_code)

        time_color_var = tk.StringVar(value=self.time_color)
        bg_color_var = tk.StringVar(value=self.bg_color)
        btn_text_color_var = tk.StringVar(value=self.btn_text_color)

        settings_frame = ttk.Frame(settings_window, style="TFrame")
        settings_frame.pack(padx=5, pady=1, ipadx=1, ipady=1, expand=tk.YES, fill=tk.X)

        # ttk.Label(settings_frame, text="Timestring Color", style="TLabel").pack(anchor="w")
        time_color_button = ttk.Button(settings_frame, text="Timestring Color", command=lambda: choose_color(time_color_var, time_color_button), style="TButton")
        time_color_button.pack(fill="x", pady=1)

        # ttk.Label(settings_frame, text="Timer Background Color", style="TLabel").pack(anchor="w")
        bg_color_button = ttk.Button(settings_frame, text="Background Color", command=lambda: choose_color(bg_color_var, bg_color_button), style="TButton")
        bg_color_button.pack(fill="x", pady=1)

        # ttk.Label(settings_frame, text="Timer Button Text Color", style="TLabel").pack(anchor="w")
        btn_text_color_button = ttk.Button(settings_frame, text="Button Text Color", command=lambda: choose_color(btn_text_color_var, btn_text_color_button), style="TButton")
        btn_text_color_button.pack(fill="x", pady=1)


        def save_settings():
            self.time_color = time_color_var.get()
            self.bg_color = bg_color_var.get()
            self.btn_text_color = btn_text_color_var.get()
            self.update_styles()
            settings_window.destroy()
            messagebox.showinfo("Settings Saved", "New settings have been applied.")

        ttk.Separator(orient="horizontal").pack(pady=1, fill="x")
        ttk.Button(settings_frame, text="Save", command=save_settings, style="TButton").pack(pady=1, fill="x")
        ttk.Button(settings_frame, text="Cancel", command=lambda: settings_window.destroy(), style="TButton").pack(pady=1, fill="x")

    def autologger(self):
        model_id_response = simpledialog.askstring("Model ID", "Enter Model ID", parent=self.master)
        if not model_id_response:
            return  # Exit if the dialog is cancelled or the input is empty
        model_id = model_id_response.upper()

        project_id_response = simpledialog.askstring("Project ID", "Enter Project ID", parent=self.master)
        if not project_id_response:
            return  # Exit if no Project ID is provided
        project_id = project_id_response.upper()

        hourly_rate = simpledialog.askstring("Hourly rate", "Enter Hourly Rate", parent=self.master)
        try:
            hourly_rate = float(hourly_rate)  # Validate that hourly rate is a number
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Invalid hourly rate; please enter a numeric value.")
            return

        # Creating the Notes window with an explicitly short height
        notes_window = tk.Toplevel(self.master)
        notes_window.title("Notes - Autologger")
        notes_window.geometry("480x640")  # Set initial size; width x height

        # Text widget for note-taking
        text = Text(notes_window, wrap=tk.WORD, height=1, bg="white", fg="black")  # Set minimal initial height
        text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame to hold the buttons, ensuring they are always visible
        button_frame = tk.Frame(notes_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Define the action for inserting a divider
        def insert_divider():
            divider = "═" * 64 + "\n"
            text.insert(tk.INSERT, divider)

        # Start the timer when the notes window is opened
        if self.timer_window is None or not tk.Toplevel.winfo_exists(self.timer_window.master):
            timer_window = tk.Toplevel(self.master)
            self.timer_window = TimerWindow(timer_window, time_color=self.time_color, bg_color=self.bg_color)
            self.timer_window.start()

        # Define the action for submitting notes
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

                self.data[formatted_id] = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Project ID": project_id,
                    "Model ID": model_id,
                    "In (hh:mm)": (datetime.now() - elapsed_time).strftime("%H:%M"),
                    "Out (hh:mm)": datetime.now().strftime("%H:%M"),
                    "Duration (hrs)": f"{duration_hrs:.2f}",
                    "Hourly rate": f"{hourly_rate:.2f}",
                    "Gross pay": f"{gross_pay:.2f}",
                }

                if not LOGS_DIR.exists():
                    LOGS_DIR.mkdir(parents=True, exist_ok=True)

                log_file_path = LOGS_DIR / f"{formatted_id}.log"
                with open(log_file_path, "w") as file:
                    file.write(text.get("1.0", tk.END))

                self.save_data()
                self.populate_tree()
                notes_window.destroy()

                if self.timer_window:
                    self.timer_window.reset()
                    self.timer_window.master.destroy()
                    self.timer_window = None
            else:
                messagebox.showerror("Error", "Timer is not running.")

        # Buttons for submit, cancel, and insert divider
        Button(button_frame, text="Submit", command=submit_notes, bg=self.btn_text_color, fg="black").pack(side=tk.RIGHT, padx=5, pady=5)
        Button(button_frame, text="Cancel", command=notes_window.destroy, bg=self.btn_text_color, fg="black").pack(side=tk.LEFT, padx=5, pady=5)
        Button(button_frame, text="Insert Divider", command=insert_divider, bg=self.btn_text_color, fg="black").pack(side=tk.LEFT, padx=5, pady=5)

    def format_id(self, id):
        """Format the given ID to have at least 4 digits with leading zeros."""
        return f"{id:04d}"

def main():
    root = tk.Tk()
    app = ShyftGUI(root)
    app.refresh_view()
    root.mainloop()

if __name__ == "__main__":
    main()
