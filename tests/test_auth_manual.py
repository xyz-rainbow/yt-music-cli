from src.api.auth import AuthManager
import json
import os

def test_auth():
    print("Testing Auth Manager...")
    auth = AuthManager()
    
    # Clean up any existing
    if os.path.exists("auth.json"):
        os.remove("auth.json")
        
    print("1. Testing Manual Login (Mock)...")
    mock_headers = json.dumps({"cookie": "test", "x-goog-authuser": "0"})
    if auth.login_with_headers(mock_headers):
        print("   - Login manual success")
    else:
        print("   - Login manual failed")
        
    if os.path.exists("auth.json"):
        print("   - auth.json created")
    else:
        print("   - auth.json MISSING")

    # Clean up
    if os.path.exists("auth.json"):
        os.remove("auth.json")

    print("2. Testing Browser JSON Load...")
    # Create dummy browser.json
    with open("browser.json", "w") as f:
        json.dump({"cookie": "browser_test", "x-goog-authuser": "0"}, f)
        
    if auth.login_with_browser_json("browser.json"):
        print("   - Login browser.json success")
    else:
        print("   - Login browser.json failed")

    # Clean up
    if os.path.exists("browser.json"):
        os.remove("browser.json")
    if os.path.exists("auth.json"):
        os.remove("auth.json")
        
if __name__ == "__main__":
    test_auth()
