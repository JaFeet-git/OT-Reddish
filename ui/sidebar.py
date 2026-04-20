import customtkinter as ctk
from typing import Callable
from ui.theme import UI

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, switch_view_callback: Callable, compact_mode: bool = False):
        super().__init__(master, corner_radius=0, fg_color=UI.SIDEBAR_BG)
        self.switch_view_callback = switch_view_callback
        self.active_view = None
        self.compact_mode = compact_mode

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.brand_label = ctk.CTkLabel(
            self,
            text="OT Reddish",
            font=ctk.CTkFont(size=19 if self.compact_mode else 24, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.brand_label.grid(row=0, column=0, sticky="w", padx=12 if self.compact_mode else 20, pady=(12 if self.compact_mode else 24, 4))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Security Console",
            font=ctk.CTkFont(size=11 if self.compact_mode else 13),
            text_color=UI.TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", padx=12 if self.compact_mode else 20, pady=(0, 8 if self.compact_mode else 18))

        self.nav_label = ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=UI.TEXT_MUTED
        )
        self.nav_label.grid(row=2, column=0, sticky="w", padx=12 if self.compact_mode else 20, pady=(0, 6))

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.grid(row=3, column=0, sticky="nsew", padx=6 if self.compact_mode else 12, pady=(0, 10 if self.compact_mode else 16))
        self.nav_frame.grid_columnconfigure(0, weight=1)

        nav_items = [
            ("IP", "IP Setup"),
            ("Scan", "Network Scan"),
            ("History", "History Log"),
            ("Settings", "Settings")
        ]

        self.buttons = {}
        for i, (view_name, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.nav_frame,
                text=label,
                fg_color=UI.CONTROL_BG,
                text_color=UI.CONTROL_TEXT,
                hover_color=UI.CONTROL_HOVER,
                font=ctk.CTkFont(size=13 if self.compact_mode else 16, weight="bold"),
                corner_radius=UI.RADIUS,
                height=36 if self.compact_mode else 44,
                anchor="w",
                command=lambda v=view_name: self._on_button_click(v)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=4 if self.compact_mode else 6, pady=4 if self.compact_mode else 6)
            self.buttons[view_name] = btn

        self.footer_chip = ctk.CTkLabel(
            self,
            text="System Ready",
            font=ctk.CTkFont(size=UI.SMALL_SIZE, weight="bold"),
            fg_color=UI.CARD_SUBTLE_BG,
            text_color=UI.TEXT_SECONDARY,
            corner_radius=20,
            padx=12,
            pady=6
        )
        if self.compact_mode:
            self.footer_chip.grid_forget()
        else:
            self.footer_chip.grid(row=4, column=0, padx=18, pady=(0, 18), sticky="w")

    def _on_button_click(self, view_name: str):
        self.switch_view_callback(view_name)

    def set_active(self, view_name: str):
        self.active_view = view_name
        for name, btn in self.buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=(UI.PRIMARY, UI.PRIMARY_HOVER),
                    text_color=("white", "white"),
                    hover_color=(UI.PRIMARY_HOVER, UI.PRIMARY_HOVER_DARK)
                )
            else:
                btn.configure(
                    fg_color=UI.CONTROL_BG,
                    text_color=UI.CONTROL_TEXT,
                    hover_color=UI.CONTROL_HOVER
                )
