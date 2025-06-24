import os
import json
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta

class DataUsageMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Data Usage Monitor")
        
        # Remove window decorations and taskbar icon
        self.root.overrideredirect(True)  # Removes title bar and borders
        self.root.attributes('-topmost', True)  # Keeps window always on top
        self.root.wm_attributes("-toolwindow", 1)  # Removes from taskbar
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.window_width = 400
        self.window_height = 500

        
        # Calculate positions
        self.hidden_x = self.screen_width - 10  # Only 10px visible
        self.shown_x = self.screen_width - self.window_width
        position_top = int(self.screen_height / 2 - self.window_height / 2)

        self.snap_edge = "right"  # Possible values: "left", "right", "top", "bottom"
        self.last_snap_position = (self.shown_x, position_top)
        
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview",
            background="#1e1e1e",
            foreground="white",
            rowheight=25,
            fieldbackground="#1e1e1e",
            font=("Segoe UI", 10)
        )
        style.map("Treeview", background=[("selected", "#264F78")])

        style.configure("Treeview.Heading",
            background="#3c3c3c",
            foreground="white",
            font=("Segoe UI", 10, "bold")
        )

        style.configure("Header.TLabel", background="#252526", foreground="white")

        style.configure("Dark.TFrame", background="#252526")

        
        # Start in hidden state
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.hidden_x}+{position_top}")
        
        # Make window draggable
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.end_drag)
        
        # Auto-hide functionality
        self.root.bind("<Enter>", self.on_enter)  # Mouse enters window
        self.root.bind("<Leave>", self.on_leave)  # Mouse leaves window
        self.is_shown = False  # Track window state
        
        # Animation control
        self.animation_id = None
        self.animating = False

        # Path to store persistent data
        self.data_file = os.path.join(os.path.expanduser("~"), ".data_usage_monitor.json")

        # Load or initialize data
        self._load_persistent_data()

        # Initialize baseline network counters for this session
        counters = psutil.net_io_counters()
        self.baseline_bytes = counters.bytes_sent + counters.bytes_recv

        # UI Elements
        self._create_widgets()

        # Start periodic update (every second)
        self._schedule_update()
        self._check_internet_connection()

    def start_drag(self, event):
        """Record starting position for drag operation"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True
        # Show window when starting to drag
        if not self.is_shown:
            self.show_window()
            
    def on_drag(self, event):
        """Handle window dragging"""
        if self.drag_data["dragging"]:
            x = self.root.winfo_x() + (event.x - self.drag_data["x"])
            y = self.root.winfo_y() + (event.y - self.drag_data["y"])
            
            # Keep window within screen bounds
            x = max(0, min(x, self.screen_width - 50))
            y = max(0, min(y, self.screen_height - 50))
            
            self.root.geometry(f"+{x}+{y}")
            
            # Update hidden positions based on new location
            self.hidden_x = self.screen_width - 10
            self.shown_x = self.screen_width - self.window_width

    def end_drag(self, event):
        """End drag operation and snap to nearest edge"""
        self.drag_data["dragging"] = False

        x = self.root.winfo_x()
        y = self.root.winfo_y()

        # Distance from each screen edge
        distances = {
            "left": x,
            "right": self.screen_width - (x + self.window_width),
            "top": y,
            "bottom": self.screen_height - (y + self.window_height),
        }

        # Find closest edge
        self.snap_edge = min(distances, key=distances.get)

        # Snap to that edge
        if self.snap_edge == "left":
            x = 0
            self.hidden_pos = (-self.window_width + 10, y)
        elif self.snap_edge == "right":
            x = self.screen_width - self.window_width
            self.hidden_pos = (self.screen_width - 10, y)
        elif self.snap_edge == "top":
            y = 0
            self.hidden_pos = (x, -self.window_height + 10)
        elif self.snap_edge == "bottom":
            y = self.screen_height - self.window_height
            self.hidden_pos = (x, self.screen_height - 10)

        self.last_snap_position = (x, y)
        self.root.geometry(f"+{x}+{y}")

    def on_enter(self, event=None):
        """Mouse enters window - show it"""
        if not self.is_shown and not self.animating:
            self.show_window()

    def on_leave(self, event=None):
        """Mouse leaves window - hide it"""
        # Only hide if mouse leaves and we're not dragging
        if self.is_shown and not self.drag_data["dragging"] and not self.animating:
            # Get mouse position relative to screen
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            
            # Get window position and dimensions
            win_x = self.root.winfo_x()
            win_y = self.root.winfo_y()
            win_w = self.root.winfo_width()
            win_h = self.root.winfo_height()
            
            # Only hide if mouse is actually outside the window
            if not (win_x <= mouse_x <= win_x + win_w and win_y <= mouse_y <= win_y + win_h):
                self.hide_window()

    def show_window(self):
        if self.animating or self.is_shown:
            return

        self.animating = True
        self.is_shown = True
        x, y = self.root.winfo_x(), self.root.winfo_y()
        to_x, to_y = self.last_snap_position

        self.animate_step(x, y, to_x, to_y, action="show")

    def hide_window(self):
        if self.animating or not self.is_shown:
            return

        self.animating = True
        self.is_shown = False
        x, y = self.root.winfo_x(), self.root.winfo_y()

        self.animate_step(x, y, *self.hidden_pos, action="hide")

    def animate_step(self, start_x, start_y, end_x, end_y, action, step=0):
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

        total_steps = 15
        progress = min(1.0, step / total_steps)
        eased = 1 - (1 - progress) ** 2

        new_x = int(start_x + (end_x - start_x) * eased)
        new_y = int(start_y + (end_y - start_y) * eased)

        self.root.geometry(f"+{new_x}+{new_y}")

        if step < total_steps:
            self.animation_id = self.root.after(15, lambda: self.animate_step(start_x, start_y, end_x, end_y, action, step + 1))
        else:
            self.animating = False
            self.animation_id = None
            self._update_edge_indicator_position()

    def _create_widgets(self):
        self.root.configure(bg="#1e1e1e")  # Dark background

        upper_frame = tk.Frame(self.root, bg="#1e1e1e")
        upper_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

        lower_frame = tk.Frame(self.root, bg="#252526")
        lower_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=1)

        self.close_btn = tk.Button(
            upper_frame, text="✕", width=3, command=self.root.destroy,
            bg="#ff5f56", fg="white", font=("Segoe UI", 10, "bold"),
            activebackground="#ffbd2e", activeforeground="black", border=0,
            relief="flat", cursor="hand2"
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5)

        main_frame = ttk.Frame(lower_frame, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.today_label = ttk.Label(
            main_frame, text="", font=("Segoe UI", 13, "bold"),
            anchor="center", justify="center", style="Header.TLabel"
        )
        self.today_label.pack(pady=(0, 10), fill=tk.X)

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        history_label = ttk.Label(
            main_frame, text="Last 30 Days Usage",
            font=("Segoe UI", 10, "bold"), foreground="white", background="#252526"
        )
        history_label.pack(pady=(5, 5))

        frame = ttk.Frame(main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ("date", "usage")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings", selectmode="browse", style="Custom.Treeview"
        )
        self.tree.heading("date", text="Date", anchor=tk.CENTER)
        self.tree.column("date", width=120, anchor=tk.CENTER)
        self.tree.heading("usage", text="Usage", anchor=tk.CENTER)
        self.tree.column("usage", width=120, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.edge_indicator = ttk.Label(
            self.root, text="≡", font=("Segoe UI", 15),
            background="#605b5b", foreground="#cccccc", anchor=tk.CENTER
        )
        self.edge_indicator.place(relx=0, rely=0.5, anchor=tk.W, width=15, height=80)

        self.status_label = ttk.Label(
            self.root,
            text="Checking connection...",
            font=("Segoe UI", 12, "bold"),
            anchor="center",
            background="#1e1e1e", 
            foreground="white"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 5))

        self._refresh_history_view()

    def _check_internet_connection(self):
        import socket

        def is_connected():
            try:
                # Connect to Google's DNS to test internet (does not send data)
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                return True
            except OSError:
                return False

        # Update label based on connection
        if is_connected():
            self.status_label.config(text="Internet Connected", foreground="lightgreen")
        else:
            self.status_label.config(text="Internet Disconnected", foreground="red")

        # Re-check every 5 seconds
        self.root.after(5000, self._check_internet_connection)

    def _update_edge_indicator_position(self):
        # Remove existing placement
        self.edge_indicator.place_forget()
        
        if self.snap_edge == "left":
            self.edge_indicator.place(relx=1.0, rely=0.5, anchor=tk.E, width=15, height=80)
        elif self.snap_edge == "right":
            self.edge_indicator.place(relx=0.0, rely=0.5, anchor=tk.W, width=15, height=80)
        elif self.snap_edge == "top":
            self.edge_indicator.place(relx=0.5, rely=1.0, anchor=tk.S, width=80, height=15)
        elif self.snap_edge == "bottom":
            self.edge_indicator.place(relx=0.5, rely=0.0, anchor=tk.N, width=80, height=15)
            
    def _load_persistent_data(self):
        today_str = date.today().isoformat()
        # Default structure
        default = {
            "history": {},  # map date string "YYYY-MM-DD" to integer bytes used
            "current_date": today_str,
            "current_usage": 0  # bytes used so far today
        }
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                # Validate structure
                if ("history" in data and isinstance(data["history"], dict)
                        and "current_date" in data and "current_usage" in data):
                    stored_date_str = data["current_date"]
                    try:
                        stored_date = datetime.strptime(stored_date_str, "%Y-%m-%d").date()
                    except Exception:
                        stored_date = date.today()
                        data = default
                    # If stored_date < today, fill missing days with 0 usage
                    today = date.today()
                    if stored_date < today:
                        # For each day between stored_date+1 and yesterday, set 0 usage if missing
                        d = stored_date
                        while True:
                            d = d + timedelta(days=1)
                            if d >= today:
                                break
                            ds = d.isoformat()
                            if ds not in data["history"]:
                                data["history"][ds] = 0
                        # For today, reset usage
                        data["current_date"] = today.isoformat()
                        data["current_usage"] = 0
                        data["history"][today.isoformat()] = 0
                    else:
                        # stored_date == today: ensure entry exists
                        if stored_date_str not in data["history"]:
                            data["history"][stored_date_str] = data.get("current_usage", 0)
                        # Load current_usage
                        data["current_usage"] = data["history"].get(stored_date_str, 0)
                    # Trim history to last 30 days
                    self._trim_history(data["history"])
                    self.data = data
                else:
                    self.data = default
            except Exception:
                # If file corrupted
                self.data = default
        else:
            # Initialize new
            default["history"][today_str] = 0
            self.data = default
            self._save_persistent_data()

    def _trim_history(self, history_dict):
        # Keep only last 30 days from today
        today = date.today()
        allowed = set((today - timedelta(days=i)).isoformat() for i in range(0, 30))
        to_delete = [d for d in history_dict if d not in allowed]
        for d in to_delete:
            del history_dict[d]

    def _save_persistent_data(self):
        tmp_file = self.data_file + ".tmp"
        try:
            with open(tmp_file, "w") as f:
                json.dump(self.data, f)
            os.replace(tmp_file, self.data_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def _refresh_history_view(self):
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Sort dates descending (most recent first)
        dates = sorted(self.data["history"].keys(), reverse=True)
        for d in dates:
            usage_bytes = self.data["history"][d]
            usage_str = self._format_bytes(usage_bytes)
            self.tree.insert("", tk.END, values=(d, usage_str))

    def _format_bytes(self, num_bytes):
        # Human-readable format
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} PB"

    def _schedule_update(self):
        # Schedule the update method to run after 1000 ms
        self.update_id = self.root.after(1000, self._update_usage)

    def _update_usage(self):
        # Check if date changed
        today = date.today()
        stored_date = datetime.strptime(self.data["current_date"], "%Y-%m-%d").date()
        if today > stored_date:
            # Day rolled over. Fill missing days if more than one day passed.
            d = stored_date
            while True:
                d = d + timedelta(days=1)
                # For each day up to yesterday, set 0 if missing
                if d < today:
                    ds = d.isoformat()
                    if ds not in self.data["history"]:
                        self.data["history"][ds] = 0
                else:
                    break
            # Reset for today
            today_str = today.isoformat()
            self.data["current_date"] = today_str
            self.data["current_usage"] = 0
            self.data["history"][today_str] = 0
            # Trim history
            self._trim_history(self.data["history"])
            # Refresh history view
            self._refresh_history_view()
            # Reset baseline counters at new day start
            counters = psutil.net_io_counters()
            self.baseline_bytes = counters.bytes_sent + counters.bytes_recv

        # Get current counters
        counters = psutil.net_io_counters()
        total_bytes = counters.bytes_sent + counters.bytes_recv
        delta = total_bytes - self.baseline_bytes
        if delta < 0:
            # This may happen if counters reset (e.g., network card reset). Reset baseline.
            delta = 0
        # Update baseline for next interval
        self.baseline_bytes = total_bytes

        # Add to current usage
        if delta > 0:
            self.data["current_usage"] += delta
            # Update history entry
            today_str = self.data["current_date"]
            self.data["history"][today_str] = self.data["current_usage"]
            # Update UI label
            self.today_label.config(text=f"Today's Usage: {self._format_bytes(self.data['current_usage'])}")
            # Update treeview for today's row
            for item in self.tree.get_children():
                vals = self.tree.item(item, "values")
                if vals and vals[0] == today_str:
                    self.tree.item(item, values=(today_str, self._format_bytes(self.data["current_usage"])))
                    break
            else:
                # If not found, insert at top
                self.tree.insert("", 0, values=(today_str, self._format_bytes(self.data["current_usage"])))
        else:
            # Even if no change, update the label text at least on first run
            self.today_label.config(text=f"Today's Usage: {self._format_bytes(self.data['current_usage'])}")

        # Persist data
        self._save_persistent_data()

        # Schedule next update
        self._schedule_update()

def main():
    # Check for psutil
    try:
        import psutil  # already imported above, just check
    except ImportError:
        message = (
            "The psutil module is required. Please install it via:\n\n"
            "    pip install psutil\n\n"
            "Then run this script again."
        )
        messagebox.showerror("Missing Dependency", message)
        return

    root = tk.Tk()
    app = DataUsageMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
