from textual.screen import Screen
from textual.widgets import Button, Label, Static
from textual.containers import Vertical
from textual import work
import logging

logger = logging.getLogger(__name__)

class AccountScreen(Screen):
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
        background: $surface;
        padding: 1 2;
    }

    #title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .info-box {
        width: 100%;
        margin: 1 0;
        text-align: center;
        height: 5;
        border: tall $primary-darken-3;
        content-align: center middle;
        background: $surface-lighten-1;
    }

    Button {
        width: 100%;
        margin-top: 1;
        border: none;
        height: 3;
        text-style: bold;
        background: $primary;
        color: white;
    }
    
    Button:hover {
        background: $accent;
    }
    """

    def compose(self):
        with Vertical(id="account-container") as v:
            v.border_title = " APP INFO "
            yield Label("YOUTUBE MUSIC CLI", id="title")
            yield Static("Guest Mode Active\nNo account connected.", classes="info-box")
            yield Button("RETURN TO PLAYER", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
