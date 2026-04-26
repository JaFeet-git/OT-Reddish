#!/usr/bin/env sh
# OT Reddish: Raspberry Pi 7" display — fullscreen kiosk + compact UI
# Usage: chmod +x run-pi-kiosk.sh && ./run-pi-kiosk.sh
cd "$(dirname "$0")" || exit 1
export OT_REDDISH_PI_MODE="${OT_REDDISH_PI_MODE:-1}"
export OT_REDDISH_KIOSK="${OT_REDDISH_KIOSK:-1}"
if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python app.py
elif [ -x "venv/bin/python" ]; then
  exec venv/bin/python app.py
else
  exec python3 app.py
fi
