import customtkinter as ctk
import threading
from hydra_runner import run_hydra_check
from ui.theme import UI


class HydraView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.is_pi_mode = self.app.shared_state.get("pi_mode", False)
        self._is_running = False

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
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

        title = ctk.CTkLabel(
            self.header_frame,
            text="Hydra Module",
            font=ctk.CTkFont(size=22 if self.is_pi_mode else UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w")

        note = ctk.CTkLabel(
            self.header_frame,
            text="Run credential checks against FTP (21), SSH (22), or TELNET (23).",
            font=ctk.CTkFont(size=12 if self.is_pi_mode else UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY,
            justify="left",
        )
        note.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.card = ctk.CTkFrame(
            self,
            corner_radius=UI.RADIUS_LG,
            fg_color=UI.CARD_BG,
            border_width=1,
            border_color=UI.BORDER
        )
        self.card.grid(
            row=1,
            column=0,
            padx=14 if self.is_pi_mode else 28,
            pady=(0, 10 if self.is_pi_mode else 16),
            sticky="nsew"
        )
        self.card.grid_rowconfigure(5, weight=1)
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_columnconfigure(1, weight=1)

        self.target_label = ctk.CTkLabel(
            self.card,
            text="Target IP",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.target_label.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self.port_label = ctk.CTkLabel(
            self.card,
            text="Port",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.port_label.grid(row=0, column=1, padx=16, pady=(12, 6), sticky="w")

        self.target_entry = ctk.CTkEntry(
            self.card,
            height=36 if self.is_pi_mode else 42,
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 16, weight="bold"),
            placeholder_text="Example: 192.168.1.15",
            fg_color=UI.INPUT_BG
        )
        self.target_entry.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        default_target = self.app.shared_state.get("target_ip")
        if default_target:
            self.target_entry.insert(0, str(default_target))

        self.port_var = ctk.StringVar(value="21")
        self.port_option = ctk.CTkOptionMenu(
            self.card,
            values=["21", "22", "23"],
            variable=self.port_var,
            height=36 if self.is_pi_mode else 42,
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 16, weight="bold")
        )
        self.port_option.grid(row=1, column=1, padx=16, pady=(0, 10), sticky="ew")

        self.action_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.action_row.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")
        self.action_row.grid_columnconfigure(0, weight=1)
        self.action_row.grid_columnconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(
            self.action_row,
            text="Run Hydra Check",
            height=36 if self.is_pi_mode else 42,
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 16, weight="bold"),
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER,
            command=self._start_hydra_check
        )
        self.run_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.clear_btn = ctk.CTkButton(
            self.action_row,
            text="Clear Output",
            height=36 if self.is_pi_mode else 42,
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 16, weight="bold"),
            fg_color=UI.CONTROL_BG,
            hover_color=UI.CONTROL_HOVER,
            text_color=UI.CONTROL_TEXT,
            command=self._clear_output
        )
        self.clear_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.card,
            text="Idle",
            font=ctk.CTkFont(size=UI.SMALL_SIZE, weight="bold"),
            text_color=UI.TEXT_SECONDARY,
            fg_color=UI.CARD_SUBTLE_BG,
            corner_radius=20,
            padx=10,
            pady=5
        )
        self.status_label.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        self.output_title = ctk.CTkLabel(
            self.card,
            text="Hydra Output",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.output_title.grid(row=4, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        self.output_box = ctk.CTkTextbox(
            self.card,
            fg_color=UI.INPUT_BG,
            font=ctk.CTkFont(family="Courier", size=12 if self.is_pi_mode else 14)
        )
        self.output_box.grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="nsew")

    def _clear_output(self):
        self.output_box.delete("1.0", "end")

    def _start_hydra_check(self):
        if self._is_running:
            return

        target_ip = self.target_entry.get().strip()
        if not target_ip:
            self.status_label.configure(text="Provide a target IP first.", text_color=UI.DANGER)
            return

        self._is_running = True
        self.run_btn.configure(state="disabled")
        self.status_label.configure(text="Running Hydra check...", text_color=UI.PRIMARY)
        self.output_box.insert("end", f"\n[Hydra] Target {target_ip}:{self.port_var.get()} started...\n")
        self.output_box.see("end")

        threading.Thread(
            target=self._run_hydra_worker,
            args=(target_ip, self.port_var.get()),
            daemon=True
        ).start()

    def _run_hydra_worker(self, target_ip, port):
        output = run_hydra_check(target_ip, port)
        self.after(0, self._on_hydra_complete, output, target_ip, port)

    def _on_hydra_complete(self, output, target_ip, port):
        self._is_running = False
        self.run_btn.configure(state="normal")
        self.status_label.configure(text="Completed", text_color=UI.SUCCESS)
        self.output_box.insert("end", f"[Hydra] Target {target_ip}:{port} completed.\n")
        self.output_box.insert("end", output if output.endswith("\n") else f"{output}\n")
        self.output_box.see("end")
