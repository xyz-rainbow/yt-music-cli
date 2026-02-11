import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.api.auth import AuthManager
    from textual.app import App
    import keyring
    import ytmusicapi
    
    print("Imports successful.")
    
    # Test keyring availability (might fail in some headless envs, but good to check)
    try:
        keyring.get_password("test-service", "test-user")
        print("Keyring backend found.")
    except Exception as e:
        print(f"Keyring warning: {e}")

except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
