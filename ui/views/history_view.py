import customtkinter as ctk
from database import get_all_logs, delete_log
from ui.theme import UI

class HistoryView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=28, pady=(18, 8), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Scan History",
            font=ctk.CTkFont(size=UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.title_label.grid(row=0, column=0)

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Review and manage previous threaded scan sessions",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, pady=(2, 0))
        
        self.table_card = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.table_card.grid(row=1, column=0, padx=28, pady=(0, 10), sticky="nsew")
        self.table_card.grid_rowconfigure(1, weight=1)
        self.table_card.grid_columnconfigure(0, weight=1)

        self.table_title = ctk.CTkLabel(
            self.table_card,
            text="Recorded Scan Sessions",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.table_title.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=3)
        self.list_frame.grid_columnconfigure(1, weight=2)
        self.list_frame.grid_columnconfigure(2, weight=3)
        self.list_frame.grid_columnconfigure(3, weight=2)
        self.list_frame.grid_columnconfigure(4, weight=1)
        
        self.selected_log = None
        self.table_widgets = []
        self.row_frames = {}
        self.row_palette = {}
        
        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, padx=28, pady=(0, 16), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.view_btn = ctk.CTkButton(
            self.action_frame, 
            text="View Detail",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=40,
            command=self._view_detail,
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER,
            state="disabled"
        )
        self.view_btn.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.delete_btn = ctk.CTkButton(
            self.action_frame, 
            text="Delete Log",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=UI.DANGER,
            hover_color=UI.DANGER_HOVER,
            height=40,
            command=self._delete_selected_log,
            state="disabled"
        )
        self.delete_btn.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Load data
        self.load_logs()

    def load_logs(self):
        # Clear existing
        for widget in self.table_widgets:
            widget.destroy()
        self.table_widgets.clear()
        self.row_frames.clear()
        self.row_palette.clear()
        self.selected_log = None
        self.view_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        
        # Fetch from DB
        logs = get_all_logs()
        
        if not logs:
            lbl = ctk.CTkLabel(self.list_frame, text="No scan history found.", font=ctk.CTkFont(size=18, slant="italic"))
            lbl.grid(row=0, column=0, padx=20, pady=20)
            self.table_widgets.append(lbl)
            return

        headers = ["Timestamp", "Target", "Scan Type", "Summary", "Select"]
        for col, header in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.list_frame,
                text=header,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=UI.TEXT_SECONDARY
            )
            lbl.grid(row=0, column=col, padx=8, pady=(5, 8), sticky="w")
            self.table_widgets.append(lbl)

        for i, log in enumerate(logs, start=1):
            row_color = UI.ROW_A if i % 2 == 0 else UI.ROW_B
            row = ctk.CTkFrame(self.list_frame, fg_color=row_color)
            row.grid(row=i, column=0, columnspan=5, padx=5, pady=4, sticky="ew")
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=3)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=1)
            self.table_widgets.append(row)
            self.row_frames[log["id"]] = row
            self.row_palette[log["id"]] = row_color

            values = [
                log["timestamp"],
                log["target_ip"],
                log["scan_type"],
                self._summarize_results(log["results"], log.get("vulnerabilities", []))
            ]
            for col, value in enumerate(values):
                value_label = ctk.CTkLabel(
                    row,
                    text=value,
                    font=ctk.CTkFont(size=13),
                    text_color=UI.TEXT_PRIMARY,
                    anchor="w",
                    justify="left"
                )
                value_label.grid(row=0, column=col, padx=8, pady=8, sticky="w")

            select_btn = ctk.CTkButton(
                row,
                text="Pick",
                width=72,
                height=30,
                fg_color=UI.CONTROL_BG,
                hover_color=UI.CONTROL_HOVER,
                text_color=UI.CONTROL_TEXT,
                command=lambda l=log: self._select_log(l)
            )
            select_btn.grid(row=0, column=4, padx=8, pady=6, sticky="e")

    def _select_log(self, log):
        self.selected_log = log
        for row_id, row in self.row_frames.items():
            if row_id == log["id"]:
                row.configure(fg_color=UI.ROW_SELECTED)
            else:
                row.configure(fg_color=self.row_palette.get(row_id, UI.ROW_A))
        self.view_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")

    def _summarize_results(self, results, vulnerabilities):
        if vulnerabilities:
            return f"{len(vulnerabilities)} potential match(es)"
        lines = [line.strip() for line in results.splitlines() if line.strip()]
        for line in lines:
            if line.lower().startswith("hosts scanned:"):
                return line[:45]
        if lines:
            return lines[0][:45]
        return "-"

    def _view_detail(self):
        if not self.selected_log: return
        
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Scan Detail: {self.selected_log['target_ip']}")
        detail_window.geometry("760x520")
        detail_window.attributes("-topmost", True)
        detail_window.configure(fg_color=UI.MAIN_PANEL_BG)

        title = ctk.CTkLabel(
            detail_window,
            text=f"{self.selected_log['scan_type']} - {self.selected_log['target_ip']}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        title.pack(anchor="w", padx=20, pady=(16, 4))

        meta = ctk.CTkLabel(
            detail_window,
            text=f"Captured at {self.selected_log['timestamp']}",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        meta.pack(anchor="w", padx=20, pady=(0, 10))

        textbox = ctk.CTkTextbox(
            detail_window,
            font=ctk.CTkFont(family="Courier", size=13),
            fg_color=UI.INPUT_BG,
            corner_radius=UI.RADIUS
        )
        textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        textbox.insert("0.0", f"Scan Profile: {self.selected_log['scan_type']}\n")
        textbox.insert("end", f"Time: {self.selected_log['timestamp']}\n")
        textbox.insert("end", "======================================\n\n")
        vulnerabilities = self.selected_log.get("vulnerabilities", [])
        if vulnerabilities:
            textbox.insert("end", "Potential Vulnerability Matches:\n")
            textbox.insert("end", "--------------------------------------\n")
            for entry in vulnerabilities:
                if entry.get("source") == "rockwell_cves":
                    textbox.insert(
                        "end",
                        f"- [Rockwell CVE] {entry.get('device_name', 'Unknown device')} | "
                        f"{entry.get('cve_id', 'N/A')} | Severity: {entry.get('severity', 'N/A')}\n"
                    )
                else:
                    textbox.insert(
                        "end",
                        f"- Host {entry.get('host', '?')} port {entry.get('port', '?')} "
                        f"({entry.get('protocol', '?')}): {entry.get('device_software', 'Unknown')} "
                        f"-> {entry.get('exploit', 'No description')}\n"
                    )
            textbox.insert("end", "\nDetailed Scan Output:\n")
            textbox.insert("end", "--------------------------------------\n")
        textbox.insert("end", self.selected_log['results'])
        textbox.configure(state="disabled") # readonly

    def _delete_selected_log(self):
        if not self.selected_log: return
        delete_log(self.selected_log['id'])
        self.load_logs()
