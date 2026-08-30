import json
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ytmusic_client import YTMusicClient
from matcher import clean_title, find_best_track_match
from storage import Storage
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console(force_terminal=True)


def migrate_playlist_from_json(json_file: str = "rabbit_playlist.json", playlist_name: str = "Rabbit"):
    if not Path(json_file).exists():
        console.print(f"[bold red]File '{json_file}' not found.[/bold red]")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tracks = data.get("tracks") or data.get("liked_songs") or []
    name = data.get("name") or playlist_name
    console.print(f"\n[bold cyan]Loaded '{json_file}' with {len(tracks)} tracks for playlist '{name}'.[/bold cyan]")

    yt = YTMusicClient(auth_file="browser.json")
    storage = Storage()

    # Check if playlist already exists in DB or find it
    migrated_pl = storage.get_migrated_playlist(f"pl_{name}")
    yt_playlist_id = None
    if migrated_pl:
        yt_playlist_id = migrated_pl["ytmusic_playlist_id"]
        console.print(f"[yellow]Found existing YouTube Music playlist ID: {yt_playlist_id}[/yellow]")
    else:
        yt_playlist_id = yt.create_playlist(title=name, description=f"Migrated Spotify playlist: {name}", privacy_status="PRIVATE")
        if yt_playlist_id:
            storage.save_migrated_playlist(f"pl_{name}", yt_playlist_id, name, len(tracks), 0)

    if not yt_playlist_id:
        console.print("[bold red]Failed to get/create playlist on YouTube Music.[/bold red]")
        return

    matched_video_ids = []
    skipped = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Matching '{name}' tracks...", total=len(tracks))

        for t in tracks:
            title = t.get("name") or t.get("title", "")
            artists = t.get("artists", [])
            artist_str = t.get("artist_str") or ", ".join(artists)
            cache_key = f"pl_{name}_{title}_{artist_str}"

            if storage.is_playlist_track_added(f"pl_{name}", cache_key):
                skipped += 1
                progress.advance(task)
                continue

            cached = storage.get_track_match(cache_key)
            vid = None
            if cached and cached.get("video_id"):
                vid = cached["video_id"]
            else:
                main_artist = artists[0] if artists else ""
                query = f"{clean_title(title)} {main_artist}".strip()
                candidates = yt.search_song(query, limit=5)
                match_res = find_best_track_match(
                    spotify_title=title,
                    spotify_artist=main_artist,
                    spotify_duration_ms=t.get("duration_ms"),
                    candidates=candidates,
                    min_confidence=0.60
                )
                if match_res:
                    cand, conf = match_res
                    vid = cand.get("videoId")
                    storage.save_track_match(cache_key, vid, title, artist_str, cand.get("title", ""), "", conf)

            if vid:
                matched_video_ids.append((cache_key, vid))

            progress.advance(task)
            time.sleep(0.05)

    if matched_video_ids:
        console.print(f"\n[bold yellow]Adding {len(matched_video_ids)} new tracks to playlist '{name}'...[/bold yellow]")
        vids_only = [v[1] for v in matched_video_ids]
        yt.add_tracks_to_playlist(yt_playlist_id, vids_only)
        for key, vid in matched_video_ids:
            storage.mark_playlist_track_added(f"pl_{name}", key, vid)

    console.print(f"[bold green]🎉 SUCCESS! Playlist '{name}' now has all {len(matched_video_ids) + skipped}/{len(tracks)} songs on YouTube Music![/bold green]")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "rabbit_playlist.json"
    migrate_playlist_from_json(target)
