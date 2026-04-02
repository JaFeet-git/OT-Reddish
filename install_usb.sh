#!/bin/bash
# OT-Reddish Raspberry Pi USB Auto-Installer Script
# Place this script on a USB formatting as FAT32, plug into the Pi, and run it.

echo "============================================="
echo "   OT-Reddish Automated Installer for RPi    "
echo "============================================="

# 1. Update and install dependencies
echo "[1/4] Installing system dependencies (nmap, python3, pip, tkinter)..."
sudo apt-get update -y
sudo apt-get install -y git nmap python3 python3-pip python3-venv python3-tk

# 2. Clone or Update the repository
INSTALL_DIR="/home/pi/OT-Reddish"
if [ -d "$INSTALL_DIR" ]; then
    echo "[2/4] Updating existing OT-Reddish repository..."
    cd $INSTALL_DIR
    git pull origin main
else
    echo "[2/4] Cloning OT-Reddish repository..."
    # Replace URL with your actual GitHub repository URL
    git clone https://github.com/we don't know yet/ot-reddish.git $INSTALL_DIR
    cd $INSTALL_DIR
fi

# 3. Setup Python Virtual Environment
echo "[3/4] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Assuming requirements: python-nmap, customtkinter
pip install python-nmap customtkinter

# 4. Setup Systemd Auto-start Service
echo "[4/4] Configuring Autostart on Boot..."
sudo cp ot-reddish.service /etc/systemd/system/
sudo systemctl enable ot-reddish.service
sudo systemctl start ot-reddish.service

echo "============================================="
echo " Installation Complete! "
echo " OT-Reddish will now run automatically on boot. "
echo " You can also run it manually via:"
echo "   cd $INSTALL_DIR && source venv/bin/activate && python3 app.py"
echo "============================================="
