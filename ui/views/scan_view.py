import customtkinter as ctk
import nmap
import threading
from database import add_scan_log
 
class ScanView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=1) # Checkboxes
        self.grid_rowconfigure(2, weight=0) # Buttons
        self.grid_rowconfigure(3, weight=2) # Results
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Network Scanning", 
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(15, 10))
        
        # Scan Type Selection
        self.scan_types_frame = ctk.CTkFrame(self)
        self.scan_types_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.scan_types_frame.grid_columnconfigure(0, weight=1)
        
        scan_options = [
            ("Quick Scan (Top 100 ports)", "-F -Pn"),
            ("Full Scan (All 65535 ports)", "-p- -Pn"),
            ("OS & Service Detection", "-O -sV -Pn"),
            ("OT Specific (Modbus/S7/EIP)", "-p 502,102,44818 -Pn")
        ]
        
        self.checkboxes = []
        for i, (option_text, option_args) in enumerate(scan_options):
            cb = ctk.CTkCheckBox(
                self.scan_types_frame, 
                text=option_text,
                font=ctk.CTkFont(size=18),
                onvalue=option_args,
                offvalue=""
            )
            cb.grid(row=i, column=0, padx=20, pady=10, sticky="w")
            if i == 0:  # Select first by default
                cb.select()
            self.checkboxes.append(cb)
            
        # Start/Stop Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        
        self.start_btn = ctk.CTkButton(
            self.button_frame, 
            text="Start Scan",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            height=50,
            command=self._start_scan
        )
        self.start_btn.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.stop_btn = ctk.CTkButton(
            self.button_frame, 
            text="Stop Scan",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#F44336",
            hover_color="#d32f2f",
            height=50,
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=1, padx=10, sticky="ew")

        # Results Area
        self.results_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Courier", size=14)
        )
        self.results_box.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="nsew")

    def _start_scan(self):
        target_ip = self.app.shared_state.get("target_ip")
        if not target_ip:
            self.results_box.insert("end", "Error: No Target IP specified.\n")
            return
            
        args = " ".join([cb.get() for cb in self.checkboxes if cb.get() != ""])
        if not args:
            args = "-F -Pn" # Default fallback
            
        self.start_btn.configure(state="disabled")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Scanning {target_ip} with args: {args}\n\nRunning...")
        
        # Run scan in thread
        self.app.shared_state["is_scanning"] = True
        threading.Thread(target=self._run_nmap_scan, args=(target_ip, args), daemon=True).start()

    def _run_nmap_scan(self, target_ip, args):
        try:
            nm = nmap.PortScanner()
            nm.scan(target_ip, arguments=args)
            
            # Post results to UI thread safely via after
            self.after(0, self._process_scan_results, nm, target_ip, args)
        except Exception as e:
            self.after(0, self._handle_scan_error, str(e))

    def _process_scan_results(self, nm, target_ip, args):
        self.app.shared_state["is_scanning"] = False
        self.start_btn.configure(state="normal")
        self.results_box.delete("1.0", "end")
        
        if not nm.all_hosts():
            self.results_box.insert("end", "Error: Check connection to the network switch/OT Reddish hardware.\n")
            return
            
        output = f"\n  Results for {target_ip}:\n"
        vulnerabilities_found = []
        for host in nm.all_hosts():
            output += f"  Host: {host} ({nm[host].hostname()})\n"
            output += f"  State: {nm[host].state()}\n"
            
            protocols = nm[host].all_protocols()
            if not protocols:
                output += "  ------------------------------------------------\n  No open ports found.\n  (All scanned ports may be filtered by a firewall)\n"
                
            for proto in protocols:
                output += f"  ------------------------------------------------\n  Protocol : {proto}\n\n"
                ports = nm[host][proto].keys()
                for port in sorted(ports):
                    state = nm[host][proto][port]['state']
                    service = nm[host][proto][port]['name']
                    output += f"  • Port : {port:<8} State : {state:<10} Service : {service}\n"
                    
                    # Basic vulnerability flagging based on open OT ports
                    ot_ports = {
                        502: "Modbus TCP",
                        102: "Siemens S7",
                        44818: "Ethernet/IP",
                        21: "FTP",
                        23: "Telnet"
                    }
                    if state == 'open' and port in ot_ports:
                        protocol_name = ot_ports.get(port, service)
                        vuln = f"Port {port} ({protocol_name}) is OPEN - Potential Vulnerability!"
                        vulnerabilities_found.append(vuln)
                        output += f"    [WARNING] {vuln}\n"
                        
        output += "\n"
        self.results_box.insert("end", output)
        self.app.shared_state["scan_results"] = output
        
        # Save to database
        scan_name = "Nmap Scan"
        if "-F" in args:
            scan_name = "Quick Scan"
        elif "-p-" in args:
            scan_name = "Full Scan"
        elif "502" in args:
            scan_name = "OT Specific Scan"
        elif "-O" in args:
            scan_name = "OS Detection"
            
        add_scan_log(target_ip, scan_name, output)
        
        # Show Accept Notification
        self._show_scan_complete_notification(target_ip, vulnerabilities_found)

    def _show_scan_complete_notification(self, target_ip, vulnerabilities):
        popup = ctk.CTkToplevel(self)
        popup.title("Scan Complete")
        popup.geometry("500x350")
        popup.attributes('-topmost', True)
        
        lbl = ctk.CTkLabel(popup, text=f"Scan completed for {target_ip}", font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=(20, 10))
        
        if vulnerabilities:
            vuln_text = "Devices at risk! The following vulnerabilities were found:\n\n"
            for v in vulnerabilities:
                vuln_text += f"- {v}\n"
            detail = ctk.CTkTextbox(popup, font=ctk.CTkFont(size=14), text_color="#F44336")
            detail.insert("0.0", vuln_text)
            detail.configure(state="disabled")
            detail.pack(fill="both", expand=True, padx=20, pady=10)
        else:
            good_lbl = ctk.CTkLabel(popup, text="No immediate vulnerabilities detected.", font=ctk.CTkFont(size=16), text_color="#4CAF50")
            good_lbl.pack(pady=20)
            
        def on_accept():
            popup.destroy()
            self.app.switch_view("IP")
            
        accept_btn = ctk.CTkButton(popup, text="Accept", command=on_accept, font=ctk.CTkFont(size=18, weight="bold"), height=40)
        accept_btn.pack(pady=20)

    def _handle_scan_error(self, error):
        self.app.shared_state["is_scanning"] = False
        self.start_btn.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Scan Error: {error}\n")
