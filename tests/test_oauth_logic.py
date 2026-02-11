from src.api.auth import AuthManager
import time
import os

def test_oauth_flow():
    print("Testing OAuth Device Flow logic...")
    auth = AuthManager()
    
    try:
        url, user_code, device_code, interval = auth.get_oauth_code()
        print(f"Success! Got code.")
        print(f"URL: {url}")
        print(f"User Code: {user_code}")
        print(f"Device Code: {device_code}")
        print(f"Interval: {interval}")
        
        print("\nSimulating a single poll check (should be pending)...")
        token = auth.check_oauth_poll(device_code)
        if token is None:
            print("Correctly returned None (Pending)")
        else:
            print(f"Unexpected token/error: {token}")
            
    except Exception as e:
        print(f"OAuth Flow Failed: {e}")

if __name__ == "__main__":
    test_oauth_flow()
