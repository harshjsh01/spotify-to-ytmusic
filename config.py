import os
import json
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import ytmusicapi

from spotify_client import SpotifyNoDevClient

ENV_PATH = Path(__file__).parent / ".env"
SPOTIFY_JSON_PATH = Path(__file__).parent / "spotify_data.json"
BROWSER_AUTH_PATH = Path(__file__).parent / "browser.json"
OAUTH_PATH = Path(__file__).parent / "oauth.json"

console = Console()


def load_config():
    load_dotenv(dotenv_path=ENV_PATH)


def get_spotify_client() -> SpotifyNoDevClient:
    """Sets up Spotify client using JSON export or sp_dc session cookie (No Developer App needed!)."""
    load_config()

    # 1. Check if spotify_data.json already exists
    if SPOTIFY_JSON_PATH.exists():
        console.print(f"[bold green]✔ Found '{SPOTIFY_JSON_PATH.name}'! Loading your Spotify library...[/bold green]")
        with open(SPOTIFY_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SpotifyNoDevClient(json_data=data)

    # 2. Check if SP_DC is stored in .env
    sp_dc = os.getenv("SPOTIFY_SP_DC")
    if sp_dc:
        try:
            return SpotifyNoDevClient(sp_dc=sp_dc)
        except Exception as e:
            console.print(f"[yellow]Stored session expired ({e}). Re-authenticating...[/yellow]")

    console.print(Panel("""[bold cyan]Spotify Connection (No Developer App / No Premium Needed)[/bold cyan]

Choose how you want to connect your Spotify library:

[bold green]Option 1: 1-Click Browser Extractor (Easiest & Recommended)[/bold green]
1. Open [bold]open.spotify.com[/bold] in your browser and log in.
2. Press [bold]F12[/bold] (or right click -> Inspect) -> go to the [bold]Console[/bold] tab.
3. Paste the provided extractor script and press [bold]Enter[/bold].
4. It will automatically download [bold yellow]'spotify_data.json'[/bold yellow].
5. Move [bold yellow]'spotify_data.json'[/bold yellow] into this folder!

[bold green]Option 2: Direct Cookie Login (sp_dc)[/bold green]
1. Open [bold]open.spotify.com[/bold] in your browser.
2. Press [bold]F12[/bold] -> [bold]Application[/bold] tab (or [bold]Storage[/bold] in Firefox) -> [bold]Cookies[/bold] -> [italic]https://open.spotify.com[/italic].
3. Find the cookie named [bold yellow]'sp_dc'[/bold yellow] and copy its value.
""", title="🎵 Spotify Setup", border_style="green"))

    choice = Prompt.ask("Choose Spotify method", choices=["1", "2"], default="1")

    if choice == "1":
        console.print("\n[bold yellow]Copy and run the JavaScript snippet located in 'export_spotify_bookmarklet.js' inside your browser console on open.spotify.com.[/bold yellow]")
        Prompt.ask("\nOnce 'spotify_data.json' is placed in this folder, press [bold green]Enter[/bold green] to continue")
        if SPOTIFY_JSON_PATH.exists():
            with open(SPOTIFY_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SpotifyNoDevClient(json_data=data)
        else:
            console.print(f"[bold red]Could not find '{SPOTIFY_JSON_PATH.name}'. Please make sure it is in this folder.[/bold red]")
            raise SystemExit(1)
    else:
        sp_dc = Prompt.ask("\n[bold green]Paste your 'sp_dc' cookie value[/bold green]").strip()
        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"\nSPOTIFY_SP_DC={sp_dc}\n")
        return SpotifyNoDevClient(sp_dc=sp_dc)


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
