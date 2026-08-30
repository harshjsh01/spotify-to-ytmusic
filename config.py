import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import ytmusicapi

ENV_PATH = Path(__file__).parent / ".env"
BROWSER_AUTH_PATH = Path(__file__).parent / "browser.json"
OAUTH_PATH = Path(__file__).parent / "oauth.json"

console = Console()


def load_config():
    load_dotenv(dotenv_path=ENV_PATH)


def ensure_spotify_credentials() -> tuple[str, str, str]:
    """Ensures Spotify Client ID & Secret are available."""
    load_config()
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        console.print(Panel("""[bold cyan]Spotify Developer Credentials Setup[/bold cyan]

To read your Spotify library, playlists, and artists, you need Spotify API keys:
1. Open: [link=https://developer.spotify.com/dashboard]https://developer.spotify.com/dashboard[/link]
2. Log in and click [bold green]'Create app'[/bold green].
3. App name: [yellow]MusicMigrator[/yellow] (or any name).
4. App description: [yellow]Migrate Spotify to YouTube Music[/yellow].
5. Redirect URI: [bold magenta]http://127.0.0.1:8888/callback[/bold magenta] (Add this exact URL!).
6. Check [italic]Web API[/italic], agree to terms, and click [bold green]Save[/bold green].
7. Go to [bold]Settings[/bold] in your new app and copy the [bold]Client ID[/bold] and [bold]Client Secret[/bold].
""", title="🎵 Spotify Setup Guide", border_style="green"))

        client_id = Prompt.ask("[bold green]Enter your Spotify Client ID[/bold green]").strip()
        client_secret = Prompt.ask("[bold green]Enter your Spotify Client Secret[/bold green]", password=True).strip()

        with open(ENV_PATH, "a", encoding="utf-8") as f:
            f.write(f"\nSPOTIPY_CLIENT_ID={client_id}\n")
            f.write(f"SPOTIPY_CLIENT_SECRET={client_secret}\n")
            f.write(f"SPOTIPY_REDIRECT_URI={redirect_uri}\n")

        os.environ["SPOTIPY_CLIENT_ID"] = client_id
        os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
        os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri
        console.print("[bold green]✔ Spotify credentials saved to .env![/bold green]\n")

    return client_id, client_secret, redirect_uri


def ensure_ytmusic_auth() -> str:
    """Ensures YouTube Music auth file (browser.json or oauth.json) exists."""
    if BROWSER_AUTH_PATH.exists():
        return str(BROWSER_AUTH_PATH)
    if OAUTH_PATH.exists():
        return str(OAUTH_PATH)

    console.print(Panel("""[bold cyan]YouTube Music Authentication Setup[/bold cyan]

YouTube Music requires authentication to like songs, subscribe to artists, and create playlists.

[bold yellow]Option 1: Fast Browser Headers Setup (Recommended)[/bold yellow]
1. Open [bold]Google Chrome[/bold] / [bold]Firefox[/bold] / [bold]Edge[/bold] and navigate to [link=https://music.youtube.com]https://music.youtube.com[/link].
2. Make sure you are logged into your Google / YouTube account.
3. Open Developer Tools ([bold]F12[/bold] or [bold]Ctrl + Shift + I[/bold]) and go to the [bold]Network[/bold] tab.
4. Filter by [bold]browse[/bold] or click on any playlist / home icon on the page.
5. Right-click any POST request to [italic]music.youtube.com[/italic] (e.g., `browse` or `next` or `like`) -> [bold]Copy[/bold] -> [bold]Copy request headers[/bold].
""", title="🔴 YouTube Music Auth Guide", border_style="red"))

    console.print("[1] Paste Raw Request Headers (Recommended)")
    console.print("[2] Browser OAuth (Follow terminal prompt)")
    choice = Prompt.ask("Choose authentication method", choices=["1", "2"], default="1")

    if choice == "1":
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
    else:
        try:
            ytmusicapi.setup_oauth(filepath=str(OAUTH_PATH), open_browser=True)
            console.print(f"[bold green]✔ OAuth credentials saved to {OAUTH_PATH.name}![/bold green]\n")
            return str(OAUTH_PATH)
        except Exception as e:
            console.print(f"[bold red]OAuth setup error: {e}[/bold red]")
            raise SystemExit(1)
