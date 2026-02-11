from textual.screen import Screen
from textual.widgets import Button, Input, Static, Label
from textual.containers import Container, Vertical
from src.api.auth import AuthManager

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
        display: none;
    }
    """

    def compose(self):
        yield Container(
            Label("Welcome to Youtube Music CLI", id="title"),
            Label("Please authenticate to continue"),
            Button("Login with Headers (Cookies)", id="btn-manual", variant="primary"),
            # Button("Login with OAuth (Coming Soon)", id="btn-oauth", disabled=True),
            Input(placeholder="Paste JSON Headers here...", id="input-headers", classes="hidden"),
            Button("Submit", id="btn-submit", classes="hidden"),
            Label("", id="error-label"),
            id="login-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-manual":
            self.query_one("#input-headers").remove_class("hidden")
            self.query_one("#btn-submit").remove_class("hidden")
            self.query_one("#btn-manual").add_class("hidden")
            
        elif event.button.id == "btn-submit":
            headers = self.query_one("#input-headers").value
            auth = AuthManager()
            if auth.login_with_headers(headers):
                self.app.switch_screen("player")
                self.app.notify("Logged in successfully!")
            else:

                err = self.query_one("#error-label")
                err.update("Invalid headers or format. Ensure it's valid JSON.")
                err.style = "display: block;"

