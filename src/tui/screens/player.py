from textual.screen import Screen
from textual.widgets import Header, Footer, Input, DataTable, Button, Label, Static
from textual.containers import Container, Horizontal, Vertical
from textual import work
from src.api.client import YTMusicClient
from src.player.functionality import Player

class PlayerScreen(Screen):
    CSS = """
    #sidebar {
        width: 20%;
        height: 100%;
        background: $surface-darken-1;
        border-right: solid $accent;
    }
    #main-content {
        width: 80%;
        height: 100%;
    }
    #player-bar {
        height: 3;
        dock: bottom;
        background: $secondary;
        color: $text;
        content-align: center middle;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("space", "toggle_pause", "Pause/Resume"),
    ]

    def compose(self):
        yield Horizontal(
            Vertical(
                Label("Library", classes="sidebar-title"),
                Button("Home", id="btn-home"),
                Button("Search", id="btn-search"),
                id="sidebar"
            ),
            Vertical(
                Input(placeholder="Search...", id="search-input"),
                DataTable(id="results-table"),
                id="main-content"
            )
        )
        yield Static("Player Controls [Space: Pause] [q: Quit]", id="player-bar")

    def on_mount(self):
        self.player = Player()
        table = self.query_one(DataTable)
        table.add_columns("Title", "Artist", "Album", "Duration")

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "search-input":
            query = event.value
            self.perform_search(query)

    @work(thread=True)
    def perform_search(self, query):
        try:
            # client.search_songs performs network I/O.
            results = self.app.client.search_songs(query)

            # Update UI in main thread
            self.app.call_from_thread(self.populate_table, results)
        except Exception as e:
            def show_error():
                self.app.notify(f"Search failed: {e}", severity="error")
            self.app.call_from_thread(show_error)

    def populate_table(self, results):
        table = self.query_one(DataTable)
        table.clear()
        for song in results:
            duration = song.get("duration", "N/A")
            video_id = song.get("videoId")
            if video_id:
                table.add_row(
                    song.get("title", "Unknown"),
                    ", ".join([a["name"] for a in song.get("artists", [])]),
                    song.get("album", {}).get("name", "Unknown"),
                    duration,
                    key=video_id
                )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        video_id = event.row_key.value
        url = f"https://music.youtube.com/watch?v={video_id}"
        try:
            self.player.play(url)
            self.query_one("#player-bar").update(f"Playing: {video_id}...")
        except Exception as e:
            self.app.notify(f"Playback error: {e}", severity="error")

    def action_toggle_pause(self):
        if not hasattr(self, 'player'):
            return

        self.player.pause()
        status = self.player.get_status()
        state = status.get("state", "Unknown")
        paused = status.get("paused", False)

        display_state = "Paused" if paused else state
        self.query_one("#player-bar").update(f"State: {display_state}")
