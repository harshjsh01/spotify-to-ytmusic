import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from config import get_spotify_client, ensure_ytmusic_auth
from spotify_client import SpotifyClient
from ytmusic_client import YTMusicClient
from storage import Storage
from migrator import Migrator

console = Console()

BANNER = r"""[bold cyan]
  ____                  _   _  __           __     _________  __             _      
 / ___| _ __   ___  ___| | | | \ \         / /_ _  \__   __/ |  \/  |_   _ ___(_) ___ 
 \___ \| '_ \ / _ \/ __| | | |  \ \  /\  / / _` |    | |    | |\/| | | | / __| |/ __|
  ___) | |_) | (_) \__ \ |_| |   \ \/  \/ / (_| |    | |    | |  | | |_| \__ \ | (__ 
 |____/| .__/ \___/|___/\___/     \__/ \__/ \__,_|   |_|    |_|  |_|\__,_|___/_|\___|
       |_|                                                                           
[/bold cyan]
[dim]Automated Spotify ➔ YouTube Music Migration Tool (Likes, Playlists & Artists)[/dim]
"""


def show_banner():
    console.print(BANNER)


def init_clients():
    console.print("[bold yellow]1. Connecting Spotify Library...[/bold yellow]")
    try:
        spotify = get_spotify_client()
        user = spotify.get_user_profile()
        console.print(f"[bold green]✔ Loaded Spotify Library for:[/bold green] {user.get('display_name', 'User')}\n")
    except Exception as e:
        console.print(f"[bold red]Failed to load Spotify data: {e}[/bold red]")
        sys.exit(1)

    console.print("[bold yellow]2. Authenticating YouTube Music...[/bold yellow]")
    auth_file = ensure_ytmusic_auth()
    try:
        ytmusic = YTMusicClient(auth_file=auth_file)
        console.print(f"[bold green]✔ YouTube Music initialized using {auth_file}![/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]Failed to connect to YouTube Music: {e}[/bold red]")
        sys.exit(1)

    storage = Storage()
    migrator = Migrator(spotify=spotify, ytmusic=ytmusic, storage=storage)
    return spotify, ytmusic, storage, migrator


def interactive_menu(spotify: SpotifyClient, migrator: Migrator, storage: Storage):
    while True:
        console.print(Panel("""[bold green]Choose an action:[/bold green]
[1] 🚀 [bold]Full Migration[/bold] (Liked Songs + Followed Artists + Playlists)
[2] 💖 [bold]Migrate Liked Songs Only[/bold]
[3] 📁 [bold]Migrate Playlists Only[/bold]
[4] 👤 [bold]Migrate Followed Artists Only[/bold]
[5] 📊 [bold]View Migration Stats & Status[/bold]
[6] ❌ [bold]Exit[/bold]
""", title="📌 Migration Options", border_style="cyan"))

        choice = Prompt.ask("Enter option number", choices=["1", "2", "3", "4", "5", "6"], default="1")

        if choice == "1":
            console.print("\n[bold cyan]Starting Full Migration...[/bold cyan]")
            migrator.migrate_liked_songs(also_create_playlist=True)
            migrator.migrate_followed_artists()
            migrator.migrate_playlists()
            migrator.generate_report()

        elif choice == "2":
            create_backup_pl = Confirm.ask("Also create a 'Spotify Liked Songs (Migrated)' backup playlist on YT Music?", default=True)
            migrator.migrate_liked_songs(also_create_playlist=create_backup_pl)
            migrator.generate_report()

        elif choice == "3":
            playlists = spotify.get_user_playlists()
            if not playlists:
                console.print("[yellow]No Spotify playlists found.[/yellow]")
                continue

            console.print("\n[bold]Found Playlists:[/bold]")
            for idx, p in enumerate(playlists, 1):
                console.print(f"[{idx}] {p['name']} ({p['total_tracks']} tracks)")

            selection = Prompt.ask("\nEnter playlist numbers to migrate (comma separated, or 'all')", default="all")
            if selection.lower().strip() == "all":
                migrator.migrate_playlists()
            else:
                try:
                    indices = [int(i.strip()) for i in selection.split(",") if i.strip().isdigit()]
                    selected_ids = [playlists[i - 1]["id"] for i in indices if 1 <= i <= len(playlists)]
                    migrator.migrate_playlists(selected_ids=selected_ids)
                except Exception as e:
                    console.print(f"[bold red]Invalid selection: {e}[/bold red]")
            migrator.generate_report()

        elif choice == "4":
            migrator.migrate_followed_artists()
            migrator.generate_report()

        elif choice == "5":
            migrator.generate_report()

        elif choice == "6":
            console.print("[green]Goodbye![/green]")
            break


def main():
    parser = argparse.ArgumentParser(description="Spotify to YouTube Music Migration Tool")
    parser.add_argument("--all", action="store_true", help="Run full migration non-interactively")
    parser.add_argument("--likes", action="store_true", help="Migrate Liked Songs only")
    parser.add_argument("--playlists", action="store_true", help="Migrate Playlists only")
    parser.add_argument("--artists", action="store_true", help="Migrate Followed Artists only")
    args = parser.parse_args()

    show_banner()
    spotify, ytmusic, storage, migrator = init_clients()

    if args.all:
        migrator.migrate_liked_songs(also_create_playlist=True)
        migrator.migrate_followed_artists()
        migrator.migrate_playlists()
        migrator.generate_report()
    elif args.likes:
        migrator.migrate_liked_songs()
        migrator.generate_report()
    elif args.playlists:
        migrator.migrate_playlists()
        migrator.generate_report()
    elif args.artists:
        migrator.migrate_followed_artists()
        migrator.generate_report()
    else:
        interactive_menu(spotify, migrator, storage)


if __name__ == "__main__":
    main()
