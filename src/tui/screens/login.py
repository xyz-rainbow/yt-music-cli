from textual.screen import Screen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical
from textual import work
from src.api.auth import AuthManager
import time
import logging

# Use logger but do not configure basicConfig here
logger = logging.getLogger(__name__)

class LoginScreen(Screen):
    CSS = """
    LoginScreen {
        align: center middle;
        background: transparent;
    }
    #login-container {
        width: 60;
        height: auto;
        border: tall $accent;
        padding: 1 4;
        background: transparent;
    }
    #title {
        text-style: bold;
        color: $accent;
        text-align: center;
        width: 100%;
    }
    .subtitle {
        text-align: center;
        width: 100%;
        color: $text-muted;
        margin-bottom: 1;
    }
    Button {
        width: 100%;
        margin-top: 1;
        height: 3;
        text-style: bold;
    }
    #btn-oauth {
        background: #2196F3;
        color: white;
    }
    #btn-submit {
        background: #4CAF50;
        color: white;
    }
    Input {
        margin-top: 1;
        border: tall $primary;
    }
    #error-label {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    .step-label {
        color: $accent;
        margin-top: 1;
        text-style: bold;
    }
    """

    def compose(self):
        with Vertical(id="login-container"):
            yield Label("YOUTUBE MUSIC CLI", id="title")
            yield Label("Authentication Required", classes="subtitle")
            
            # OAuth Section
            yield Button("Login with Google", id="btn-oauth")
            
            with Vertical(id="oauth-container", classes="hidden"):
                yield Label("1. Go to URL:", classes="step-label")
                yield Input(id="url-copy", classes="copy-field", value="", disabled=True)
                yield Label("2. Enter Code:", classes="step-label")
                yield Input(id="user-code", classes="copy-field", value="", disabled=True)
                yield Label("Waiting for approval...", id="status-label")

            yield Button("Paste Headers (Advanced)", id="btn-manual-toggle")
            yield Input(placeholder="Paste JSON Headers here...", id="input-headers", classes="hidden")
            yield Button("Submit Headers", id="btn-submit", classes="hidden")
            
            yield Label("", id="error-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        logger.info(f"Button pressed: {event.button.id}")
        auth = self.app.auth
        
        if event.button.id == "btn-oauth":
            self.start_oauth_flow(auth)

        elif event.button.id == "btn-manual-toggle":
            self.query_one("#input-headers").remove_class("hidden")
            self.query_one("#btn-submit").remove_class("hidden")
            self.query_one("#btn-manual-toggle").add_class("hidden")
            
        elif event.button.id == "btn-submit":
            headers = self.query_one("#input-headers").value
            if auth.login_with_headers(headers):
                self.app.switch_screen("player")
                self.app.notify("Logged in successfully!")
            else:
                self.query_one("#error-label").update("Invalid headers.")

    @work(thread=True)
    def start_oauth_flow(self, auth):
        logger.info("Inside start_oauth_flow worker")
        try:
            # Show "Loading..." state
            logger.info("Updating UI to loading state")
            self.app.call_from_thread(self.query_one("#status-label").update, "Contacting Google...")
            self.app.call_from_thread(self.query_one("#oauth-container").remove_class, "hidden")
            
            # Run blocking network call (safe in thread worker)
            logger.info("Calling get_oauth_code")
            url, user_code, device_code, interval = auth.get_oauth_code()
            logger.info(f"Got code: {user_code}")
            
            # Update fields safely
            def update_ui():
                self.query_one("#url-copy").value = url
                self.query_one("#user-code").value = user_code
                self.query_one("#status-label").update("Waiting for approval... (Browser opened)")
                self.query_one("#btn-oauth").add_class("hidden")
            
            self.app.call_from_thread(update_ui)
            

            # Auto-open browser & Copy Code
            import webbrowser
            import pyperclip
            
            try:
                # Try Textual's clipboard first (if available in newer versions)
                if hasattr(self.app, "copy_to_clipboard"):
                     self.app.copy_to_clipboard(user_code)
                     self.app.notify("Code copied to clipboard! Browser opened.")
                else:
                     pyperclip.copy(user_code)
                     self.app.notify("Code copied to clipboard! Browser opened.")
            except Exception as e:
                logger.error(f"Clipboard error: {e}")
                self.app.notify("Could not copy automatically. Please copy the code manually from the screen.", severity="warning")
            
            webbrowser.open(url)
            
            # Start Polling Worker
            self.poll_auth_worker(auth, device_code, interval)
            
        except Exception as e:
            logger.error(f"OAuth flow error: {e}")
            def show_error():
                self.query_one("#error-label").update(f"OAuth Error: {e}")
                self.query_one("#oauth-container").add_class("hidden")
            self.app.call_from_thread(show_error)

    @work(thread=True)
    def poll_auth_worker(self, auth, device_code, interval):
        logger.info("Inside poll_auth_worker")
        
        while True:
            try:
                # Wait for interval
                time.sleep(interval + 1)
                
                # Check status (blocking call)
                token = auth.check_oauth_poll(device_code)
                
                if token:
                    auth.finish_oauth(token)
                    # UI update must be scheduled
                    self.app.call_from_thread(self.on_login_success)
                    break
                    
            except Exception as e:
                self.app.call_from_thread(self.on_oauth_error, str(e))
                break

    def on_login_success(self):
        self.app.switch_screen("player")
        self.app.notify("OAuth Login Successful!")

    def on_oauth_error(self, message):
        self.query_one("#error-label").update(f"Poll Error: {message}")
        self.query_one("#status-label").update("Login Checked Failed.")
