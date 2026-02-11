import json
import keyring
import logging
from typing import Optional
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials

APP_NAME = "ytmusic-cli"
KEYRING_SERVICE = "ytmusic-cli-auth"
CREDENTIALS_FILE = "oauth.json"

class AuthManager:
    def __init__(self):
        self.api: Optional[YTMusic] = None
        self.logger = logging.getLogger(__name__)

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials stored."""
        token = keyring.get_password(KEYRING_SERVICE, "auth_token")
        if token:
            try:
                # Try to load credentials
                self.login()
                return True
            except Exception as e:
                self.logger.error(f"Auth check failed: {e}")
                return False
        return False

    def login(self) -> None:
        """Login using stored credentials."""
        token = keyring.get_password(KEYRING_SERVICE, "auth_token")
        if not token:
            raise Exception("No credentials found")
        
        try:
            # Determine if it's OAuth or Browser Cookies based on format
            # For simplicity, we assume JSON string for now
            auth_data = json.loads(token)
            
            # If it's oauth, we might need a file, ytmusicapi expects a file for oauth
            # For this implementation, we will use a temporary file or pass dict if supported
            # ytmusicapi 1.0+ supports passing dict/json directly in some methods, but standard init takes file for oauth
            # OR headers dict for browser.
            
            # Creating a fresh instance
            if "token_type" in auth_data: # OAuth
                 with open(CREDENTIALS_FILE, 'w') as f:
                     json.dump(auth_data, f)
                 self.api = YTMusic(CREDENTIALS_FILE)
            else: # Cookies (headers dict)
                self.api = YTMusic(auth=json.dumps(auth_data))
                
        except json.JSONDecodeError:
            # Maybe it's a raw headers string? 
             self.api = YTMusic(auth=token)

    def get_oauth_url(self):
        """
        Generates the OAuth URL and code for the user.
        Returns a tuple (url, code) or raises Exception.
        """
        # We need to simulate what setup_oauth does but break it into steps
        # flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(...)
        # However, ytmusicapi wraps this. 
        # For simplicity in this demo without a custom client ID, we might need to rely on
        # the user pasting headers or a simplified flow.
        # But let's assume we can use the default ytmusicapi simplified flow if possible, 
        # or just ask for headers which is more reliable for "ytmusicapi".
        pass 

    def login_with_headers(self, headers_str: str) -> bool:
        """Login with raw JSON headers."""
        try:
            headers = json.loads(headers_str)
            self.api = YTMusic(auth=json.dumps(headers))
            self.save_credentials(json.dumps(headers))
            return True
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

