from textual.app import App
from src.api.auth import AuthManager
from src.api.client import YTMusicClient
from src.tui.screens.login import LoginScreen
from src.tui.screens.player import PlayerScreen
from src.tui.screens.account import AccountScreen

class YTMusicApp(App):
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("escape", "push_screen('account')", "Account"),
    ]

    def on_mount(self) -> None:
        self.auth = AuthManager()
        self.client = YTMusicClient(self.auth)
        
        # Define screens
        self.install_screen(LoginScreen(), name="login")
        self.install_screen(PlayerScreen(), name="player")
        self.install_screen(AccountScreen(), name="account")
        
        # Always start at Welcome Screen (Guest Mode)
        # Auth check removed to enforce Guest-Only flow
        self.push_screen("login")

    def action_quit(self) -> None:
        """Force clean exit."""
        if hasattr(self, "screen") and hasattr(self.screen, "player"):
            self.screen.player.stop()
        self.exit()

    def action_toggle_pause(self) -> None:
        """Global pause action."""
        if hasattr(self.screen, "action_toggle_pause"):
            self.screen.action_toggle_pause()
        elif hasattr(self.screen, "player"):
            self.screen.player.toggle_pause()

def run_app():
    app = YTMusicApp()
    app.run()

if __name__ == "__main__":
    run_app()
