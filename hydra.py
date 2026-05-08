import shutil
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("hydra_results.log")


DB_FILE = Path("scans.db")
USER_FILE = Path("user.txt")
PASS_FILE = Path("pass.txt")

SERVICES = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
}


def check_requirements():
    if shutil.which("wsl") is None:
        raise RuntimeError("WSL is not installed or not in PATH.")

    for file in [DB_FILE, USER_FILE, PASS_FILE]:
        if not file.exists():
            raise FileNotFoundError(f"Missing required file: {file}")


def read_lines(file_path):
    return [
        line.strip()
        for line in file_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_targets_from_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT results
        FROM scan_history
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        print("[-] No scan data found in scans.db.")
        return []

    results = row[0]
    targets = []

    print("[+] Pulling targets from latest scan in scans.db")
    print("[+] Parsing formatted scan table...")

    lines = results.splitlines()

    for line in lines:
        line = line.strip()

        if not line.startswith("192.168."):
            continue

        parts = line.split()

        if len(parts) < 4:
            continue

        ip = parts[0]

        # Based on your saved scan table:
        # parts[1] = FTP(21)
        # parts[2] = SSH(22)
        # parts[3] = TELNET(23)

        if parts[1].upper() == "OPEN":
            print(f"[+] Found FTP open on {ip}:21")
            targets.append((ip, 21, "ftp"))

        if parts[2].upper() == "OPEN":
            print(f"[+] Found SSH open on {ip}:22")
            targets.append((ip, 22, "ssh"))

        if parts[3].upper() == "OPEN":
            print(f"[+] Found TELNET open on {ip}:23")
            targets.append((ip, 23, "telnet"))

    return targets


def log_result(text):
    with LOG_FILE.open("a") as log:
        log.write(text + "\n")


def run_hydra(ip, port, service):
    print(f"\n[+] Testing {service} on {ip}:{port}")

    cmd = [
        "wsl",
        "hydra",
        "-L", str(USER_FILE),
        "-P", str(PASS_FILE),
        "-s", str(port),
        "-t", "1",
        "-W", "3",
        "-I",
        "-f",
        "-u",
        ip,
        service,
    ]

    print("DEBUG CMD:", cmd)

    log_result(f"\n--- {datetime.now()} ---")
    log_result(f"Target: {ip}:{port} ({service})")
    log_result("Command: " + " ".join(cmd))

    process = None

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            print(line, end="")
            log_result(line.strip())

        process.wait(timeout=30)

        if process.returncode == 0:
            print("[+] Hydra finished successfully.")
        else:
            print(f"[-] Hydra exited with code {process.returncode}")

    except subprocess.TimeoutExpired:
        print("[!] Hydra timed out. Stopping scan.")
        log_result("[!] Hydra timed out. Stopping scan.")
        if process:
            process.terminate()
            process.wait()

    except KeyboardInterrupt:
        print("\n[!] Scan cancelled by user.")
        if process:
            process.terminate()


def main():
    check_requirements()

    users = read_lines(USER_FILE)
    passwords = read_lines(PASS_FILE)
    targets = load_targets_from_db()

    print(f"[+] Loaded {len(users)} username(s)")
    print(f"[+] Loaded {len(passwords)} password(s)")
    print(f"[+] Total attempts per target: {len(users) * len(passwords)}")

    if not targets:
        print("[-] No Hydra-compatible targets found in latest scan.")
        return

    for ip, port, service in targets:
        run_hydra(ip, port, service)


if __name__ == "__main__":
    main()