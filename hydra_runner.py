import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

USER_FILE = BASE_DIR / "user.txt"
PASS_FILE = BASE_DIR / "pass.txt"

SERVICES = {
    "21": "ftp",
    "22": "ssh",
    "23": "telnet",
}
SOCKET_CHECK_TIMEOUT_SECONDS = 1.5
HYDRA_TIMEOUT_SECONDS = 180


def _is_port_reachable(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_CHECK_TIMEOUT_SECONDS)
    try:
        return sock.connect_ex((ip, int(port))) == 0
    except OSError:
        return False
    finally:
        sock.close()


def run_hydra_check(ip, port):
    if not ip:
        return "Error: No IP provided.\n"

    if not port:
        return "Error: No port provided.\n"

    port = str(port)

    if port not in SERVICES:
        return f"Error: Port {port} not supported (try 21, 22, 23).\n"

    if not USER_FILE.exists():
        return f"Error: user.txt not found at {USER_FILE}\n"

    if not PASS_FILE.exists():
        return f"Error: pass.txt not found at {PASS_FILE}\n"

    service = SERVICES[port]

    if not _is_port_reachable(ip, port):
        return (
            f"Error: {ip}:{port} is not reachable right now. "
            "Verify host is online, service is listening, and firewall rules allow access.\n"
        )

    # Linux/macOS path: use hydra directly.
    if os.name != "nt":
        if shutil.which("hydra") is None:
            if sys.platform == "darwin":
                return "Error: Hydra is not installed or not in PATH. On macOS run: brew install hydra\n"
            return "Error: Hydra is not installed or not in PATH.\n"

        command = [
            "hydra",
            "-L", str(USER_FILE),
            "-P", str(PASS_FILE),
            "-s", port,
            "-t", "1",
            "-w", "5",
            "-W", "1",
            "-I",
            "-f",
            ip,
            service,
        ]

    # Windows path: prefer native hydra.exe/hydra in PATH, fallback to WSL.
    else:
        hydra_exe = shutil.which("hydra.exe") or shutil.which("hydra")
        if hydra_exe:
            command = [
                hydra_exe,
                "-L", str(USER_FILE),
                "-P", str(PASS_FILE),
                "-s", port,
                "-t", "1",
                "-w", "5",
                "-W", "1",
                "-I",
                "-f",
                ip,
                service,
            ]
        else:
            wsl_exe = shutil.which("wsl.exe") or shutil.which("wsl")
            if not wsl_exe:
                return (
                    "Error: Hydra is not available on Windows PATH and WSL is not installed. "
                    "Install Hydra natively or enable WSL + Hydra.\n"
                )

            def to_wsl_path(path):
                p = str(path).replace("\\", "/")
                drive, rest = p.split(":", 1)
                return f"/mnt/{drive.lower()}{rest}"

            command = [
                wsl_exe,
                "hydra",
                "-L", to_wsl_path(USER_FILE),
                "-P", to_wsl_path(PASS_FILE),
                "-s", port,
                "-t", "1",
                "-w", "5",
                "-W", "1",
                "-I",
                "-f",
                ip,
                service,
            ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=HYDRA_TIMEOUT_SECONDS,
        )

        output = result.stdout + result.stderr
        return output if output.strip() else "No results returned.\n"

    except subprocess.TimeoutExpired:
        return (
            f"Error: Hydra scan timed out after {HYDRA_TIMEOUT_SECONDS}s. "
            "Try a smaller wordlist or verify target service responsiveness.\n"
        )

    except Exception as e:
        return f"Error: {str(e)}\n"