import customtkinter as ctk
import ipaddress

class IPView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1)
        
        # Display Area
        self.ip_display = ctk.CTkEntry(
            self, 
            height=60, 
            font=ctk.CTkFont(size=30, weight="bold"),
            justify="center",
            placeholder_text="Enter IP Address..."
        )
        self.ip_display.grid(row=0, column=0, padx=40, pady=(40, 5), sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self, 
            text="", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F44336"
        )
        self.status_label.grid(row=1, column=0, pady=(0, 5))
        
        # Numpad Area
        self.numpad_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.numpad_frame.grid(row=2, column=0, padx=40, pady=10, sticky="nsew")
        
        for i in range(4):
            self.numpad_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.numpad_frame.grid_columnconfigure(i, weight=1)
            
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('DEL', 3, 2)
        ]
        
        for key, row, col in keys:
            btn = ctk.CTkButton(
                self.numpad_frame, 
                text=key,
                font=ctk.CTkFont(size=24, weight="bold"),
                fg_color=("gray75", "gray30"),
                text_color=("black", "white"),
                hover_color=("gray60", "gray40"),
                command=lambda k=key: self._on_key_press(k)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
        # Confirm Button
        self.confirm_btn = ctk.CTkButton(
            self, 
            text="Confirm IP", 
            height=50,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self._on_confirm
        )
        self.confirm_btn.grid(row=3, column=0, padx=40, pady=20, sticky="ew")

    def _on_confirm(self):
        ip = self.ip_display.get().strip()
        if not ip:
            return
            
        try:
            # Validate IP
            ipaddress.ip_address(ip)
            
            # Success
            self.status_label.configure(text="IP address has been successfully configured!", text_color="#4CAF50")
            self.app.shared_state["target_ip"] = ip
            
            # Redirect to Scan view after a short delay
            self.after(1500, self._redirect_to_scan)
            
        except ValueError:
            # Invalid IP
            self.status_label.configure(text="Invalid IP address. Please enter a valid address.", text_color="#F44336")

    def _redirect_to_scan(self):
        self.status_label.configure(text="") # Clear for next time
        self.ip_display.delete(0, 'end')
        self.app.switch_view("Scan")
        
    def _on_key_press(self, key):
        current_text = self.ip_display.get()
        if key == 'DEL':
            self.ip_display.delete(0, 'end')
            self.ip_display.insert(0, current_text[:-1])
        else:
            self.ip_display.insert('end', key)
