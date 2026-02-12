from textual.screen import Screen
from textual.widgets import Button, Input, Label, TextArea
from textual.containers import Vertical
from textual import work
from src.api.auth import AuthManager
import time
import logging
import pyperclip
import webbrowser
import os
import json

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
        background: $surface-lighten-1;
        color: white;
        border: none;
    }
    #btn-paste {
        background: $accent;
        color: white;
        height: 3;
        margin-top: 1;
    }
    Input {
        margin-top: 1;
        border: tall $primary;
    }
    .instructions {
        margin: 1 0;
        color: $text-muted;
        height: auto;
    }
    .step {
        color: $accent;
        text-style: bold;
    }
    #error-label {
        color: $error;
        text-align: center;
        margin-top: 1;
        height: auto;
    }
    #code-display {
        text-align: center;
        width: 100%;
        height: 3;
        background: $surface-lighten-1;
        color: $accent;
        text-style: bold;
        border: double $accent;
        margin: 1 0;
        content-align: center middle;
    }
    .hidden {
        display: none;
    }
    """


    def compose(self):
        with Vertical(id="login-container"):
            yield Label("YOUTUBE MUSIC CLI [v2 INFALLIBLE]", id="title")
            yield Label("Authentication Required", classes="subtitle")
            
            # The Main and only Button the user should need
            yield Button("Login with Google", id="btn-oauth", variant="primary")
            
            # Additional fallback option for local browser flow
            yield Button("Try Browser Redirect (if above fails)", id="btn-local-flow", variant="default", classes="hidden")
            
            with Vertical(id="oauth-container", classes="hidden"):
                yield Label("Mete este código en el navegador:", id="status-label")
                yield Label("", id="code-display") # removed classes="hidden" to ensure it's there
                yield Button("COPIAR CÓDIGO", id="btn-copy-code", variant="success")
                yield Label("Se ha intentado copiar automáticamente.", classes="step-label")
                yield Label("Si no se abre, ve a: https://www.google.com/device", classes="instructions")
            
            yield Label("──────────────────────────────────────", classes="subtitle")

            # Minimal fallbacks hidden away
            yield Button("Show Cookies Login (Option B)", id="btn-toggle-advanced")
            with Vertical(id="advanced-container", classes="hidden"):
                yield Label("Paste Browser Data (Cookies)", classes="step-label")
                yield TextArea(id="input-headers")
                yield Button("Login with Cookies", id="btn-submit-cookies")

            yield Label("", id="error-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        auth = self.app.auth
        
        if event.button.id == "btn-oauth":
            # Clear previous errors
            self.query_one("#error-label").update("")
            # We pivot the main button to the infallible Device Flow
            self.start_device_flow(auth)
        
        elif event.button.id == "btn-copy-code":
            code = self.query_one("#code-display").renderable
            self.copy_code_to_clipboard(str(code))

        elif event.button.id == "btn-local-flow":
            self.run_local_flow(auth)

        elif event.button.id == "btn-toggle-advanced":
            container = self.query_one("#advanced-container")
            if "hidden" in container.classes:
                container.remove_class("hidden")
            else:
                container.add_class("hidden")

        elif event.button.id == "btn-submit-cookies":
            cookies = self.query_one("#input-headers").text
            if auth.login_with_headers(cookies):
                self.app.switch_screen("player")
                self.app.notify("Logged in successfully via Cookies!")
            else:
                self.query_one("#error-label").update("Failed to login. Verify cookies/headers.")

    @work(thread=True)
    def start_device_flow(self, auth):
        """Starts the standard and infallible Google Device Code flow."""
        try:
            # UI setup
            self.app.call_from_thread(self.query_one("#oauth-container").remove_class, "hidden")
            self.app.call_from_thread(self.query_one("#btn-oauth").add_class, "hidden")
            self.app.call_from_thread(self.query_one("#status-label").update, "Connecting to Google...")
            
            # Use the infallible method (Public ID + Device Flow)
            url, user_code, device_code, interval = auth.start_google_login()
            
            def update_ui_and_actions():
                # Show the code prominently
                code_lbl = self.query_one("#code-display")
                code_lbl.update(user_code)
                code_lbl.remove_class("hidden")
                
                self.query_one("#status-label").update("Please enter this code:")
                
                # 1. Copy BOTH Code and URL to clipboard if possible
                self.copy_code_to_clipboard(user_code)
                
                # 2. Open browser SECOND with redundant fallbacks
                try:
                    opened = webbrowser.open(url)
                    if not opened:
                         # Fallback for some Linux environments
                         os.system(f"xdg-open '{url}' &")
                except Exception as e:
                    logger.warning(f"Browser open failed: {e}")
                    self.app.notify("Could not open browser. Please visit the link above.", severity="error")

            self.app.call_from_thread(update_ui_and_actions)
            
            # Polling for success
            while True:
                time.sleep(interval + 1)
                token = auth.check_oauth_poll(device_code)
                if token:
                    auth.save_credentials(json.dumps(token))
                    auth.login()
                    self.app.call_from_thread(self.on_login_success)
                    break
        except Exception as e:
            self.app.call_from_thread(self.on_oauth_error, f"{e}")

    def copy_code_to_clipboard(self, code: str):
        """Attempts to copy to clipboard using multiple fallbacks."""
        import base64
        import sys
        
        # 1. Try Pyperclip (standard)
        try:
            import pyperclip
            pyperclip.copy(code)
            self.app.notify("¡Copiado al portapapeles!", severity="information")
            return
        except Exception:
            pass

        # 2. Try OSC 52 (Terminal fallback - works in VS Code, Kitty, etc.)
        try:
            base64_payload = base64.b64encode(code.encode('utf-8')).decode('utf-8')
            osc52 = f"\x1b]52;c;{base64_payload}\x1b\\"
            
            # Using Textual's console for better compatibility with its driver
            from rich.control import Control
            self.app.console.control(Control.from_string(osc52))
            self.app.notify("Copiado vía Terminal (OSC 52)", severity="information")
        except Exception as e:
            logger.warning(f"OSC52 failed: {e}")
            # Final fallback: print it so it's in the terminal history if possible
            # (though in Textual this might be hidden)
            self.app.notify("No se pudo copiar automáticamente.", severity="error")

    @work(thread=True)
    def run_local_flow(self, auth):
        """Runs the Local App Flow (OAuth Redirect)."""
        try:
            self.app.call_from_thread(self.query_one("#status-label").update, "Opening browser for redirect...")
            if auth.start_local_oauth_flow():
                self.app.call_from_thread(self.on_login_success)
        except Exception as e:
            self.app.call_from_thread(self.on_oauth_error, f"Local flow failed: {e}")

    def on_login_success(self):
        self.app.switch_screen("player")
        self.app.notify("Login Successful!")

    def on_oauth_error(self, message):
        """Display error and allow retry."""
        tip = "Si tienes un error 401/403, asegúrate de que la 'YouTube Data API v3' esté activada."
        if "Pyperclip" in message or "copy/paste mechanism" in message:
            tip = "No tienes instalado un gestor de portapapeles en Linux. Prueba a instalar 'xclip' (`sudo apt install xclip`) o usa el código de arriba manualmente."
        
        self.query_one("#error-label").update(f"ERROR: {message}\n\n[u]Tip:[/u] {tip}")
        self.query_one("#status-label").update("Failed to login.")
        self.query_one("#btn-oauth").remove_class("hidden")
        self.query_one("#btn-local-flow").remove_class("hidden")
        self.query_one("#oauth-container").add_class("hidden")
