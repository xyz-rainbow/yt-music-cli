import sys
import os
sys.path.append(os.getcwd())
try:
    from src.tui.screens.login import LoginScreen
    print("Imports OK")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)
