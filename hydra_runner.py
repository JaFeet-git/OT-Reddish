import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

USER_FILE = BASE_DIR / "user.txt"
PASS_FILE = BASE_DIR / "pass.txt"

SERVICES = {
    "21": "ftp",
    "22": "ssh",
    "23": "telnet",
}


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

    # If running in Linux/WSL, use hydra directly
    if os.name != "nt":
        if shutil.which("hydra") is None:
            return "Error: Hydra is not installed in WSL/Linux.\n"

        command = [
            "hydra",
            "-L", str(USER_FILE),
            "-P", str(PASS_FILE),
            "-s", port,
            "-t", "1",
            "-W", "5",
            "-I",
            "-f",
            ip,
            service,
        ]

    # If running in Windows, call Hydra through WSL
    else:
        wsl_exe = shutil.which("wsl.exe") or shutil.which("wsl")

        if not wsl_exe:
            return "Error: WSL is not available from Windows.\n"

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
            "-W", "5",
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
            timeout=60,
        )

        output = result.stdout + result.stderr
        return output if output.strip() else "No results returned.\n"

    except subprocess.TimeoutExpired:
        return "Error: Hydra scan timed out.\n"

    except Exception as e:
        return f"Error: {str(e)}\n"