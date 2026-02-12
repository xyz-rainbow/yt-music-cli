import json
import logging
import os
from typing import Optional, Dict
from ytmusicapi import YTMusic

APP_NAME = "ytmusic-cli"
CREDENTIALS_FILE = "oauth.json"
CLIENT_SECRETS_FILE = "client_secrets.json"

from ytmusicapi.auth.oauth import OAuthCredentials

class AuthManager:
    def __init__(self):
        self._api: Optional[YTMusic] = None
        self.logger = logging.getLogger(__name__)

    @property
    def api(self) -> YTMusic:
        """Returns the authenticated YTMusic instance, initializing it if necessary."""
        if self._api is None:
            self.login()
        return self._api

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials stored and can login."""
        if os.path.exists(CREDENTIALS_FILE):
            try:
                self.login()
                return True
            except Exception as e:
                self.logger.error(f"Auth check failed: {e}")
                return False
        return False

    def login(self) -> None:
        """Login using stored credentials (either OAuth or Headers)."""
        if not os.path.exists(CREDENTIALS_FILE):
            raise Exception("No credentials found. Please login first.")
        
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                auth_data = json.load(f)

            # Check if it's OAuth (has token keys) or Headers (usually has Cookie)
            # Add check for access_token before OAuth logic
            is_oauth = "access_token" in auth_data

            if is_oauth:
                # For OAuth, we might need to pass the client secrets if they exist
                client_id, client_secret = self.get_custom_credentials()
                if client_id and client_secret:
                    # ytmusicapi uses these to refresh tokens
                    
                    # Fetch Channel ID first
                    token = auth_data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    self.logger.debug("Fetching Channel ID...")
                    user_id = None
                    try:
                        import requests
                        resp = requests.get("https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true", headers=headers)
                        resp.raise_for_status()
                        channel_data = resp.json()
                        
                        if "items" in channel_data and len(channel_data["items"]) > 0:
                            user_id = channel_data["items"][0]["id"]
                            self.logger.debug(f"Found Channel ID: {user_id}")
                        else:
                            self.logger.warning("No Channel ID found in API response!")
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch Channel ID: {e}")
                        user_id = None

                    oauth_creds = OAuthCredentials(client_id, client_secret)
                    # Pass user=user_id to YTMusic
                    self._api = YTMusic(CREDENTIALS_FILE, oauth_credentials=oauth_creds, user=user_id)
                else:
                    self._api = YTMusic(CREDENTIALS_FILE)
            else:
                # Headers authentication
                self._api = YTMusic(auth=json.dumps(auth_data))
                
        except Exception:
            self.logger.error("Login error: Authentication failed.")
            raise

    def get_custom_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Load client_id and client_secret from client_secrets.json."""
        if os.path.exists(CLIENT_SECRETS_FILE):
            try:
                with open(CLIENT_SECRETS_FILE, "r") as f:
                    data = json.load(f)
                    creds = data.get("installed", {})
                    return creds.get("client_id"), creds.get("client_secret")
            except Exception as e:
                self.logger.error(f"Error loading secrets: {e}")
        return None, None

    def has_custom_credentials(self) -> bool:
        cid, secret = self.get_custom_credentials()
        return bool(cid and secret)

    def save_custom_credentials(self, client_id: str, client_secret: str):
        with open(CLIENT_SECRETS_FILE, "w") as f:
            json.dump({"installed": {"client_id": client_id, "client_secret": client_secret}}, f)

    def get_oauth_code(self):
        """Initiates the OAuth Device Code flow."""
        client_id, client_secret = self.get_custom_credentials()
        
        if not client_id or not client_secret:
             raise Exception("Missing Client Credentials. Please configure them in the UI.")

        scope = "https://www.googleapis.com/auth/youtube"
        
        try:
            import requests
            response = requests.post(
                "https://oauth2.googleapis.com/device/code",
                data={"client_id": client_id, "client_secret": client_secret, "scope": scope}
            )
            response.raise_for_status()
            data = response.json()
            return data["verification_url"], data["user_code"], data["device_code"], data["interval"]
        except Exception as e:
            self.logger.error(f"OAuth Init Failed: {e}")
            raise

    def check_oauth_poll(self, device_code: str):
        """Polls for the token using the device code."""
        client_id, client_secret = self.get_custom_credentials()

        try:
            import requests
            response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 428: # Precondition Required
                return None
            
            error_data = response.json()
            if error_data.get("error") == "authorization_pending":
                return None
            
            raise Exception(error_data.get("error_description", "Unknown error"))
                
        except Exception as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
                 # Often happens if the code expired or rate limited
                 raise Exception("Authorization expired or forbidden.")
            self.logger.error(f"OAuth Poll Failed: {e}")
            raise

    def finish_oauth(self, token_data: Dict):
        """Finalize login with token data."""
        self.save_credentials(json.dumps(token_data))
        # Re-initialize API to use the new credentials
        self.login()


    def login_with_headers(self, headers_raw: str) -> bool:
        """Attempt to login with raw JSON headers."""
        try:
            headers_dict = json.loads(headers_raw)
            # Basic validation: check if 'Cookie' or some key exists
            # ytmusicapi will validate it properly on init
            self.save_credentials(headers_raw)
            self.login()
            return True
        except Exception as e:
            self.logger.error(f"Manual header login failed: {e}")
            return False

    def save_credentials(self, data: str):
        """Save credentials to local file."""
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(data)

    def logout(self):
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
        self._api = None

