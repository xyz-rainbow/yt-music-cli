import json
import logging
import os
import time
from typing import Optional, Dict
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
import base64

# New imports for Simple Login
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    InstalledAppFlow = None

from src.config import get_config_dir

APP_NAME = "ytmusic-cli"
CONFIG_DIR = get_config_dir()
CREDENTIALS_FILE = str(CONFIG_DIR / "oauth.json")
CLIENT_SECRETS_FILE = str(CONFIG_DIR / "client_secrets.json")

# Simple XOR obfuscation (Key: 123) to prevent automated scraping
# These strings are XOR'd and then Base64 encoded.
_KEY = 123
_CID_ENC = "TEJOQ01PQkpCTk5PVhoXFBIWFkkUFA0fS0oXDQ4eTE8TFApMHBFJEEJDTRcLVRoLCwhVHBQUHBceDggeCRgUFQ8eFQ9VGBQW"
_SEC_ENC = "PDQ4KCsjVlYaHCRDKU0pMjA2Py5NFQwJFjcsEisdGTIsHU8="

def _get_decoded_defaults():
    try:
        cid_bytes = base64.b64decode(_CID_ENC)
        sec_bytes = base64.b64decode(_SEC_ENC)
        # Decode: XOR back with key
        cid = "".join(chr(b ^ _KEY) for b in cid_bytes)
        sec = "".join(chr(b ^ _KEY) for b in sec_bytes)
        return cid, sec
    except Exception:
        return "", ""

DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET = _get_decoded_defaults()

# Scopes required for YouTube Music
SCOPES = ["https://www.googleapis.com/auth/youtube"]

