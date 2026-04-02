import customtkinter as ctk

from ui.sidebar import Sidebar
from ui.views.ip_view import IPView
from ui.views.scan_view import ScanView
from ui.views.history_view import HistoryView
from ui.views.settings_view import SettingsView
from ui.views.login_view import LoginView
from database import init_db

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("OT Reddish Scanner")
        # Standard Raspberry Pi display size
        self.geometry("800x480")
        
        # Configure layout (2 columns: Sidebar and Content)
        # Sidebar gets fixed width, Content expands
        self.grid_columnconfigure(0, weight=1) # 20% width roughly
        self.grid_columnconfigure(1, weight=4) # 80% width roughly
        self.grid_rowconfigure(0, weight=1)

        # 0. Initialize Database
        init_db()

        # 1. Sidebar Setup
        self.sidebar = Sidebar(self, switch_view_callback=self.switch_view)
        # self.sidebar.grid(row=0, column=0, sticky="nsew") # Hidden by default until login

        # 2. Main Content Area Setup
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # 3. Initialize Views
        self.views = {
            "Login": LoginView(self.main_content, app=self),
            "IP": IPView(self.main_content, app=self),
            "Scan": ScanView(self.main_content, app=self),
            "History": HistoryView(self.main_content, app=self),
            "Settings": SettingsView(self.main_content, app=self)
        }
        
        # 4. Shared Application State
        self.shared_state = {
            "target_ip": None,
            "scan_results": None,
            "is_scanning": False,
            "authenticated": False
        }
        
        # Default starting view
        self.current_view = None
        self.switch_view("Login")

    def switch_view(self, view_name: str):
        if self.current_view == view_name:
            return
            
        # Hide current view
        if self.current_view:
            self.views[self.current_view].grid_forget()
            
        # Refresh History if opening
        if view_name == "History":
            self.views["History"].load_logs()
            
        # Show new view
        self.views[view_name].grid(row=0, column=0, sticky="nsew")
        self.current_view = view_name

if __name__ == "__main__":
    # Default appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
