from textual.screen import Screen
from textual.widgets import Button, Input, Static, Label, Header, Footer
from textual.containers import Container, Vertical
from textual import work
from src.api.auth import AuthManager
import logging

# Use logger but do not configure basicConfig here
logger = logging.getLogger(__name__)

class LoginScreen(Screen):
    CSS = """
    LoginScreen {
        align: center middle;
    }
    #login-container {
        width: 60;
        height: auto;
        border: solid $accent;
        padding: 2;
        background: $surface;
    }
    Button {
        width: 100%;
        margin-top: 1;
    }
    Input {
        margin-top: 1;
    }
    #error-label {
        color: $error;
        text-align: center;
        /* display: none;  <-- REMOVE THIS to ensure we see errors if they occur contextually, or handle via class */
    }
    """

    def compose(self):
        yield Container(
            Label("Welcome to Youtube Music CLI", id="title"),
            Label("Please Login", classes="subtitle"),
            
            # OAuth Section
            Button("Login with Google", id="btn-oauth", variant="primary"),
            
            Container(
                Label("Setup Custom API Credentials", classes="step-label"),
                Input(placeholder="Client ID", id="input-client-id"),
                Input(placeholder="Client Secret", id="input-client-secret", password=True),
                Button("Save & Login", id="btn-save-custom", variant="warning"),
                id="custom-api-container",
                classes="hidden"
            ),

            Container(
                Label("1. Go to URL:", classes="step-label"),
                Input(id="url-copy", classes="copy-field", value="", disabled=True),
                Label("2. Enter Code:", classes="step-label"),
                Input(id="user-code", classes="copy-field", value="", disabled=True),
                Label("Waiting for approval...", id="status-label"),
                id="oauth-container",
                classes="hidden"
            ),

            Button("Configure API Keys", id="btn-config"),
            Button("Paste Headers (Advanced)", id="btn-manual-toggle"),
            Input(placeholder="Paste JSON Headers here...", id="input-headers", classes="hidden"),
            Button("Submit Headers", id="btn-submit", classes="hidden"),
            
            Label("", id="error-label"),
            id="login-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        logger.info(f"Button pressed: {event.button.id}")
        auth = self.app.auth
        
        if event.button.id == "btn-oauth":
            # Check if we have custom credentials saved or loaded
            if auth.has_custom_credentials():
                 self.start_oauth_flow(auth)
            else:
                 self.query_one("#custom-api-container").remove_class("hidden")
                 self.query_one("#btn-oauth").add_class("hidden")
                 self.query_one("#btn-config").add_class("hidden")
                 self.app.notify("Please enter your Google Cloud Client ID/Secret first.")

        elif event.button.id == "btn-config":
             self.query_one("#custom-api-container").remove_class("hidden")
             self.query_one("#btn-oauth").add_class("hidden")
             self.query_one("#btn-config").add_class("hidden")
             
        elif event.button.id == "btn-save-custom":
            client_id = self.query_one("#input-client-id").value
            client_secret = self.query_one("#input-client-secret").value
            
            if client_id and client_secret:
                auth.save_custom_credentials(client_id, client_secret)
                self.app.notify("Credentials Saved!")
                self.start_oauth_flow(auth)
            else:
                self.query_one("#error-label").update("Client ID and Secret required.")

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
            
            # Auto-open browser
            try:
                import webbrowser
                webbrowser.open(url)
                self.app.notify("Browser opened! Please enter the code.")
            except Exception as e:
                logger.warning(f"Failed to open browser: {e}")
                self.app.notify(f"Please open {url} manually", severity="warning")
            
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
        import time
        logger.info("Inside poll_auth_worker")
        import time
        
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
