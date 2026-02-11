from textual.app import App
from src.api.auth import AuthManager
from src.api.client import YTMusicClient
from src.tui.screens.login import LoginScreen
from src.tui.screens.player import PlayerScreen

class YTMusicApp(App):
    CSS_PATH = "styles.css"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def on_mount(self) -> None:
        self.auth = AuthManager()
        self.client = YTMusicClient(self.auth)
        
        # Define screens
        self.install_screen(LoginScreen(), name="login")
        self.install_screen(PlayerScreen(), name="player")
        
        # Check authentication and route
        if self.auth.is_authenticated():
            self.push_screen("player")
        else:
            self.push_screen("login")

if __name__ == "__main__":
    app = YTMusicApp()
    app.run()
