import customtkinter as ctk
import nmap
import threading
import socket
import time
import ipaddress
import os
from database import add_scan_log, get_vulnerability_matches_by_ports, get_rockwell_cves_preview
from ui.theme import UI
 
class ScanView(ctk.CTkFrame):
    FALLBACK_SUBNET_HOST_LIMIT = 32
    SOCKET_TIMEOUT_SECONDS = 0.35
    BLACKLIST_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "blacklist.txt")
    PORT_OPTIONS = [
        (21, "FTP", "ftp"),
        (22, "SSH", "ssh"),
        (23, "TELNET", "telnet"),
        (80, "HTTP", "http"),
        (102, "S7", "s7comm"),
        (443, "HTTPS", "https"),
        (1105, "FTRAN", "ftranhc"),
        (1217, "HPSS-ND", "hpss-ndapi"),
        (6001, "X11-1", "X11:1"),
        (2222, "RKWL", "rockwell-mgmt"),
        (44818, "ENIP", "ethernet-ip"),
    ]

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.is_pi_mode = self.app.shared_state.get("pi_mode", False)
        self.stop_event = threading.Event()
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
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
            text="Network Scanning",
            font=ctk.CTkFont(size=22 if self.is_pi_mode else UI.HEADER_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Multithreaded discovery: OT/IT + PLC (1105 ftranhc, 1217 hpss-ndapi, 6001 X11) plus FTP, SSH, S7, ENIP, etc.",
            font=ctk.CTkFont(size=12 if self.is_pi_mode else UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.scan_types_frame = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.scan_types_frame.grid(row=1, column=0, padx=14 if self.is_pi_mode else 28, pady=(0, 8 if self.is_pi_mode else 10), sticky="ew")
        self.scan_types_frame.grid_columnconfigure(0, weight=1)
        self.scan_types_frame.grid_columnconfigure(1, weight=1)

        self.profile_label = ctk.CTkLabel(
            self.scan_types_frame,
            text="Scan Profile",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.profile_label.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self.profile_value = ctk.CTkLabel(
            self.scan_types_frame,
            text="Select ports to scan",
            font=ctk.CTkFont(size=UI.SUBHEADER_SIZE),
            text_color=UI.TEXT_SECONDARY
        )
        self.profile_value.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="w")

        self.port_checks = []
        self.ports_frame = ctk.CTkFrame(self.scan_types_frame, fg_color="transparent")
        self.ports_frame.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        cols = 2 if self.is_pi_mode else 4
        for c in range(cols):
            self.ports_frame.grid_columnconfigure(c, weight=1)

        default_ports = {21, 22, 23, 80, 102, 443, 1105, 1217, 6001, 2222, 44818}
        for idx, (port, label, service_name) in enumerate(self.PORT_OPTIONS):
            cb = ctk.CTkCheckBox(
                self.ports_frame,
                text=f"{label} ({port})",
                font=ctk.CTkFont(size=12 if self.is_pi_mode else 14, weight="bold"),
            )
            if port in default_ports:
                cb.select()
            r = idx // cols
            c = idx % cols
            cb.grid(row=r, column=c, padx=6, pady=4, sticky="w")
            self.port_checks.append((port, label, service_name, cb))

        self.scan_state = ctk.CTkLabel(
            self.scan_types_frame,
            text="Idle",
            font=ctk.CTkFont(size=UI.SMALL_SIZE, weight="bold"),
            text_color=UI.TEXT_SECONDARY,
            fg_color=UI.CARD_SUBTLE_BG,
            corner_radius=20,
            padx=10,
            pady=5
        )
        self.scan_state.grid(row=0, column=1, rowspan=2, padx=16, pady=12, sticky="e")

        self.progress = ctk.CTkProgressBar(self.scan_types_frame, mode="indeterminate")
        self.progress.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")
        self.progress.set(0)

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, padx=14 if self.is_pi_mode else 28, pady=0, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        if self.is_pi_mode:
            self.button_frame.grid_rowconfigure(1, weight=1)
        else:
            self.button_frame.grid_columnconfigure(2, weight=1)
        
        self.start_btn = ctk.CTkButton(
            self.button_frame, 
            text="Start Scan",
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 20, weight="bold"),
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER,
            height=38 if self.is_pi_mode else 50,
            command=self._start_scan
        )
        self.start_btn.grid(row=0, column=0, padx=6 if self.is_pi_mode else 10, sticky="ew")
        
        self.stop_btn = ctk.CTkButton(
            self.button_frame, 
            text="Stop Scan",
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 20, weight="bold"),
            fg_color=UI.DANGER,
            hover_color=UI.DANGER_HOVER,
            height=38 if self.is_pi_mode else 50,
            state="disabled",
            command=self._stop_scan
        )
        self.stop_btn.grid(row=0, column=1, padx=6 if self.is_pi_mode else 10, sticky="ew")

        self.demo_btn = ctk.CTkButton(
            self.button_frame,
            text="Demo Mode" if self.is_pi_mode else "Run Demo Mode",
            font=ctk.CTkFont(size=14 if self.is_pi_mode else 20, weight="bold"),
            fg_color=UI.CONTROL_BG,
            hover_color=UI.CONTROL_HOVER,
            text_color=UI.CONTROL_TEXT,
            height=34 if self.is_pi_mode else 50,
            command=self._start_demo_scan
        )
        if self.is_pi_mode:
            self.demo_btn.grid(row=1, column=0, columnspan=2, padx=6, pady=(6, 0), sticky="ew")
        else:
            self.demo_btn.grid(row=0, column=2, padx=10, sticky="ew")

        self.results_card = ctk.CTkFrame(self, corner_radius=UI.RADIUS_LG, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        self.results_card.grid(row=4, column=0, padx=14 if self.is_pi_mode else 28, pady=(8 if self.is_pi_mode else 12, 10 if self.is_pi_mode else 16), sticky="nsew")
        self.results_card.grid_rowconfigure(1, weight=1)
        self.results_card.grid_columnconfigure(0, weight=1)

        self.results_title = ctk.CTkLabel(
            self.results_card,
            text="Scan Output",
            font=ctk.CTkFont(size=UI.BODY_SIZE, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        self.results_title.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.results_box = ctk.CTkTextbox(
            self.results_card,
            font=ctk.CTkFont(family="Courier", size=12 if self.is_pi_mode else 14),
            corner_radius=UI.RADIUS,
            fg_color=UI.INPUT_BG
        )
        self.results_box.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="nsew")

    def _start_scan(self):
        target_ip = self.app.shared_state.get("target_ip")
        if not target_ip:
            self.results_box.insert("end", "Error: No Target IP specified.\n")
            return
        selected_ports = self._get_selected_ports()
        if not selected_ports:
            self.results_box.insert("end", "Error: Select at least one port to scan.\n")
            return

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.demo_btn.configure(state="disabled")
        self.scan_state.configure(text="Scanning", text_color=UI.PRIMARY)
        self.progress.start()
        self.stop_event.clear()
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Discovering hosts in {target_ip}...\nPorts: {', '.join(str(p) for p in selected_ports)}\n")

        self.app.shared_state["is_scanning"] = True
        threading.Thread(target=self._run_threaded_scan, args=(target_ip, selected_ports), daemon=True).start()

    def _start_demo_scan(self):
        target_ip = self.app.shared_state.get("target_ip") or "192.168.100.0/24 (DEMO)"
        selected_ports = self._get_selected_ports()
        if not selected_ports:
            selected_ports = [p for (p, _lbl, _svc) in self.PORT_OPTIONS]

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.demo_btn.configure(state="disabled")
        self.scan_state.configure(text="Demo Running", text_color=UI.WARNING)
        self.progress.start()
        self.stop_event.clear()
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", "Demo mode enabled.\nGenerating simulated host results...\n")

        self.app.shared_state["is_scanning"] = True
        threading.Thread(target=self._run_demo_scan, args=(target_ip, selected_ports), daemon=True).start()

    def _stop_scan(self):
        if not self.app.shared_state.get("is_scanning"):
            return
        self.stop_event.set()
        self.scan_state.configure(text="Stopping", text_color=UI.WARNING)
        self.results_box.insert("end", "\nStopping scan... waiting for worker threads.\n")

    def _run_threaded_scan(self, target_ip, selected_ports):
        started_at = time.time()
        fallback_notice = ""
        try:
            nm = nmap.PortScanner()
            nm.scan(target_ip, arguments="-sn -n")

            hosts = [host for host in nm.all_hosts() if nm[host].state() == "up"]
            # If user entered a single IP and host discovery is blocked, still attempt direct scan.
            if not hosts and "/" not in target_ip and not self.stop_event.is_set():
                hosts = [target_ip]
            # Some networks block ping/host discovery. Fall back to direct host attempts for subnets.
            elif not hosts and "/" in target_ip and not self.stop_event.is_set():
                try:
                    network = ipaddress.ip_network(target_ip, strict=False)
                    candidate_hosts = [str(host) for host in network.hosts()]
                    if len(candidate_hosts) > self.FALLBACK_SUBNET_HOST_LIMIT:
                        hosts = candidate_hosts[: self.FALLBACK_SUBNET_HOST_LIMIT]
                        fallback_notice = (
                            f"Host discovery blocked. Fast fallback scan enabled for first "
                            f"{self.FALLBACK_SUBNET_HOST_LIMIT} hosts in {target_ip}."
                        )
                    else:
                        hosts = candidate_hosts
                        fallback_notice = (
                            f"Host discovery blocked. Fast fallback scan enabled for all "
                            f"{len(hosts)} hosts in {target_ip}."
                        )
                except ValueError:
                    hosts = []

            blacklist_entries = self._load_blacklist()
            original_count = len(hosts)
            if blacklist_entries and hosts:
                hosts = [h for h in hosts if not self._is_blacklisted(h, blacklist_entries)]
                skipped = original_count - len(hosts)
                if skipped > 0:
                    fallback_notice += (("\n" if fallback_notice else "") + f"Blacklisted hosts skipped: {skipped}.")

            host_results = []
            results_lock = threading.Lock()
            workers = []

            for host in hosts:
                if self.stop_event.is_set():
                    break
                worker = threading.Thread(
                    target=self._scan_single_host_services,
                    args=(host, selected_ports, host_results, results_lock),
                    daemon=True
                )
                workers.append(worker)
                worker.start()

            for worker in workers:
                worker.join()

            self.after(0, self._process_scan_results, target_ip, host_results, started_at, "live", fallback_notice, selected_ports)
        except Exception as e:
            self.after(0, self._handle_scan_error, str(e))

    def _run_demo_scan(self, target_ip, selected_ports):
        started_at = time.time()
        try:
            for _ in range(5):
                if self.stop_event.is_set():
                    break
                time.sleep(0.18)

            host_results = []
            if not self.stop_event.is_set():
                demo_services = {
                    "192.168.100.10": [(22, "ssh"), (80, "http"), (443, "https")],
                    "192.168.100.25": [(44818, "ethernet-ip"), (2222, "rockwell-mgmt")],
                    "192.168.100.30": [(1105, "ftranhc"), (1217, "hpss-ndapi"), (6001, "X11:1")],
                    "192.168.100.44": [(23, "telnet"), (102, "s7comm")],
                }
                selected_set = set(selected_ports)
                for host, services in demo_services.items():
                    filtered = [(p, s) for (p, s) in services if p in selected_set]
                    host_results.append({"host": host, "open_services": filtered})

            self.after(0, self._process_scan_results, target_ip, host_results, started_at, "demo", "", selected_ports)
        except Exception as e:
            self.after(0, self._handle_scan_error, str(e))

    def _scan_single_host_services(self, host, selected_ports, host_results, results_lock):
        open_services = []
        service_by_port = {p: svc for (p, _lbl, svc, _cb) in self.port_checks}
        for port in selected_ports:
            if self.stop_event.is_set():
                return
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.SOCKET_TIMEOUT_SECONDS)
            try:
                if sock.connect_ex((host, port)) == 0:
                    open_services.append((port, service_by_port.get(port, "unknown")))
            except OSError:
                # Ignore per-port socket errors and keep scanning the rest.
                pass
            finally:
                sock.close()

        with results_lock:
            host_results.append({
                "host": host,
                "open_services": open_services
            })

    def _process_scan_results(self, target_ip, host_results, started_at, scan_mode="live", fallback_notice="", selected_ports=None):
        self.app.shared_state["is_scanning"] = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.demo_btn.configure(state="normal")
        self.progress.stop()
        self.results_box.delete("1.0", "end")

        if self.stop_event.is_set():
            self.scan_state.configure(text="Stopped", text_color=UI.WARNING)
            self.results_box.insert("end", "Scan stopped by user.\n")
            return

        if not host_results:
            self.scan_state.configure(text="No hosts found", text_color=UI.WARNING)
            self.results_box.insert("end", "No active hosts discovered for scanning.\n")
            return

        duration = time.time() - started_at
        if scan_mode == "demo":
            output = f"DEMO MODE: Threaded service scan results for {target_ip}\n"
        else:
            output = f"Threaded service scan results for {target_ip}\n"
        output += f"Hosts scanned: {len(host_results)} | Duration: {duration:.2f}s\n"
        if fallback_notice:
            output += f"{fallback_notice}\n"
        display_cols = [(p, lbl) for (p, lbl, _svc, cb) in self.port_checks if cb.get() == 1]
        if not display_cols:
            display_cols = [(p, lbl) for (p, lbl, _svc) in self.PORT_OPTIONS]
        header_columns = " ".join(f"{label}({port})".ljust(12) for port, label in display_cols)
        header_line = f"{'Host':<16} {header_columns}"
        output += "=" * len(header_line) + "\n"
        output += header_line + "\n"
        output += "-" * len(header_line) + "\n"

        vulnerabilities_found = []
        detailed_vulnerabilities = []
        for result in sorted(host_results, key=lambda item: item["host"]):
            host = result["host"]
            open_ports = {port for port, _ in result["open_services"]}
            status_columns = " ".join(
                ("OPEN" if port in open_ports else "closed").ljust(12)
                for port, _ in display_cols
            )
            output += f"{host:<16} {status_columns}\n"
            if open_ports:
                service_list = ", ".join(service for _, service in result["open_services"])
                vulnerabilities_found.append(f"{host}: {service_list} open")
                catalog_matches = get_vulnerability_matches_by_ports(sorted(open_ports))
                for match in catalog_matches:
                    detailed_vulnerabilities.append(
                        {
                            "host": host,
                            "port": match["port"],
                            "protocol": match["protocol"],
                            "device_software": match["device_software"],
                            "exploit": match["exploit"]
                        }
                    )
        has_rockwell_context = any(
            "rockwell" in str(item.get("device_software", "")).lower()
            or "rockwell" in str(item.get("exploit", "")).lower()
            for item in detailed_vulnerabilities
        )
        if scan_mode == "demo":
            has_rockwell_context = True

        rockwell_preview = []
        if has_rockwell_context:
            rockwell_preview = get_rockwell_cves_preview(limit=5)
            for cve in rockwell_preview:
                detailed_vulnerabilities.append(
                    {
                        "source": "rockwell_cves",
                        "vendor": cve["vendor"],
                        "device_name": cve["device_name"],
                        "cve_id": cve["cve_id"],
                        "severity": cve["severity"],
                    }
                )

        if detailed_vulnerabilities:
            output += "\nPotential vulnerability matches (by open port):\n"
            output += "-" * 76 + "\n"
            for match in detailed_vulnerabilities:
                if match.get("source") == "rockwell_cves":
                    continue
                output += (
                    f"- Host {match['host']} port {match['port']} "
                    f"({match['protocol']}): {match['device_software']} -> {match['exploit']}\n"
                )
        if rockwell_preview:
            output += "\nRockwell CVE preview (mock-up data):\n"
            output += "-" * 76 + "\n"
            for cve in rockwell_preview:
                output += (
                    f"- {cve['device_name']} | {cve['cve_id']} | "
                    f"Severity: {cve['severity']}\n"
                )

        self.results_box.insert("end", output)
        self.app.shared_state["scan_results"] = output
        if scan_mode == "demo":
            self.scan_state.configure(text="Demo Complete", text_color=UI.SUCCESS)
        else:
            self.scan_state.configure(text="Completed", text_color=UI.SUCCESS)

        scan_name = "Threaded Service Scan (Demo)" if scan_mode == "demo" else "Threaded Service Scan"
        add_scan_log(target_ip, scan_name, output, vulnerabilities=detailed_vulnerabilities)
        self._show_scan_complete_notification(target_ip, vulnerabilities_found)

    def _get_selected_ports(self):
        return [port for (port, _lbl, _svc, cb) in self.port_checks if cb.get() == 1]

    def _load_blacklist(self):
        entries = []
        if not os.path.exists(self.BLACKLIST_FILE):
            return entries
        with open(self.BLACKLIST_FILE, "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                entries.append(line)
        return entries

    def _is_blacklisted(self, host, entries):
        try:
            host_ip = ipaddress.ip_address(host)
        except ValueError:
            return False
        for entry in entries:
            try:
                if "/" in entry:
                    if host_ip in ipaddress.ip_network(entry, strict=False):
                        return True
                else:
                    if host_ip == ipaddress.ip_address(entry):
                        return True
            except ValueError:
                continue
        return False

    def _show_scan_complete_notification(self, target_ip, vulnerabilities):
        popup = ctk.CTkToplevel(self)
        popup.title("Scan Complete")
        popup.geometry("560x380")
        popup.attributes('-topmost', True)
        popup.configure(fg_color=UI.MAIN_PANEL_BG)
        
        lbl = ctk.CTkLabel(
            popup,
            text=f"Scan completed for {target_ip}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=UI.TEXT_PRIMARY
        )
        lbl.pack(pady=(20, 10))
        
        if vulnerabilities:
            vuln_text = "Open services found on discovered hosts:\n\n"
            for v in vulnerabilities:
                vuln_text += f"- {v}\n"
            detail = ctk.CTkTextbox(
                popup,
                font=ctk.CTkFont(size=14),
                fg_color=UI.INPUT_BG,
                text_color=UI.DANGER
            )
            detail.insert("0.0", vuln_text)
            detail.configure(state="disabled")
            detail.pack(fill="both", expand=True, padx=20, pady=10)
        else:
            good_lbl = ctk.CTkLabel(
                popup,
                text="No immediate vulnerabilities detected.",
                font=ctk.CTkFont(size=16),
                text_color=UI.SUCCESS
            )
            good_lbl.pack(pady=20)
            
        def on_accept():
            popup.destroy()
            self.app.switch_view("IP")
            
        accept_btn = ctk.CTkButton(
            popup,
            text="Accept",
            command=on_accept,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=UI.PRIMARY,
            hover_color=UI.PRIMARY_HOVER,
            height=40
        )
        accept_btn.pack(pady=20)

    def _handle_scan_error(self, error):
        self.app.shared_state["is_scanning"] = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.demo_btn.configure(state="normal")
        self.progress.stop()
        self.scan_state.configure(text="Error", text_color=UI.DANGER)
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Scan Error: {error}\n")
