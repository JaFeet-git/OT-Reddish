import customtkinter as ctk
import ipaddress
import socket
from ui.theme import UI

def get_hardware_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class IPView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.is_pi_mode = self.app.shared_state.get("pi_mode", False)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(
            row=0,
            column=0,
            padx=14 if self.is_pi_mode else 28,
            pady=(10 if self.is_pi_mode else 18, 6 if self.is_pi_mode else 8),
            sticky="ew"
        )
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="IP Configuration",
            font=ctk.CTkFont(size=22 if self.is_pi_mode else UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Define target host or subnet and continue to network scanning",
            font=ctk.CTkFont(size=12 if self.is_pi_mode else UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.overview_frame = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.overview_frame.grid(row=1, column=0, padx=14 if self.is_pi_mode else 28, pady=(0, 8 if self.is_pi_mode else 10), sticky="ew")
        self.overview_frame.grid_columnconfigure(1, weight=1)

        hardware_lbl = ctk.CTkLabel(
            self.overview_frame,
            text="Scanner Interface",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        hardware_lbl.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.hardware_ip_display = ctk.CTkLabel(
            self.overview_frame,
            text=get_hardware_ip(),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=UI.SUCCESS
        )
        self.hardware_ip_display.grid(row=0, column=1, padx=16, pady=(12, 4), sticky="w")

        self.hardware_hint = ctk.CTkLabel(
            self.overview_frame,
            text="Use this address to validate scanner connectivity.",
            font=ctk.CTkFont(size=UI.SMALL_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.hardware_hint.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="w")

        refresh_btn = ctk.CTkButton(
            self.overview_frame,
            text="Refresh",
            width=96,
            fg_color=UI.CONTROL_BG,
            hover_color=UI.CONTROL_HOVER,
            text_color=UI.CONTROL_TEXT,
            command=self._refresh_hardware_ip
        )
        refresh_btn.grid(row=0, column=2, rowspan=2, padx=16, pady=12, sticky="e")

        self.target_frame = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.target_frame.grid(row=2, column=0, padx=14 if self.is_pi_mode else 28, pady=0, sticky="ew")
        self.target_frame.grid_columnconfigure(0, weight=1)

        self.target_label = ctk.CTkLabel(
            self.target_frame,
            text="Target Address or Subnet",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.target_label.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self.ip_display = ctk.CTkEntry(
            self.target_frame,
            height=40 if self.is_pi_mode else 48,
            font=ctk.CTkFont(size=18 if self.is_pi_mode else 22, weight="bold"),
            fg_color=UI.INPUT_BG,
            justify="center",
            placeholder_text="Example: 192.168.1.0/24 or 192.168.1.15"
        )
        self.ip_display.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.target_frame,
            text="",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE, weight="bold"),
            text_color=UI.DANGER
        )
        self.status_label.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        if not self.is_pi_mode:
            self.numpad_frame = ctk.CTkFrame(self.target_frame, fg_color="transparent")
            self.numpad_frame.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
            for i in range(3):
                self.numpad_frame.grid_rowconfigure(i, weight=1)
                self.numpad_frame.grid_columnconfigure(i, weight=1)

            keys = [
                ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
                ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
                ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ]
            for key, row, col in keys:
                btn = ctk.CTkButton(
                    self.numpad_frame,
                    text=key,
                    height=42,
                    font=ctk.CTkFont(size=20, weight="bold"),
                    fg_color=UI.CONTROL_BG,
                    text_color=UI.CONTROL_TEXT,
                    hover_color=UI.CONTROL_HOVER,
                    command=lambda k=key: self._on_key_press(k)
                )
                btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            self.quick_keys = ctk.CTkFrame(self.target_frame, fg_color="transparent")
            self.quick_keys.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")
            for col in range(3):
                self.quick_keys.grid_columnconfigure(col, weight=1)
            for idx, key in enumerate([".", "0", "DEL"]):
                btn = ctk.CTkButton(
                    self.quick_keys,
                    text=key,
                    height=40,
                    fg_color=UI.CONTROL_BG,
                    hover_color=UI.CONTROL_HOVER,
                    text_color=UI.CONTROL_TEXT,
                    font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
                    command=lambda k=key: self._on_key_press(k)
                )
                btn.grid(row=0, column=idx, padx=4, pady=0, sticky="ew")
        else:
            self.pi_hint = ctk.CTkLabel(
                self.target_frame,
                text="Pi mode: use keyboard input, then tap Confirm.",
                font=ctk.CTkFont(size=UI.SMALL_SIZE),
                text_color=UI.TEXT_SECONDARY
            )
            self.pi_hint.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="w")

        self.confirm_btn = ctk.CTkButton(
            self,
            text="Confirm Target IP & Proceed",
            height=38 if self.is_pi_mode else 45,
            font=ctk.CTkFont(size=15 if self.is_pi_mode else 20, weight="bold"),
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER,
            command=self._on_confirm
        )
        self.confirm_btn.grid(row=4, column=0, padx=14 if self.is_pi_mode else 28, pady=(8 if self.is_pi_mode else 12, 10 if self.is_pi_mode else 16), sticky="ew")

    def _refresh_hardware_ip(self):
        new_ip = get_hardware_ip()
        self.hardware_ip_display.configure(text=new_ip)

    def _on_confirm(self):
        ip = self.ip_display.get().strip()
        if not ip:
            return
            
        try:
            # Allow individual IP or network subnets loosely
            ipaddress.ip_network(ip, strict=False)
            
            # Success
            self.status_label.configure(text="Target IP address configured!", text_color=UI.SUCCESS)
            self.app.shared_state["target_ip"] = ip
            
            # Redirect to Scan view after a short delay
            self.after(1000, self._redirect_to_scan)
            
        except ValueError:
            # Invalid IP
            self.status_label.configure(text="Invalid IP/Subnet. Please enter a valid address.", text_color="#F44336")

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
