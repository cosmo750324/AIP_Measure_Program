import subprocess
import os
import sys

# Determine the path to config_viewer_ui.py (assumed to be in the same directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(current_dir, "config_viewer_ui.py")

if not os.path.exists(ui_path):
    sys.stderr.write(f"[ERROR] UI script not found at {ui_path}\n")
    sys.exit(1)

# Launch the UI script using the same Python interpreter
try:
    subprocess.run([sys.executable, ui_path], check=True)
except subprocess.CalledProcessError as e:
    sys.stderr.write(f"[ERROR] Failed to launch UI: {e}\n")
    sys.exit(e.returncode)

