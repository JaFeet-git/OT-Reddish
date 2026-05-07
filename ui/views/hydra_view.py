import customtkinter as ctk
from ui.theme import UI


class HydraView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Hydra Module",
            font=ctk.CTkFont(size=UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY,
        )
        title.grid(row=1, column=0, pady=(0, 10))

        note = ctk.CTkLabel(
            self,
            text="Hydra view is available for integration.\nUse the external Hydra scripts for now.",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY,
            justify="center",
        )
        note.grid(row=2, column=0, pady=(0, 30))
