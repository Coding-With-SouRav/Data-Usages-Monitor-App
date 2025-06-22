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
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.wm_attributes("-toolwindow", 1)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.window_width = 400
        self.window_height = 500
        self.hidden_x = self.screen_width - 10
        self.shown_x = self.screen_width - self.window_width
        position_top = int(self.screen_height / 2 - self.window_height / 2)
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
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.hidden_x}+{position_top}")
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.end_drag)
        self.root.bind("<Enter>", self.on_enter)
        self.root.bind("<Leave>", self.on_leave)
        self.is_shown = False
        self.animation_id = None
        self.animating = False
        self.data_file = os.path.join(os.path.expanduser("~"), ".data_usage_monitor.json")
        self._load_persistent_data()
        counters = psutil.net_io_counters()
        self.baseline_bytes = counters.bytes_sent + counters.bytes_recv
        self._create_widgets()
        self._schedule_update()
        self._check_internet_connection()

    def start_drag(self, event):
        """Record starting position for drag operation"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True

        if not self.is_shown:
            self.show_window()

    def on_drag(self, event):
        """Handle window dragging"""

        if self.drag_data["dragging"]:
            x = self.root.winfo_x() + (event.x - self.drag_data["x"])
            y = self.root.winfo_y() + (event.y - self.drag_data["y"])
            x = max(0, min(x, self.screen_width - 50))
            y = max(0, min(y, self.screen_height - 50))
            self.root.geometry(f"+{x}+{y}")
            self.hidden_x = self.screen_width - 10
            self.shown_x = self.screen_width - self.window_width

    def end_drag(self, event):
        """End drag operation"""
        self.drag_data["dragging"] = False

    def on_enter(self, event=None):
        """Mouse enters window - show it"""

        if not self.is_shown and not self.animating:
            self.show_window()

    def on_leave(self, event=None):
        """Mouse leaves window - hide it"""

        if self.is_shown and not self.drag_data["dragging"] and not self.animating:
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            win_x = self.root.winfo_x()
            win_y = self.root.winfo_y()
            win_w = self.root.winfo_width()
            win_h = self.root.winfo_height()

            if not (win_x <= mouse_x <= win_x + win_w and win_y <= mouse_y <= win_y + win_h):
                self.hide_window()

    def show_window(self):
        """Smoothly show the window"""

        if self.animating or self.is_shown:
            return
        self.animating = True
        self.is_shown = True
        current_x = self.root.winfo_x()
        y_pos = self.root.winfo_y()
        self.animate_step(current_x, self.shown_x, y_pos, "show")

    def hide_window(self):
        """Smoothly hide the window"""

        if self.animating or not self.is_shown:
            return
        self.animating = True
        self.is_shown = False
        current_x = self.root.winfo_x()
        y_pos = self.root.winfo_y()
        self.animate_step(current_x, self.hidden_x, y_pos, "hide")

    def animate_step(self, start_x, end_x, y_pos, action, step=0):
        """Animate window sliding with easing function"""

        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        total_steps = 15
        progress = min(1.0, step / total_steps)
        eased_progress = 1 - (1 - progress) ** 2
        distance = end_x - start_x
        new_x = start_x + (distance * eased_progress)
        self.root.geometry(f"+{int(new_x)}+{y_pos}")

        if step < total_steps:
            step += 1
            self.animation_id = self.root.after(15, lambda: self.animate_step(start_x, end_x, y_pos, action, step))
        else:
            self.animating = False
            self.animation_id = None

            if action == "hide":
                position_top = int(self.screen_height / 2 - self.window_height / 2)
                self.root.geometry(f"+{self.hidden_x}+{position_top}")

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
            self.root, text="≡", font=("Segoe UI", 12),
            background="#3c3c3c", foreground="#cccccc", anchor=tk.CENTER
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
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                return True

            except OSError:
                return False

        if is_connected():
            self.status_label.config(text="Internet Connected", foreground="lightgreen")
        else:
            self.status_label.config(text="Internet Disconnected", foreground="red")
        self.root.after(5000, self._check_internet_connection)

    def _load_persistent_data(self):
        today_str = date.today().isoformat()

        default = {
            "history": {},
            "current_date": today_str,
            "current_usage": 0
        }

        if os.path.exists(self.data_file):

            try:

                with open(self.data_file, "r") as f:
                    data = json.load(f)

                if ("history" in data and isinstance(data["history"], dict)
                        and "current_date" in data and "current_usage" in data):
                    stored_date_str = data["current_date"]

                    try:
                        stored_date = datetime.strptime(stored_date_str, "%Y-%m-%d").date()

                    except Exception:
                        stored_date = date.today()
                        data = default
                    today = date.today()

                    if stored_date < today:
                        d = stored_date

                        while True:
                            d = d + timedelta(days=1)

                            if d >= today:
                                break
                            ds = d.isoformat()

                            if ds not in data["history"]:
                                data["history"][ds] = 0
                        data["current_date"] = today.isoformat()
                        data["current_usage"] = 0
                        data["history"][today.isoformat()] = 0
                    else:

                        if stored_date_str not in data["history"]:
                            data["history"][stored_date_str] = data.get("current_usage", 0)
                        data["current_usage"] = data["history"].get(stored_date_str, 0)
                    self._trim_history(data["history"])
                    self.data = data
                else:
                    self.data = default

            except Exception:
                self.data = default
        else:

            default["history"][today_str] = 0
            self.data = default
            self._save_persistent_data()

    def _trim_history(self, history_dict):
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
        for item in self.tree.get_children():
            self.tree.delete(item)
        dates = sorted(self.data["history"].keys(), reverse=True)
        for d in dates:
            usage_bytes = self.data["history"][d]
            usage_str = self._format_bytes(usage_bytes)
            self.tree.insert("", tk.END, values=(d, usage_str))

    def _format_bytes(self, num_bytes):
        for unit in ["B", "KB", "MB", "GB", "TB"]:

            if num_bytes < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} PB"

    def _schedule_update(self):
        self.update_id = self.root.after(1000, self._update_usage)

    def _update_usage(self):
        today = date.today()
        stored_date = datetime.strptime(self.data["current_date"], "%Y-%m-%d").date()

        if today > stored_date:
            d = stored_date

            while True:
                d = d + timedelta(days=1)

                if d < today:
                    ds = d.isoformat()

                    if ds not in self.data["history"]:
                        self.data["history"][ds] = 0
                else:
                    break
            today_str = today.isoformat()
            self.data["current_date"] = today_str
            self.data["current_usage"] = 0
            self.data["history"][today_str] = 0
            self._trim_history(self.data["history"])
            self._refresh_history_view()
            counters = psutil.net_io_counters()
            self.baseline_bytes = counters.bytes_sent + counters.bytes_recv
        counters = psutil.net_io_counters()
        total_bytes = counters.bytes_sent + counters.bytes_recv
        delta = total_bytes - self.baseline_bytes

        if delta < 0:
            delta = 0
        self.baseline_bytes = total_bytes

        if delta > 0:
            self.data["current_usage"] += delta
            today_str = self.data["current_date"]
            self.data["history"][today_str] = self.data["current_usage"]
            self.today_label.config(text=f"Today's Usage: {self._format_bytes(self.data['current_usage'])}")
            for item in self.tree.get_children():
                vals = self.tree.item(item, "values")

                if vals and vals[0] == today_str:
                    self.tree.item(item, values=(today_str, self._format_bytes(self.data["current_usage"])))
                    break
            else:
                self.tree.insert("", 0, values=(today_str, self._format_bytes(self.data["current_usage"])))
        else:
            self.today_label.config(text=f"Today's Usage: {self._format_bytes(self.data['current_usage'])}")
        self._save_persistent_data()
        self._schedule_update()

def main():

    try:
        import psutil

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
