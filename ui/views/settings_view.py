import customtkinter as ctk
from ui.theme import UI

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=28, pady=(18, 8), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Settings",
            font=ctk.CTkFont(size=UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.title_label.grid(row=0, column=0)

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Appearance and data lifecycle controls",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, pady=(2, 0))
        
        self.settings_frame = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.settings_frame.grid(row=1, column=0, padx=28, pady=(0, 16), sticky="nsew")
        
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        self.theme_label = ctk.CTkLabel(
            self.settings_frame, 
            text="Application Theme",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.theme_label.grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        self.theme_help = ctk.CTkLabel(
            self.settings_frame,
            text="Choose a comfortable mode for you",
            font=ctk.CTkFont(size=UI.SMALL_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.theme_help.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")
        
        self.theme_switch = ctk.CTkSwitch(
            self.settings_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(size=18),
            onvalue=1,
            offvalue=0
        )
        self.theme_switch.grid(row=0, column=1, rowspan=2, padx=24, pady=(20, 16), sticky="e")
        self.theme_switch.select() # Default to dark mode by system
        
        self.divider = ctk.CTkFrame(self.settings_frame, height=1, fg_color=UI.BORDER)
        self.divider.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))

        self.wipe_label = ctk.CTkLabel(
            self.settings_frame, 
            text="Factory Reset",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.wipe_label.grid(row=3, column=0, padx=24, pady=(14, 4), sticky="w")

        self.wipe_help = ctk.CTkLabel(
            self.settings_frame,
            text="Erases stored history logs. ",
            font=ctk.CTkFont(size=UI.SMALL_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.wipe_help.grid(row=4, column=0, padx=24, pady=(0, 20), sticky="w")
        
        self.wipe_btn = ctk.CTkButton(
            self.settings_frame, 
            text="Wipe All Data",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=UI.DANGER,
            hover_color=UI.DANGER_HOVER,
            height=40,
            state="disabled"
        )
        self.wipe_btn.grid(row=3, column=1, rowspan=2, padx=24, pady=(14, 20), sticky="e")
        
    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Light Mode")
