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

from spotify_client import SpotifyClient

ENV_PATH = Path(__file__).parent / ".env"
BROWSER_AUTH_PATH = Path(__file__).parent / "browser.json"
OAUTH_PATH = Path(__file__).parent / "oauth.json"

console = Console(force_terminal=True)


def load_config():
    load_dotenv(dotenv_path=ENV_PATH)


def get_spotify_client() -> SpotifyClient:
    """Ensures Spotify credentials are loaded and returns SpotifyClient."""
    load_config()
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id:
        client_id = Prompt.ask("[bold green]Enter your Spotify Client ID[/bold green]").strip()
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"SPOTIPY_CLIENT_ID={client_id}\n")
        os.environ["SPOTIPY_CLIENT_ID"] = client_id

    if not client_secret:
        client_secret = Prompt.ask("[bold green]Enter your Spotify Client Secret[/bold green]", password=True).strip()
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"SPOTIPY_CLIENT_SECRET={client_secret}\n")
            f.write(f"SPOTIPY_REDIRECT_URI={redirect_uri}\n")
        os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
        os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

    return SpotifyClient(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)


def ensure_ytmusic_auth() -> str:
    """Ensures YouTube Music auth file (browser.json or oauth.json) exists."""
    if BROWSER_AUTH_PATH.exists():
        return str(BROWSER_AUTH_PATH)
    if OAUTH_PATH.exists():
        return str(OAUTH_PATH)

    console.print(Panel("""[bold cyan]YouTube Music Authentication Setup[/bold cyan]

1. Open [link=https://music.youtube.com]https://music.youtube.com[/link] in your browser and log in.
2. Open Developer Tools ([bold]F12[/bold]) -> [bold]Network[/bold] tab.
3. Filter by [bold]browse[/bold] and click anywhere on the page (e.g. Home or Explore).
4. Right-click the [italic]'browse'[/italic] request -> [bold]Copy[/bold] -> [bold]Copy request headers[/bold].
""", title="🔴 YouTube Music Auth Guide", border_style="red"))

    console.print("\n[yellow]Paste your copied Request Headers below. When done, press Enter, then type 'DONE' on a new line and press Enter:[/yellow]")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "DONE":
                break
            lines.append(line)
        except EOFError:
            break
    headers_raw = "\n".join(lines)
    if not headers_raw.strip():
        console.print("[bold red]No headers provided. Exiting.[/bold red]")
        raise SystemExit(1)

    try:
        ytmusicapi.setup(filepath=str(BROWSER_AUTH_PATH), headers_raw=headers_raw)
        console.print(f"[bold green]✔ YouTube Music headers authenticated and saved to {BROWSER_AUTH_PATH.name}![/bold green]\n")
        return str(BROWSER_AUTH_PATH)
    except Exception as e:
        console.print(f"[bold red]Failed to parse headers: {e}[/bold red]")
        console.print("Please make sure you copied the request headers properly.")
        raise SystemExit(1)
