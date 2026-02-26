import customtkinter as ctk

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Settings", 
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(40, 20))
        
        # Settings Layout
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        # Light/Dark Mode Switch
        self.theme_label = ctk.CTkLabel(
            self.settings_frame, 
            text="Application Theme",
            font=ctk.CTkFont(size=20)
        )
        self.theme_label.grid(row=0, column=0, padx=40, pady=40, sticky="w")
        
        self.theme_switch = ctk.CTkSwitch(
            self.settings_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(size=18),
            onvalue=1,
            offvalue=0
        )
        self.theme_switch.grid(row=0, column=1, padx=40, pady=40, sticky="e")
        self.theme_switch.select() # Default to dark mode by system
        
        # Wipe Data Button
        self.wipe_label = ctk.CTkLabel(
            self.settings_frame, 
            text="Factory Reset",
            font=ctk.CTkFont(size=20)
        )
        self.wipe_label.grid(row=1, column=0, padx=40, pady=40, sticky="w")
        
        self.wipe_btn = ctk.CTkButton(
            self.settings_frame, 
            text="Wipe All Data",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#F44336",
            hover_color="#d32f2f",
            height=40
        )
        self.wipe_btn.grid(row=1, column=1, padx=40, pady=40, sticky="e")
        
    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Light Mode")
