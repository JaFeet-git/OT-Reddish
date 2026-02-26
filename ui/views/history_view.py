import customtkinter as ctk
from database import get_all_logs, delete_log

class HistoryView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Scan History", 
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(40, 20))
        
        # Log List Area (Scrollable)
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        self.selected_log = None
        self.log_buttons = []
        
        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, padx=40, pady=20, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.view_btn = ctk.CTkButton(
            self.action_frame, 
            text="View Detail",
            font=ctk.CTkFont(size=20),
            height=40,
            command=self._view_detail,
            state="disabled"
        )
        self.view_btn.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.delete_btn = ctk.CTkButton(
            self.action_frame, 
            text="Delete Log",
            font=ctk.CTkFont(size=20),
            fg_color="#F44336",
            hover_color="#d32f2f",
            height=40,
            command=self._delete_selected_log,
            state="disabled"
        )
        self.delete_btn.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Load data
        self.load_logs()

    def load_logs(self):
        # Clear existing
        for btn in self.log_buttons:
            btn.destroy()
        self.log_buttons.clear()
        self.selected_log = None
        self.view_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        
        # Fetch from DB
        logs = get_all_logs()
        
        if not logs:
            lbl = ctk.CTkLabel(self.list_frame, text="No scan history found.", font=ctk.CTkFont(size=18, slant="italic"))
            lbl.grid(row=0, column=0, padx=20, pady=20)
            self.log_buttons.append(lbl)
            return

        for i, log in enumerate(logs):
            display_text = f"{log['timestamp']}  |  {log['scan_type']} ({log['target_ip']})"
            btn = ctk.CTkButton(
                self.list_frame, 
                text=display_text,
                font=ctk.CTkFont(size=16),
                fg_color=("gray75", "gray30"),
                text_color=("black", "white"),
                hover_color=("gray60", "gray40"),
                anchor="w",
                height=40,
                command=lambda l=log: self._select_log(l)
            )
            btn.grid(row=i, column=0, padx=20, pady=(15 if i==0 else 5), sticky="ew")
            self.log_buttons.append(btn)

    def _select_log(self, log):
        self.selected_log = log
        # Highlight logic could be added here
        self.view_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")

    def _view_detail(self):
        if not self.selected_log: return
        
        # Create a popup window to show results
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Scan Detail: {self.selected_log['target_ip']}")
        detail_window.geometry("600x400")
        detail_window.attributes('-topmost', True) # Keep on top
        
        textbox = ctk.CTkTextbox(detail_window, font=ctk.CTkFont(family="Courier", size=14))
        textbox.pack(fill="both", expand=True, padx=20, pady=20)
        textbox.insert("0.0", f"Scan Profile: {self.selected_log['scan_type']}\n")
        textbox.insert("end", f"Time: {self.selected_log['timestamp']}\n")
        textbox.insert("end", "======================================\n\n")
        textbox.insert("end", self.selected_log['results'])
        textbox.configure(state="disabled") # readonly

    def _delete_selected_log(self):
        if not self.selected_log: return
        delete_log(self.selected_log['id'])
        self.load_logs()
