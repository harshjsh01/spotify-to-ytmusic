import os
import sys
import json
from pathlib import Path

# Force UTF-8 for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import ytmusicapi

from spotify_client import SpotifyWebClient

ENV_PATH = Path(__file__).parent / ".env"
SPOTIFY_JSON_PATH = Path(__file__).parent / "spotify_data.json"
LIKED_SONG_PATH = Path(__file__).parent / "liked_song_data.json"
DATA_LIKED_SONG_PATH = Path(__file__).parent / "data" / "liked_song_data.json"
ARTISTS_PATH = Path(__file__).parent / "artists_data.json"
DATA_ARTISTS_PATH = Path(__file__).parent / "data" / "artists_data.json"
BROWSER_AUTH_PATH = Path(__file__).parent / "browser.json"
OAUTH_PATH = Path(__file__).parent / "oauth.json"

console = Console(force_terminal=True)


def load_config():
    load_dotenv(dotenv_path=ENV_PATH)


def get_spotify_client() -> SpotifyWebClient:
    """Sets up Spotify client using JSON export or Web Player Bearer token."""
    load_config()

    # 1. Check if artists_data.json or liked_song_data.json exists
    if DATA_ARTISTS_PATH.exists():
        console.print(f"[bold green]✔ Found '{DATA_ARTISTS_PATH}'! Loading artists...[/bold green]")
        return SpotifyWebClient(json_file=str(DATA_ARTISTS_PATH))

    if ARTISTS_PATH.exists():
        console.print(f"[bold green]✔ Found '{ARTISTS_PATH.name}'! Loading artists...[/bold green]")
        return SpotifyWebClient(json_file=str(ARTISTS_PATH))

    if DATA_LIKED_SONG_PATH.exists():
        console.print(f"[bold green]✔ Found '{DATA_LIKED_SONG_PATH}'! Loading library...[/bold green]")
        return SpotifyWebClient(json_file=str(DATA_LIKED_SONG_PATH))

    if LIKED_SONG_PATH.exists():
        console.print(f"[bold green]✔ Found '{LIKED_SONG_PATH.name}'! Loading library...[/bold green]")
        return SpotifyWebClient(json_file=str(LIKED_SONG_PATH))

    if SPOTIFY_JSON_PATH.exists():
        console.print(f"[bold green]✔ Found '{SPOTIFY_JSON_PATH.name}'! Loading library...[/bold green]")
        return SpotifyWebClient(json_file=str(SPOTIFY_JSON_PATH))

    # 2. Check if token in .env
    token = os.getenv("SPOTIFY_BEARER_TOKEN")
    if token:
        client = SpotifyWebClient(token=token)
        count = client.get_liked_tracks_count()
        if count > 0:
            return client

    console.print(Panel("""[bold cyan]Spotify Authorization (No Developer App / No Premium Needed)[/bold cyan]

How to get your Spotify Web token in 5 seconds:
1. Open [bold]open.spotify.com[/bold] in Chrome/Edge/Firefox.
2. Press [bold]F12[/bold] (DevTools) -> click the [bold]Network[/bold] tab.
3. In the filter box, type [bold]pathfinder[/bold] (or [bold]query[/bold]).
4. Click on [bold]"Liked Songs"[/bold] in your Spotify left sidebar.
5. Click any request that appears -> scroll down to [bold]Request Headers[/bold] -> copy the [bold yellow]Authorization[/bold yellow] header value (starts with `Bearer BQ...`).
""", title="🎵 Spotify Web Token", border_style="green"))

    token = Prompt.ask("[bold green]Paste your Spotify Authorization Bearer token[/bold green]").strip()
    with open(ENV_PATH, "a", encoding="utf-8") as f:
        f.write(f"\nSPOTIFY_BEARER_TOKEN={token}\n")

    return SpotifyWebClient(token=token)


def ensure_ytmusic_auth() -> str:
    """Ensures YouTube Music auth file exists."""
    if BROWSER_AUTH_PATH.exists():
        return str(BROWSER_AUTH_PATH)
    if OAUTH_PATH.exists():
        return str(OAUTH_PATH)

    console.print("[bold red]YouTube Music authentication (browser.json) is missing.[/bold red]")
    raise SystemExit(1)
