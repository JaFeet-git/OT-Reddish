import customtkinter as ctk
import os

from ui.sidebar import Sidebar
from ui.views.ip_view import IPView
from ui.views.scan_view import ScanView
from ui.views.history_view import HistoryView
from ui.views.settings_view import SettingsView
from ui.views.login_view import LoginView
from ui.theme import UI
from database import init_db

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OT Reddish Scanner")
        force_pi_mode = os.environ.get("OT_REDDISH_PI_MODE", "1").lower() in ("1", "true", "yes")
        self.pi_mode = force_pi_mode
        if self.pi_mode:
            self.geometry("800x480")
            self.minsize(800, 480)
        else:
            self.geometry("1120x680")
            self.minsize(980, 600)
        self.configure(fg_color=UI.APP_BG)
        
        # Sidebar gets fixed width, content expands.
        self.grid_columnconfigure(0, weight=0, minsize=170 if self.pi_mode else 250)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 0. Initialize Database
        init_db()

        # 1. Shared Application State
        self.shared_state = {
            "target_ip": None,
            "scan_results": None,
            "is_scanning": False,
            "authenticated": False,
            "pi_mode": self.pi_mode
        }

        # 1. Sidebar Setup
        self.sidebar = Sidebar(self, switch_view_callback=self.switch_view, compact_mode=self.pi_mode)
        # self.sidebar.grid(row=0, column=0, sticky="nsew") # Hidden by default until login

        # 2. Main Content Area Setup
        self.main_content = ctk.CTkFrame(
            self,
            corner_radius=UI.RADIUS_LG,
            fg_color=UI.MAIN_PANEL_BG,
            border_width=1,
            border_color=UI.BORDER
        )
        # Login starts in centered full-width mode (no sidebar shown).
        self.main_content.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
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
        
        # Default starting view
        self.current_view = None
        self.switch_view("Login")

    def switch_view(self, view_name: str):
        if self.current_view == view_name:
            return

        self._apply_layout_for_view(view_name)
            
        # Hide current view
        if self.current_view:
            self.views[self.current_view].grid_forget()
            
        # Refresh History if opening
        if view_name == "History":
            self.views["History"].load_logs()
            
        # Show new view
        self.views[view_name].grid(row=0, column=0, sticky="nsew")
        if view_name in self.sidebar.buttons:
            self.sidebar.set_active(view_name)
        self.current_view = view_name

    def _apply_layout_for_view(self, view_name: str):
        is_login = view_name == "Login"
        is_authenticated = self.shared_state.get("authenticated", False)

        if is_login or not is_authenticated:
            self.sidebar.grid_forget()
            self.main_content.grid_forget()
            self.main_content.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
            return

        # Authenticated app shell with sidebar.
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.main_content.grid_forget()
        if self.pi_mode:
            self.main_content.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=(6, 8), pady=8)
        else:
            self.main_content.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=(10, 20), pady=20)

if __name__ == "__main__":
    # Default appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()
