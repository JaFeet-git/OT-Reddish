import customtkinter as ctk
from typing import Callable, Tuple

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, switch_view_callback: Callable):
        super().__init__(master, corner_radius=0)
        
        self.switch_view_callback = switch_view_callback
        
        # Grid layout for sidebar (4 rows for 4 buttons)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Colors based on mockup
        colors = [
            ("IP", "#FFFF00", "black"),         # Yellow, Black text
            ("Scan", "#FF0000", "white"),       # Red, White text
            ("History", "#FF8C00", "black"),    # Orange, Black text
            ("Settings", "#9370DB", "white")    # Purple, White text
        ]
        
        self.buttons = {}
        
        for i, (text, bg_color, text_color) in enumerate(colors):
            btn = ctk.CTkButton(
                self, 
                text=text, 
                fg_color=bg_color, 
                text_color=text_color,
                hover_color=self._adjust_color(bg_color, -20),
                font=ctk.CTkFont(size=20, weight="bold"),
                corner_radius=10,
                command=lambda t=text: self._on_button_click(t)
            )
            # Add padding around buttons to match mockup look somewhat 
            btn.grid(row=i, column=0, sticky="nsew", padx=20, pady=20)
            self.buttons[text] = btn

    def _on_button_click(self, view_name: str):
        self.switch_view_callback(view_name)
        
    def _adjust_color(self, hex_color: str, factor: int) -> str:
        """Helper to slightly darken/lighten a hex color for hover effect"""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, min(255, r + factor))
            g = max(0, min(255, g + factor))
            b = max(0, min(255, b + factor))
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return hex_color
