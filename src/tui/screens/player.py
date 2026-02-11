from textual.screen import Screen
from textual.widgets import Header, Footer, Input, DataTable, Button, Label, Static
from textual.containers import Container, Horizontal, Vertical
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
            results = self.app.client.search_songs(query)
            self.populate_table(results)

    def populate_table(self, results):
        table = self.query_one(DataTable)
        table.clear()
        for song in results:
            # Safely get duration, sometimes it's missing
            duration = song.get("duration", "N/A")
            # Store full song data in the row key or checking ID
            # For now row_key is videoId
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
        # In a real app we need to get the streaming URL. 
        # mpv with ytdl=True can often handle "https://music.youtube.com/watch?v=VIDEO_ID"
        url = f"https://music.youtube.com/watch?v={video_id}"
        self.player.play(url)
        self.query_one("#player-bar").update(f"Playing: {video_id}...")

