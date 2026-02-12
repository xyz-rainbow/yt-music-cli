from textual.screen import Screen
from textual.widgets import Button, Label, Static
from textual.containers import Vertical
from textual import work
import logging

logger = logging.getLogger(__name__)

class AccountScreen(Screen):
    CSS = """
    AccountScreen {
        align: center middle;
        background: transparent;
    }

    #account-container {
        width: 60;
        height: auto;
        border: tall $accent;
        background: transparent;
        padding: 1 2;
    }

    #title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .account-info {
        width: 100%;
        margin: 1 0;
        text-align: center;
        height: 5;
        border: tall $primary-darken-3;
        content-align: center middle;
        background: $surface;
    }

    .user-name {
        text-style: bold;
        color: $accent;
    }

    Button {
        width: 100%;
        margin: 0;
        border: none;
        height: 3;
        text-style: bold;
    }

    #btn-player {
        background: #2E7D32; /* Material Green 800 */
        margin-top: 1;
        color: white;
    }
    
    #btn-relogin {
        background: #F57C00; /* Material Orange 700 */
        color: white;
    }

    #btn-logout {
        background: #C62828; /* Material Red 800 */
        color: white;
    }

    Button:hover {
        background: $accent;
        color: white;
    }
    
    .status-msg {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self):
        with Vertical(id="account-container") as v:
            v.border_title = " SESSION CONTROL "
            yield Label("YOUTUBE MUSIC CLI", id="title")
            yield Static("🔄 Syncing profile...", id="user-info-display", classes="account-info")
            yield Button("PROCEED TO PLAYER", id="btn-player")
            yield Button("SWITCH ACCOUNT", id="btn-relogin")
            yield Button("LOGOUT", id="btn-logout")
            yield Static("Press [[Esc]] to return here anytime", classes="status-msg")

    def on_mount(self):
        self.load_user_info()

    @work(thread=True)
    def load_user_info(self):
        try:
            # First ensure we are actually authenticated
            if not self.app.auth.is_authenticated():
                self.app.call_from_thread(self.query_one("#user-info-display").update, "[red]Session expired.[/red]")
                return

            info = self.app.auth.get_user_info()
            name = info.get("name", "Authenticated User")
            account_name = info.get("accountName", "")
            
            display_text = f"Logged in as:\n[b class='user-name']{name}[/b]"
            if account_name:
                display_text += f"\n{account_name}"
                
            self.app.call_from_thread(self.query_one("#user-info-display").update, display_text)
        except Exception as e:
            logger.error(f"Error loading user info: {e}")
            self.app.call_from_thread(self.query_one("#user-info-display").update, "[yellow]Session Active\n(User data restricted)[/yellow]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-player":
            self.app.push_screen("player")
        elif event.button.id == "btn-relogin":
            self.app.push_screen("login")
        elif event.button.id == "btn-logout":
            self.app.auth.logout()
            self.app.switch_screen("login")
            self.app.notify("Logged out successfully.")