class AuthManager:
    def __init__(self):
        self._api: Optional[YTMusic] = None
        self.logger = logging.getLogger(__name__)
        self._custom_creds: Optional[tuple[Optional[str], Optional[str]]] = None

    def _get_defaults(self) -> tuple[str, str]:
        """Return default public credentials."""
        return (DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET)

    @property
    def api(self) -> YTMusic:
        """Returns the authenticated YTMusic instance, initializing it if necessary."""
        if self._api is None:
            # We don't catch the exception here so it bubbles up to the TUI
            self.login()
        return self._api

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials stored and can login."""
        if self._api is not None:
            return True

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
                content = f.read().strip()
                if not content:
                    raise Exception("Credentials file is empty.")
                auth_data = json.loads(content)

            # Stricter check for OAuth: standard ytmusicapi oauth fields
            # Headers login usually only has 'Cookie', 'User-Agent', etc.
            is_oauth = isinstance(auth_data, dict) and (
                "access_token" in auth_data or 
                "refresh_token" in auth_data
            )

            if is_oauth:
                client_id, client_secret = self.get_custom_credentials()
                if not client_id:
                    client_id, client_secret = self._get_defaults()

                oauth_creds = OAuthCredentials(client_id, client_secret)
                self._api = YTMusic(CREDENTIALS_FILE, oauth_credentials=oauth_creds)
            else:
                # For headers/cookies, pass as stringified JSON
                self._api = YTMusic(auth=json.dumps(auth_data))
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            raise

    def get_custom_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Load custom client_id and client_secret from client_secrets.json.
        """
        if self._custom_creds:
            return self._custom_creds

        if os.path.exists(CLIENT_SECRETS_FILE):
            try:
                with open(CLIENT_SECRETS_FILE, "r") as f:
                    data = json.load(f)
                    if "installed" in data:
                        creds = data["installed"]
                    elif "web" in data:
                        creds = data["web"]
                    else:
                        creds = data
                        
                    cid = creds.get("client_id")
                    secret = creds.get("client_secret")
                    if cid:
                        self._custom_creds = (cid, secret)
                        return self._custom_creds
            except Exception as e:
                self.logger.error(f"Error loading secrets: {e}")
        return None, None

    def has_custom_credentials(self) -> bool:
        cid, secret = self.get_custom_credentials()
        return bool(cid)

    def save_custom_credentials(self, client_id: str, client_secret: str):
        """
        Save custom credentials to client_secrets.json.
        """
        data = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        fd = os.open(CLIENT_SECRETS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        self._custom_creds = (client_id, client_secret)

    def _get_oauth_credentials(self, use_defaults=False) -> OAuthCredentials:
        """Build OAuthCredentials using custom or default client ID/secret."""
        if use_defaults:
            client_id, client_secret = self._get_defaults()
        else:
            client_id, client_secret = self.get_custom_credentials()
            if not client_id:
                client_id, client_secret = self._get_defaults()
        return OAuthCredentials(client_id, client_secret)

    def start_google_login(self):
        """
        The 'Infallible' login method for the main UI button.
        Uses Device Flow + Custom or Public credentials.
        """
        try:
            # TRY CUSTOM FIRST! This is what the user probably wants if they have a file.
            creds = self._get_oauth_credentials()
            code = creds.get_code()
            return (
                code["verification_url"],
                code["user_code"],
                code["device_code"],
                code["interval"],
            )
        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg or "Unauthorized" in err_msg:
                # If custom failed, maybe try public as extreme fallback, 
                # but only if it wasn't already public.
                try:
                    self.logger.info("Custom creds failed/missing, trying public fallback...")
                    creds = self._get_oauth_credentials(use_defaults=True)
                    code = creds.get_code()
                    return (
                        code["verification_url"],
                        code["user_code"],
                        code["device_code"],
                        code["interval"],
                    )
                except Exception as e2:
                    self.logger.error(f"Fallback also failed: {e2}")
                    raise Exception("Auth failed. Check if YouTube Data API v3 is enabled in Google Cloud Console.") from e2
            
            self.logger.error(f"Infallible login start failed: {e}")
            raise

    def start_local_oauth_flow(self):
        """
        Starts the 'Simple Login' flow using InstalledAppFlow.
        (Option A: Browser Redirect)
        """
        if not InstalledAppFlow:
            raise ImportError("google-auth-oauthlib and google-auth-httplib2 are required for simple login. Please install them.")

        client_id, client_secret = self.get_custom_credentials()
        if not client_id:
             client_id, client_secret = self._get_defaults()

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret or "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        try:
            # We use port 0 to find any available port.
            # We also set access_type to offline to get a refresh_token.
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(
                port=0, 
                open_browser=True,
                access_type='offline',
                prompt='consent'
            )
            
            token_data = {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": " ".join(creds.scopes),
                "expires_at": int(time.time()) + 3600
            }
            
            self.save_credentials(json.dumps(token_data))
            self.login()
            return True

        except Exception as e:
            self.logger.error(f"Local OAuth Flow Failed: {e}")
            raise Exception(f"Local login failed: {e}. If it's a 401/403, check your Google Cloud Project settings.") from e

    def get_oauth_code(self):
        """Request a device code from YouTube's OAuth endpoint (Option C)."""
        try:
            creds = self._get_oauth_credentials()
            code = creds.get_code()
            return (
                code["verification_url"],
                code["user_code"],
                code["device_code"],
                code["interval"],
            )
        except Exception as e:
            self.logger.error(f"Device Code Init Failed: {e}")
            raise

    def check_oauth_poll(self, device_code: str):
        """Poll YouTube's token endpoint for the Device Flow."""
        try:
            creds = self._get_oauth_credentials()
            token = creds.token_from_code(device_code)
            if "access_token" in token:
                return token
            if token.get("error") == "authorization_pending":
                return None
            raise Exception(token.get("error_description", "Unknown error"))
        except Exception as e:
            if "authorization_pending" in str(e):
                return None
            self.logger.error(f"Device Flow Poll Failed: {e}")
            raise

    def login_with_headers(self, headers_raw: str) -> bool:
        """
        Setup authentication using browser headers or cookies.
        (Option B)
        """
        try:
            final_headers = headers_raw.strip()
            if not final_headers:
                return False

            try:
                headers_dict = json.loads(final_headers)
            except json.JSONDecodeError:
                headers_dict = {}
                lines = final_headers.splitlines()
                for line in lines:
                    if ":" in line:
                        key, val = line.split(":", 1)
                        headers_dict[key.strip()] = val.strip()
                if not headers_dict:
                    headers_dict["Cookie"] = final_headers

            # ytmusicapi requires User-Agent
            if "User-Agent" not in headers_dict:
                headers_dict["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                
            # Safely avoid OAuth detection in YTMusic.__init__
            headers_dict.pop("access_token", None)
            headers_dict.pop("refresh_token", None)

            auth_str = json.dumps(headers_dict)
            api = YTMusic(auth=auth_str)
            api.get_library_playlists(limit=1)
            
            self.save_credentials(auth_str)
            self._api = api
            return True
        except Exception as e:
            self.logger.error(f"Header login failed: {e}")
            return False

    def save_credentials(self, data: str):
        fd = os.open(CREDENTIALS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(data)

    def logout(self):
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
        self._api = None

    def get_user_info(self) -> Dict:
        try:
            api_instance = self.api
            if api_instance:
                return api_instance.get_account_info()
        except Exception as e:
            self.logger.warning(f"Could not fetch account info: {e}")
        
        return {"name": "Authenticated User"}
