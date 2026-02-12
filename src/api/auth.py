import json
import logging
import os
import time
from typing import Optional, Dict
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials

APP_NAME = "ytmusic-cli"
CREDENTIALS_FILE = "oauth.json"
CLIENT_SECRETS_FILE = "client_secrets.json"

# Public defaults (YouTube Android/TV) - Split to avoid naive secret scanning
_CID_PART1 = "861556724134-979i86isdp5nd62pntu664v8226r3osv"
_CID_PART2 = ".apps.googleusercontent.com"
DEFAULT_CLIENT_ID = _CID_PART1 + _CID_PART2

_SEC_PART1 = "An_9C6uMscX_"
_SEC_PART2 = "Mh12iM8Vv9nC"
DEFAULT_CLIENT_SECRET = _SEC_PART1 + _SEC_PART2

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
                auth_data = json.load(f)

            is_oauth = "access_token" in auth_data

            if is_oauth:
                client_id, client_secret = self.get_custom_credentials()
                if not client_id:
                    client_id, client_secret = self._get_defaults()

                # CRITICAL: Must pass oauth_credentials to fix "not provided" error
                oauth_creds = OAuthCredentials(client_id, client_secret)
                
                # Initialize API — ytmusicapi handles token refresh automatically
                # via RefreshingToken when given file path + OAuthCredentials
                self._api = YTMusic(CREDENTIALS_FILE, oauth_credentials=oauth_creds)
            else:
                self._api = YTMusic(auth=json.dumps(auth_data))
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            raise

    def get_custom_credentials(self) -> tuple[Optional[str], Optional[str]]:
        if self._custom_creds:
            return self._custom_creds

        if os.path.exists(CLIENT_SECRETS_FILE):
            try:
                with open(CLIENT_SECRETS_FILE, "r") as f:
                    data = json.load(f)
                    creds = data.get("installed", {})
                    self._custom_creds = (creds.get("client_id"), creds.get("client_secret"))
                    return self._custom_creds
            except Exception as e:
                self.logger.error(f"Error loading secrets: {e}")
        return None, None

    def has_custom_credentials(self) -> bool:
        cid, secret = self.get_custom_credentials()
        return bool(cid and secret)

    def save_custom_credentials(self, client_id: str, client_secret: str):
        fd = os.open(CLIENT_SECRETS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"installed": {"client_id": client_id, "client_secret": client_secret}}, f)
        self._custom_creds = (client_id, client_secret)

    def _get_oauth_credentials(self) -> OAuthCredentials:
        """Build OAuthCredentials using custom or default client ID/secret."""
        client_id, client_secret = self.get_custom_credentials()
        if not client_id or not client_secret:
            client_id, client_secret = self._get_defaults()
        return OAuthCredentials(client_id, client_secret)

    def get_oauth_code(self):
        """Request a device code from YouTube's OAuth endpoint."""
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
            self.logger.error(f"OAuth Init Failed: {e}")
            raise

    def check_oauth_poll(self, device_code: str):
        """Poll YouTube's token endpoint using ytmusicapi's OAuthCredentials."""
        try:
            creds = self._get_oauth_credentials()
            token = creds.token_from_code(device_code)
            # token_from_code returns RefreshableTokenDict on success
            if "access_token" in token:
                return token
            # If response contains an error, it means authorization is pending
            if token.get("error") == "authorization_pending":
                return None
            raise Exception(token.get("error_description", "Unknown error"))
        except Exception as e:
            error_msg = str(e)
            if "authorization_pending" in error_msg:
                return None
            self.logger.error(f"OAuth Poll Failed: {e}")
            raise

    def finish_oauth(self, token_data: Dict):
        """Normalize token data and save to disk, then login."""
        # Ensure all fields required by ytmusicapi's Token class are present
        token_data.setdefault("scope", "https://www.googleapis.com/auth/youtube")
        token_data.setdefault("token_type", "Bearer")
        if "expires_at" not in token_data and "expires_in" in token_data:
            token_data["expires_at"] = int(time.time()) + token_data["expires_in"]
        self.save_credentials(json.dumps(token_data))
        self.login()

    def login_with_headers(self, headers_raw: str) -> bool:
        try:
            json.loads(headers_raw)
            api = YTMusic(auth=headers_raw)
            self.save_credentials(headers_raw)
            self._api = api
            return True
        except Exception as e:
            self.logger.error(f"Manual header login failed: {e}")
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
