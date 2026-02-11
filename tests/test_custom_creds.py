from src.api.auth import AuthManager
import json
import os

def test_custom_creds():
    print("Testing Custom Credentials Logic...")
    
    # Create mock client_secrets.json
    mock_creds = {
        "installed": {
            "client_id": "mock_id",
            "client_secret": "mock_secret"
        }
    }
    with open("client_secrets.json", "w") as f:
        json.dump(mock_creds, f)
        
    auth = AuthManager()
    if auth.has_custom_credentials():
        print("PASS: Detected custom credentials")
    else:
        print("FAIL: Did not detect custom credentials")
        
    # We can't actually test get_oauth_code fully without real creds, 
    # but we can check if it tries to load them.
    # The actual integration test will happen when User inputs real creds.
    
    # Cleanup
    if os.path.exists("client_secrets.json"):
        os.remove("client_secrets.json")

if __name__ == "__main__":
    test_custom_creds()
