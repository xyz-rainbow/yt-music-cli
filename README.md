<p align="center">
<pre>
 ███  ███ █████████          ██████   ██████ ███    ███  █████████ ███  █████████
░░███░███░░░░███░░░         ░░██████ ██████ ░███   ░███ ░███░░░░░░ ░███ ░███░░░░░░
 ░░█████     ░███            ░███░█████░███ ░███   ░███ ░███       ░███ ░███
  ░░███      ░███   ███████  ░███░░███ ░███ ░███   ░███ ░█████████ ░███ ░███
   ░███      ░███  ░░░░░░░   ░███ ░░░  ░███ ░███   ░███ ░░░░░░░███ ░███ ░███
   ░███      ░███            ░███      ░███ ░░███ ███░  █████████  ░███ ░███
   █████     █████           █████     █████ ░░█████░  ░█████████  █████░█████████
  ░░░░░     ░░░░░           ░░░░░     ░░░░░   ░░░░░    ░░░░░░░░░  ░░░░░ ░░░░░░░░░
</pre>
</p>

<p align="center">
  <strong>🎵 YouTube Music in your terminal. No browser required.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/TUI-Textual-FF3333?logo=gnometerminal&logoColor=white" alt="Textual"></a>
  <a href="https://mpv.io/"><img src="https://img.shields.io/badge/Audio-mpv-690DAD" alt="mpv"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
</p>

---

A **lightweight, powerful, and minimalist** YouTube Music player for the terminal. Industrial-modern TUI built with [Textual](https://textual.textualize.io/), audio powered by [mpv](https://mpv.io/), and YouTube Music integration via [ytmusicapi](https://github.com/sigma67/ytmusicapi).

## ✨ Features

- 🔍 **Smart Search** — Instant results with title & artist columns
- 🏠 **Home Recommendations** — Personalized suggestions from YouTube Music
- 🖼️ **Album Art** — High-resolution cover art via ANSI block rendering
- 📂 **Queue Management** — Add songs without interrupting playback
- ❤️ **Favorites** — Like/unlike songs synced to your YT Music library
- 🔊 **Volume Control** — Fine-grained adjustment with visual feedback
- 🔐 **Google OAuth Login** — One-click device code authentication
- 🌓 **Transparency** — Respects your terminal's transparency & blur settings

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Play selected song |
| `Space` | Pause / Resume |
| `Alt+Enter` | Add to queue |
| `Alt+Backspace` | Remove last from queue |
| `Alt+→` / `Alt+←` | Next / Previous in queue |
| `→` / `←` | Seek ±10 seconds |
| `Alt+↑` / `Alt+↓` | Volume ±5% |
| `Alt+F` | Like / Unlike song |
| `Alt+H` | Home recommendations |
| `Alt+S` | Focus search bar |
| `Esc` | Account screen |
| `Q` | Quit |

## 📦 Requirements

| Dependency | Purpose |
|------------|---------|
| **Python 3.10+** | Runtime |
| **[mpv](https://mpv.io/)** | Audio playback engine (must be in `PATH`) |
| **A modern terminal** | Ghostty, Kitty, WezTerm, Alacritty, etc. |

## 🚀 Installation

```bash
# Clone
git clone https://github.com/xyz-rainbow/yt-music-cli.git
cd yt-music-cli

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

### Install mpv (if not already installed)

```bash
# Debian/Ubuntu
sudo apt install mpv

# Arch
sudo pacman -S mpv

# macOS
brew install mpv
```

## ▶️ Usage

```bash
# Run the app
yt-music

# Or directly with Python
python main.py
```

### Authentication (Recommended)

Google has restricted the public OAuth flow for many users. The most reliable way to login is **Browser Authentication**:

1. Open **music.youtube.com** in your browser.
2. Open Developer Tools (`F12`), go to the **Network** tab, and refresh the page.
3. Look for a request to `music.youtube.com`, find the **Cookie** header in the request headers, and copy its value.
4. In **yt-music-cli**, paste the cookie string into the login screen and press Enter.

---
**Note**: Legacy "Login with Google" is still available but may require you to configure your own Google Cloud project if it fails with an `invalid_client` error.


## 🏗️ Project Structure

```
yt-music-cli/
├── main.py                  # Entry point
├── pyproject.toml           # Package config
├── src/
│   ├── api/
│   │   ├── auth.py          # OAuth & authentication
│   │   └── client.py        # YouTube Music API client
│   ├── player/
│   │   └── functionality.py # mpv playback engine
│   └── tui/
│       ├── app.py           # Textual app root
│       ├── styles.css       # TUI theme
│       └── screens/
│           ├── login.py     # Login screen
│           ├── player.py    # Main player screen
│           └── account.py   # Account management
└── styles.css               # Global styles
```

## ⚠️ Known Limitations

- **OAuth search fallback**: Due to a [known ytmusicapi bug](https://github.com/sigma67/ytmusicapi/issues), some OAuth client types receive HTTP 400 on search. The app automatically falls back to unauthenticated search, which works without issues.
- **Library operations**: Playlist and like sync may be affected by the same upstream OAuth bug.

## 📄 License

[MIT](LICENSE) © 2026

---

<p align="center">
  Built with ❤️ for terminal lovers.
</p>
