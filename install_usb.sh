#!/bin/bash
#
# OT-Reddish — Raspberry Pi USB one-shot installer
#
# Step 1: Flash Raspberry Pi OS, boot with network, then plug in a USB drive
#         that contains this script (FAT32 is fine) and run:
#
#     bash /media/pi/NAMEOFUSB/install_usb.sh
#
#     or, after copying the script to the home folder:
#     sudo bash ./install_usb.sh
#
# This will: install dependencies (nmap, Python, venv, Tcl/Tk), clone
# https://github.com/JaFeet-git/OT-Reddish from GitHub, create a venv from
# requirements.txt, and install/enable a systemd user-facing service that
# starts the GUI on the graphical target. With OT_REDDISH_KIOSK=1, the app
# opens in fullscreen (kiosk) after the desktop and DISPLAY :0 are up.
#
# Reboot if the service was already running, or: sudo systemctl restart ot-reddish
#

set -euo pipefail

GITHUB_REPO="https://github.com/JaFeet-git/OT-Reddish.git"
INSTALL_NAME="OT-Reddish"

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  head -n 20 "$0" | tail -n +2
  exit 0
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This installer must be run as root, e.g.: sudo $0" >&2
  exit 1
fi

# Default Raspberry Pi OS login user; allow override: OT_REDDISH_USER=jane ./install
RUN_USER="${OT_REDDISH_USER:-${SUDO_USER:-}}"
if [[ -z "$RUN_USER" ]] || [[ "$RUN_USER" == "root" ]]; then
  if id -u pi &>/dev/null; then
    RUN_USER="pi"
  else
    echo "Set OT_REDDISH_USER to a non-root user that owns the desktop (e.g. export OT_REDDISH_USER=pi) and re-run with sudo." >&2
    exit 1
  fi
fi

if ! id -u "$RUN_USER" &>/dev/null; then
  echo "User $RUN_USER does not exist on this system." >&2
  exit 1
fi

USER_HOME=$(getent passwd "$RUN_USER" | cut -d: -f6)
INSTALL_DIR="$USER_HOME/$INSTALL_NAME"
VENV_PY="$INSTALL_DIR/venv/bin/python"

if [[ -z "$USER_HOME" || ! -d "$USER_HOME" ]]; then
  echo "Could not resolve home for user $RUN_USER" >&2
  exit 1
fi

echo "============================================="
echo "  OT-Reddish — Raspberry Pi installer         "
echo "  Install for user: $RUN_USER  ($USER_HOME) "
echo "============================================="

export DEBIAN_FRONTEND=noninteractive
echo
echo "[1/5] Installing system packages (git, nmap, python3, venv, python3-tk)…"
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates \
  git \
  nmap \
  python3 \
  python3-pip \
  python3-venv \
  python3-tk

echo
if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "[2/5] Updating existing $INSTALL_NAME…"
  sudo -u "$RUN_USER" -H env HOME="$USER_HOME" bash -c "cd $(printf %q "$INSTALL_DIR") && git pull --ff-only origin main"
else
  if [[ -e "$INSTALL_DIR" ]]; then
    echo "Path exists and is not a git repo: $INSTALL_DIR" >&2
    echo "Move or remove it, then re-run the installer." >&2
    exit 1
  fi
  echo "[2/5] Cloning $INSTALL_NAME from GitHub…"
  sudo -u "$RUN_USER" -H env HOME="$USER_HOME" git clone --branch main --depth 1 "$GITHUB_REPO" "$INSTALL_DIR"
fi

echo
echo "[3/5] Python virtual environment and pip…"
if [[ ! -f "$VENV_PY" ]]; then
  sudo -u "$RUN_USER" -H env HOME="$USER_HOME" bash -c "cd $(printf %q "$INSTALL_DIR") && python3 -m venv venv"
fi
sudo -u "$RUN_USER" -H env HOME="$USER_HOME" bash -c "cd $(printf %q "$INSTALL_DIR") && venv/bin/pip install -U pip && venv/bin/pip install -r $(printf %q "$INSTALL_DIR/requirements.txt")"

echo
echo "[4/5] Writing systemd service (kiosk on boot)…"
SERVICE_FILE="/etc/systemd/system/ot-reddish.service"
cat > "$SERVICE_FILE" <<EOF2
[Unit]
Description=OT-Reddish Scanner (Kiosk)
After=network.target graphical.target
Wants=network.target

[Service]
Type=simple
User=$RUN_USER
Group=$RUN_USER
WorkingDirectory=$INSTALL_DIR
Environment=HOME=$USER_HOME
Environment=DISPLAY=:0
Environment=OT_REDDISH_PI_MODE=1
Environment=OT_REDDISH_KIOSK=1
Environment=XAUTHORITY=$USER_HOME/.Xauthority
# Allow GUI after desktop session on :0 (Raspberry Pi OS)
ExecStart=$VENV_PY $INSTALL_DIR/app.py
Restart=on-failure
RestartSec=5
# If the app starts before the desktop, systemd will restart until DISPLAY works.
TimeoutStartSec=60

[Install]
WantedBy=graphical.target
EOF2
chmod 644 "$SERVICE_FILE"

echo
echo "[5/5] Enabling and starting service…"
systemctl daemon-reload
systemctl enable ot-reddish.service
# Try to start; failure here is not fatal (e.g. no GUI yet in SSH-only session)
if systemctl start ot-reddish.service 2>/dev/null; then
  systemctl --no-pager -l status ot-reddish.service || true
else
  echo "Service start skipped or failed (normal if you are in SSH with no local desktop). Reboot the Pi: the app should start in kiosk after login to the desktop."
fi

echo
echo "============================================="
echo " Installation complete."
echo "  • App path:  $INSTALL_DIR"
echo "  • Service:  sudo systemctl status|restart|stop ot-reddish"
echo "  • Kiosk env: OT_REDDISH_KIOSK=1 OT_REDDISH_PI_MODE=1 (set in the unit)"
echo " Reboot to confirm full-screen on every power-up."
echo "============================================="
