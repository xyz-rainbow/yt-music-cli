import asyncio
import threading
import base64
import io
import httpx
from PIL import Image
from textual import work
from textual.screen import Screen
from textual.widgets import Input, DataTable, Button, Label, Static
from textual.containers import Container, Horizontal, Vertical
from src.player.functionality import Player

class AlbumArt(Static):
    """A widget to display album art using Kitty graphics protocol."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._image_data = None
        self._last_url = None

    def set_image(self, image_bytes: bytes):
        """Process and set the image data."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Resize to fit the sidebar roughly (e.g., 300x300)
            img.thumbnail((400, 400))
            
            output = io.BytesIO()
            img.save(output, format="PNG")
            raw_data = output.getvalue()
            
            # Kitty graphics protocol escape sequence
            b64_data = base64.b64encode(raw_data).decode("ascii")
            # a=T (transfer and display), f=100 (PNG), m=0 (last chunk)
            self._image_data = f"\x1b_Gf=100,a=T,m=0;{b64_data}\x1b\\"
            self.update(" ") # Trigger a repaint
        except Exception as e:
            self.update(f"Error loading image: {e}")

    def render(self):
        if self._image_data:
            return self._image_data
        return "No Art"

class PlayerScreen(Screen):
    CSS = """
    #sidebar {
        width: 20%;
        height: 100%;
        background: $surface-darken-1;
        border-right: solid $accent;
    }
    .sidebar-title {
        text-style: bold;
        padding: 1;
        background: $accent;
        color: $text;
        text-align: center;
    }
    #playlist-list {
        height: 1fr;
        border: none;
        background: transparent;
    }
    #main-content {
        width: 50%;
        height: 100%;
    }
    #now-playing {
        width: 30%;
        height: 100%;
        background: $surface-darken-1;
        border-left: solid $accent;
        align: center middle;
        padding: 1;
    }
    AlbumArt {
        width: 100%;
        height: 15;
        border: solid $secondary;
        margin: 1 0;
        content-align: center middle;
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
    .song-title {
        text-style: bold;
        color: $accent;
        content-align: center middle;
        text-align: center;
    }
    .song-artist {
        color: $info;
        content-align: center middle;
        text-align: center;
    }
    #empty-state {
        height: 1fr;
        align: center middle;
    }
    .empty-icon {
        text-style: bold;
        color: $accent;
        height: auto;
        content-align: center middle;
        text-align: center;
        padding-bottom: 1;
    }
    .empty-title {
        text-style: bold;
        color: $primary;
        content-align: center middle;
        text-align: center;
    }
    .empty-subtitle {
        color: $text;
        content-align: center middle;
        text-align: center;
    }
    .hidden {
        display: none;
    }
    """

    def compose(self):
        yield Horizontal(
            Vertical(
                Label("LIBRARY", classes="sidebar-title"),
                Button("Search Home", id="btn-home", variant="default"),
                Label("PLAYLISTS", classes="sidebar-title"),
                DataTable(id="playlist-list"),
                id="sidebar"
            ),
            Vertical(
                Input(placeholder="Search songs...", id="search-input"),
                Container(
                    Container(
                        Label("🎵", classes="empty-icon"),
                        Label("Start Typing to Search", classes="empty-title"),
                        Label("Find your favorite songs, artists, and albums.", classes="empty-subtitle"),
                        id="empty-state"
                    ),
                    DataTable(id="results-table", classes="hidden"),
                    id="results-container"
                ),
                id="main-content"
            ),
            Vertical(
                Label("NOW PLAYING", classes="sidebar-title"),
                AlbumArt(id="album-art"),
                Label("No song selected", id="current-title", classes="song-title"),
                Label("", id="current-artist", classes="song-artist"),
                id="now-playing"
            )
        )
        yield Static("Controls: [Space] Pause | [s] Focus Search | [q] Quit", id="player-bar")

    def on_mount(self):
        self.player = Player()
        self.results_data = {}
        self.current_track_id = None # Track current song
        
        # Setup results table
        table = self.query_one("#results-table")
        table.add_columns("Title", "Artist", "Album", "Duration")
        table.cursor_type = "row"

        # Setup playlist table
        p_table = self.query_one("#playlist-list")
        p_table.add_column("My Playlists")
        p_table.cursor_type = "row"
        
        # Initialize with empty rows or a prompt
        p_table.add_row("❤️ Liked Music", key="liked")
        p_table.add_row("🔄 Refresh Lists", key="refresh")
        
        # Focus search input on start
        self.query_one("#search-input").focus()

    @work(exclusive=True)
    async def load_playlists(self):
        """Fetch playlists from YouTube Music API."""
        self.query_one("#player-bar").update("Refreshing playlists...")
        try:
            # Run in a thread to avoid blocking
            playlists = await asyncio.to_thread(self.app.client.get_library_playlists)
            p_table = self.query_one("#playlist-list")
            p_table.clear()
            
            p_table.add_row("❤️ Liked Music", key="liked")
            p_table.add_row("🔄 Refresh Lists", key="refresh")
            
            for p in playlists:
                p_table.add_row(p.get("title", "Untitled"), key=p.get("playlistId"))
            
            self.query_one("#player-bar").update("Playlists updated.")
        except Exception as e:
            self.query_one("#player-bar").update(f"Could not load playlists: {e}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id == "playlist-list":
            playlist_id = event.row_key.value
            if playlist_id == "refresh":
                self.load_playlists()
            else:
                self.load_playlist_content(playlist_id)
        elif event.data_table.id == "results-table":
            self.play_selected_song(event.row_key.value)

    @work(exclusive=True)
    async def load_playlist_content(self, playlist_id):
        """Fetch and display songs from a playlist."""
        try:
            if playlist_id == "liked":
                songs = self.app.client.get_liked_songs()
                # get_liked_songs usually returns a list or a dict with 'tracks'
                tracks = songs.get("tracks", []) if isinstance(songs, dict) else songs
            else:
                playlist_data = self.app.client.get_playlist_songs(playlist_id)
                tracks = playlist_data.get("tracks", [])

            self.results_data = {t['videoId']: t for t in tracks if 'videoId' in t}
            self.populate_table(tracks)
        except Exception as e:
            self.notify(f"Error loading playlist tracks: {e}", severity="error")

    def populate_table(self, results):
        table = self.query_one("#results-table")
        empty_state = self.query_one("#empty-state")

        table.remove_class("hidden")
        empty_state.add_class("hidden")

        table.clear()
        for song in results:
            duration = song.get("duration", "N/A")
            video_id = song.get("videoId")
            if video_id:
                artists = song.get("artists", [])
                artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
                album_name = song.get("album", {}).get("name", "Unknown") if isinstance(song.get("album"), dict) else "N/A"
                
                table.add_row(
                    song.get("title", "Unknown"),
                    artist_name,
                    album_name,
                    duration,
                    key=video_id
                )

    @work(exclusive=True)
    async def play_worker(self, url: str):
        """Play a song in a worker thread."""
        try:
            await asyncio.to_thread(self.player.play, url)
        except Exception as e:
            self.app.notify(f"Playback error: {e}", severity="error")

    @work(exclusive=True)
    async def toggle_worker(self):
        """Toggle pause in a worker thread."""
        try:
            await asyncio.to_thread(self.player.toggle_pause)
            status = await asyncio.to_thread(self.player.get_status)
            state = "Paused" if status.get("paused") else "Playing"
            self.query_one("#player-bar").update(f"Status: {state}")
        except Exception as e:
            self.app.notify(f"Toggle error: {e}", severity="error")

    def play_selected_song(self, video_id):
        """Reproducción en hilo puro de sistema para máxima fluidez de GUI."""
        # Lógica de Toggle: Si es la misma canción, pausamos/reanudamos
        if self.current_track_id == video_id:
            self.toggle_worker()
            self.query_one("#player-bar").update(f"⏯️ Toggle Play/Pause")
            return

        song = self.results_data.get(video_id)
        if not song:
            return

        self.current_track_id = video_id # Update current song
        
        self.query_one("#current-title").update(song.get("title", "Unknown"))
        artists = song.get("artists", [])
        artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
        self.query_one("#current-artist").update(artist_name)

        thumbnails = song.get("thumbnails", [])
        if thumbnails:
            self.download_art(thumbnails[-1]["url"])

        url = f"https://music.youtube.com/watch?v={video_id}"
        title = song.get('title')
        self.query_one("#player-bar").update(f"Buffering: [b]{title}[/b]...")
        
        self.play_worker(url)
        
        # Ensure focus is not lost
        self.query_one("#results-table").focus()

    def on_input_changed(self, event: Input.Changed):
        """Activate search while typing."""
        if event.input.id == "search-input":
            query = event.value
            if len(query) > 2:  # Only search if at least 3 characters
                self.run_search(query)
            elif len(query) <= 2:
                # Show empty state for short queries (unless we decide otherwise)
                # But mainly if it's cleared or very short, we reset to empty state.
                self.query_one("#results-table").add_class("hidden")
                self.query_one("#empty-state").remove_class("hidden")

    def on_key(self, event):
        """Handle navigation and auto-focus of search."""
        # Global Play/Pause shortcut with Space
        if event.key == "space":
            # If we are in the input, allow typing spaces
            if self.focused and self.focused.id == "search-input":
                return
            
            self.toggle_worker()
            event.prevent_default()
            return

        # If an alphanumeric key is pressed and no input is focused, focus search
        if event.is_printable and len(event.key) == 1:
            if not (self.focused and isinstance(self.focused, (Input))):
                self.query_one("#search-input").focus()

        # Navigation from search to table
        if self.focused and self.focused.id == "search-input":
            if event.key == "down":
                table = self.query_one("#results-table")
                if not table.has_class("hidden"):
                    table.focus()
                event.prevent_default()
            elif event.key == "escape":
                table = self.query_one("#results-table")
                if not table.has_class("hidden"):
                    table.focus()
                event.prevent_default()

    def on_input_submitted(self, event: Input.Submitted):
        """Keep Enter support, but actual search happens in on_input_changed."""
        if event.input.id == "search-input":
            self.run_search(event.value)

    @work(exclusive=True)
    async def run_search(self, query):
        if not query.strip():
            return
            
        self.query_one("#player-bar").update(f"🔍 Searching for '{query}'...")
        table = self.query_one("#results-table")
        table.loading = True  # Native Textual loading visual effect
        
        try:
            # Run search in a thread to avoid blocking the event loop
            results = await asyncio.to_thread(self.app.client.search_songs, query)
            
            self.results_data = {song['videoId']: song for song in results if 'videoId' in song}
            self.populate_table(results)
            self.query_one("#player-bar").update(f"Found {len(results)} results for '{query}'")
        except Exception as e:
            self.query_one("#player-bar").update(f"Search error: {e}")
        finally:
            table.loading = False

    def key_s(self):
        self.query_one("#search-input").focus()

    def action_quit(self):
        self.player.stop()
        self.app.exit()

    def key_q(self):
        self.action_quit()

    @work(exclusive=True)
    async def download_art(self, url: str):
        """Download album art asynchronously."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    self.query_one(AlbumArt).set_image(response.content)
            except Exception as e:
                self.query_one("#player-bar").update(f"Error downloading art: {e}")

    def action_toggle_pause(self):
        self.toggle_worker()

    def key_space(self):
        self.action_toggle_pause()
