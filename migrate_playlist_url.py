import sys
import requests
import json
import re
import time

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

PLAYLIST_URL = "https://open.spotify.com/playlist/0V50Da6LqukljMWmvW5r7g"


def extract_spotify_playlist(url: str):
    # Normalize embed URL
    playlist_id = url.split("playlist/")[-1].split("?")[0]
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    resp = requests.get(embed_url, headers=headers)
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
    if not match:
        raise ValueError("Could not extract playlist data from Spotify URL.")

    data = json.loads(match.group(1))
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
    name = entity.get("name", "Spotify Playlist")
    tracklist = entity.get("trackList", [])

    parsed_tracks = []
    for t in tracklist:
        title = t.get("title", "")
        # Clean subtitle / artist
        subtitle = t.get("subtitle", "").replace("\xa0", " ").replace("", "")
        artists = [a.strip() for a in subtitle.split(",") if a.strip()]
        duration_ms = t.get("duration", 0)

        if title:
            parsed_tracks.append({
                "title": title,
                "artists": artists,
                "artist_str": ", ".join(artists),
                "duration_ms": duration_ms
            })

    return name, parsed_tracks


def migrate_playlist(url: str = PLAYLIST_URL):
    console.print(f"\n[bold cyan]1. Scraping Spotify playlist from: {url}[/bold cyan]")
    name, tracks = extract_spotify_playlist(url)
    console.print(f"[bold green]✔ Found Playlist:[/bold green] [yellow]'{name}'[/yellow] with [bold green]{len(tracks)}[/bold green] tracks.\n")

    console.print("[bold cyan]2. Connecting to YouTube Music...[/bold cyan]")
    yt = YTMusicClient(auth_file="browser.json")
    storage = Storage()

    # Create playlist on YT Music
    console.print(f"[yellow]Creating playlist '{name}' on YouTube Music...[/yellow]")
    yt_playlist_id = yt.create_playlist(title=name, description=f"Migrated from Spotify: {url}", privacy_status="PRIVATE")
    if not yt_playlist_id:
        console.print("[bold red]Failed to create playlist on YouTube Music.[/bold red]")
        return

    console.print(f"[bold green]✔ Created YouTube Music Playlist ID: {yt_playlist_id}[/bold green]\n")

    # Match and add tracks
    matched_video_ids = []
    unmatched = []

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
            title = t["title"]
            artists = t["artists"]
            artist_str = t["artist_str"]
            duration_ms = t.get("duration_ms")

            # Check cache
            cache_key = f"pl_{title}_{artist_str}"
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
                    spotify_duration_ms=duration_ms,
                    candidates=candidates,
                    min_confidence=0.60
                )
                if match_res:
                    cand, conf = match_res
                    vid = cand.get("videoId")
                    storage.save_track_match(cache_key, vid, title, artist_str, cand.get("title", ""), "", conf)
                else:
                    unmatched.append(f"{title} - {artist_str}")

            if vid:
                matched_video_ids.append(vid)

            progress.advance(task)
            time.sleep(0.05)

    console.print(f"\n[bold yellow]Adding {len(matched_video_ids)} matched tracks to playlist '{name}' on YouTube Music...[/bold yellow]")
    yt.add_tracks_to_playlist(yt_playlist_id, matched_video_ids)

    console.print(f"[bold green]🎉 SUCCESS! Playlist '{name}' has been created on YouTube Music with {len(matched_video_ids)}/{len(tracks)} songs![/bold green]")
    if unmatched:
        console.print(f"[yellow]Unmatched ({len(unmatched)} songs):[/yellow] {', '.join(unmatched[:5])}")


if __name__ == "__main__":
    migrate_playlist()
