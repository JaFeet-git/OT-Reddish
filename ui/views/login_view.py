import customtkinter as ctk

class LoginView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure((0, 4), weight=1)
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="OT-Reddish Authentication", 
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.title_label.grid(row=1, column=1, pady=(0, 30))

        # Username
        self.username_entry = ctk.CTkEntry(
            self,
            placeholder_text="Username",
            width=300,
            height=40,
            font=ctk.CTkFont(size=18)
        )
        self.username_entry.grid(row=2, column=1, pady=10)

        # Password
        self.password_entry = ctk.CTkEntry(
            self,
            placeholder_text="Password",
            show="*",
            width=300,
            height=40,
            font=ctk.CTkFont(size=18)
        )
        self.password_entry.grid(row=3, column=1, pady=10)

        # Login button
        self.login_btn = ctk.CTkButton(
            self, 
            text="Login",
            command=self._attempt_login,
            width=300,
            height=45,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.login_btn.grid(row=4, column=1, pady=20)
        
        self.error_label = ctk.CTkLabel(
            self, 
            text="", 
            text_color="#F44336",
            font=ctk.CTkFont(size=14)
        )
        self.error_label.grid(row=5, column=1)

    def _attempt_login(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()
        
        # Simple hardcoded check for MVP Capstone
        if user == "admin" and pwd == "admin":
            self.error_label.configure(text="")
            self.app.shared_state["authenticated"] = True
            
            # Show the sidebar now that we are logged in
            self.app.sidebar.grid(row=0, column=0, sticky="nsew")
            
            # Move to the IP screen
            self.app.switch_view("IP")
        else:
            self.error_label.configure(text="Invalid credentials. Try admin/admin")
