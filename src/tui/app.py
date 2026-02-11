from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

ASCI_ART = """
 ███            █████████  ██████████ ██████   ██████ █████ ██████   █████ █████
░░░███         ███░░░░░███░░███░░░░░█░░██████ ██████ ░░███ ░░██████ ░░███ ░░███
  ░░░███      ███     ░░░  ░███  █ ░  ░███░█████░███  ░███  ░███░███ ░███  ░███
    ░░░███   ░███          ░██████    ░███░░███ ░███  ░███  ░███░░███░███  ░███
     ███░    ░███    █████ ░███░░█    ░███ ░░░  ░███  ░███  ░███ ░░██████  ░███
   ███░      ░░███  ░░███  ░███ ░   █ ░███      ░███  ░███  ░███  ░░█████  ░███
 ███░         ░░█████████  ██████████ █████     █████ █████ █████  ░░█████ █████
░░░            ░░░░░░░░░  ░░░░░░░░░░ ░░░░░     ░░░░░ ░░░░░ ░░░░░    ░░░░░ ░░░░░
"""

from src.api.auth import AuthManager
from src.tui.screens.login import LoginScreen
from src.tui.screens.player import PlayerScreen

class YoutubeMusicApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [("q", "quit", "Quit")]
    SCREENS = {
        "login": LoginScreen,
        "player": PlayerScreen
    }

    def compose(self) -> ComposeResult:
        yield Container(
            Static(ASCI_ART, id="ascii-art"),
            id="header-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        auth = AuthManager()
        if not auth.is_authenticated():
            self.push_screen("login")
        else:
            self.push_screen("player")


