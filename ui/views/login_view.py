import customtkinter as ctk
from ui.theme import UI

class LoginView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.card = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.card.grid(row=1, column=0, padx=20, pady=20, sticky="")
        self.card.grid_columnconfigure(0, weight=1)

        self.kicker_label = ctk.CTkLabel(
            self.card,
            text="ACCESS CONTROL",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=UI.TEXT_MUTED
        )
        self.kicker_label.grid(row=0, column=0, padx=40, pady=(24, 2))

        self.title_label = ctk.CTkLabel(
            self.card,
            text="OT-Reddish Authentication", 
            font=ctk.CTkFont(size=UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.title_label.grid(row=1, column=0, padx=40, pady=(0, 6))

        # self.subtitle_label = ctk.CTkLabel(
        #     self.card,
        #     # text="Enter operator credentials to access scan controls",
        #     font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
        #     text_color=UI.TEXT_SECONDARY
        # )
        # self.subtitle_label.grid(row=2, column=0, padx=40, pady=(0, 18))

        self.username_entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Username",
            width=360,
            height=44,
            fg_color=UI.INPUT_BG,
            font=ctk.CTkFont(size=18)
        )
        self.username_entry.grid(row=3, column=0, padx=40, pady=8)

        self.password_entry = ctk.CTkEntry(
            self.card,
            placeholder_text="Password",
            show="*",
            width=360,
            height=44,
            fg_color=UI.INPUT_BG,
            font=ctk.CTkFont(size=18)
        )
        self.password_entry.grid(row=4, column=0, padx=40, pady=8)

        self.login_btn = ctk.CTkButton(
            self.card,
            text="Login",
            command=self._attempt_login,
            width=360,
            height=46,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER
        )
        self.login_btn.grid(row=5, column=0, padx=40, pady=(16, 8))
        
        self.error_label = ctk.CTkLabel(
            self.card,
            text="", 
            text_color=UI.DANGER,
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE)
        )
        self.error_label.grid(row=6, column=0, padx=40, pady=(0, 8))

        # self.hint_label = ctk.CTkLabel(
        #     self.card,
        #     text="Demo credentials: admin / admin",
        #     text_color=UI.TEXT_MUTED,
        #     font=ctk.CTkFont(size=UI.SMALL_SIZE)
        # )
        # self.hint_label.grid(row=7, column=0, padx=40, pady=(0, 20))

        self.username_entry.bind("<Return>", lambda _: self._attempt_login())
        self.password_entry.bind("<Return>", lambda _: self._attempt_login())

    def _attempt_login(self):
        # lower case accept
        user = self.username_entry.get().strip().lower()
        pwd = self.password_entry.get().strip()
        
        # Simple hardcoded check for MVP Capstone
        if user == "admin" and pwd == "admin":
            self.error_label.configure(text="")
            self.app.shared_state["authenticated"] = True

            # Move to the IP screen
            self.app.switch_view("IP")
        else:
            self.error_label.configure(text="Invalid credentials. Try admin/admin")
