import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

from spotify_client import SpotifyWebClient
from ytmusic_client import YTMusicClient
from matcher import clean_title, find_best_track_match
from storage import Storage

console = Console()


class Migrator:
    def __init__(self, spotify: SpotifyWebClient, ytmusic: YTMusicClient, storage: Storage):
        self.spotify = spotify
        self.ytmusic = ytmusic
        self.storage = storage

    def match_track(self, track: Dict[str, Any]) -> Optional[str]:
        """Resolves Spotify track to YouTube Music videoId using cache or API search."""
        spotify_id = track["id"]
        cached = self.storage.get_track_match(spotify_id)
        if cached and cached.get("video_id"):
            return cached["video_id"]

        # Search YT Music
        artist_name = track["artists"][0] if track.get("artists") else ""
        query = f"{clean_title(track['name'])} {artist_name}".strip()

        candidates = self.ytmusic.search_song(query, limit=6)
        match_res = find_best_track_match(
            spotify_title=track["name"],
            spotify_artist=artist_name,
            spotify_duration_ms=track.get("duration_ms"),
            candidates=candidates,
            min_confidence=0.60
        )

        if match_res:
            cand, confidence = match_res
            vid = cand.get("videoId")
            cand_title = cand.get("title", "")
            cand_artist = ", ".join([a.get("name", "") for a in cand.get("artists", [])])
            self.storage.save_track_match(
                spotify_id=spotify_id,
                video_id=vid,
                s_title=track["name"],
                s_artist=track.get("artist_str", artist_name),
                yt_title=cand_title,
                yt_artist=cand_artist,
                confidence=confidence
            )
            return vid
        else:
            self.storage.log_unmatched("track", spotify_id, track["name"], track.get("artist_str", artist_name), "No close match found on YT Music")
            return None

    def migrate_liked_songs(self, also_create_playlist: bool = True) -> Dict[str, int]:
        """Migrates all Spotify Liked Songs to YouTube Music Likes (and backup playlist)."""
        console.print("\n[bold cyan]▶ Starting Liked Songs Migration...[/bold cyan]")
        total_count = self.spotify.get_liked_tracks_count()
        console.print(f"Found [bold green]{total_count}[/bold green] liked tracks on Spotify.")

        playlist_id = None
        if also_create_playlist:
            existing = self.storage.get_migrated_playlist("spotify_liked_tracks_backup")
            if existing:
                playlist_id = existing["ytmusic_playlist_id"]
            else:
                playlist_id = self.ytmusic.create_playlist(
                    title="Spotify Liked Songs (Migrated)",
                    description="Backup playlist of all Spotify Liked Songs migrated automatically."
                )
                if playlist_id:
                    self.storage.save_migrated_playlist("spotify_liked_tracks_backup", playlist_id, "Spotify Liked Songs (Migrated)", total_count, 0)

        migrated = 0
        skipped = 0
        failed = 0
        new_playlist_vids = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Migrating Liked Songs...", total=total_count)

            for track in self.spotify.get_liked_tracks():
                track_id = track["id"]
                track_name = track["name"]

                if self.storage.is_like_migrated(track_id):
                    skipped += 1
                    progress.advance(task)
                    continue

                vid = self.match_track(track)
                if vid:
                    success = self.ytmusic.rate_song_like(vid)
                    if success:
                        self.storage.mark_like_migrated(track_id, vid)
                        migrated += 1
                        if playlist_id:
                            new_playlist_vids.append(vid)
                    else:
                        failed += 1
                else:
                    failed += 1

                progress.advance(task)
                time.sleep(0.1)

        if playlist_id and new_playlist_vids:
            console.print(f"[yellow]Adding {len(new_playlist_vids)} tracks to backup playlist...[/yellow]")
            self.ytmusic.add_tracks_to_playlist(playlist_id, new_playlist_vids)

        console.print(f"[bold green]✔ Liked Songs migration complete![/bold green] (Migrated: {migrated}, Already Migrated: {skipped}, Unmatched/Failed: {failed})")
        return {"migrated": migrated, "skipped": skipped, "failed": failed}

    def migrate_followed_artists(self) -> Dict[str, int]:
        """Migrates followed artists by subscribing on YouTube Music."""
        console.print("\n[bold cyan]▶ Starting Followed Artists Migration...[/bold cyan]")
        total_count = self.spotify.get_followed_artists_count()
        console.print(f"Found [bold green]{total_count}[/bold green] followed artists on Spotify.")

        subscribed = 0
        skipped = 0
        failed = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Subscribing to Artists...", total=total_count)

            for artist in self.spotify.get_followed_artists():
                artist_id = artist["id"]
                artist_name = artist["name"]

                cached = self.storage.get_artist_match(artist_id)
                if cached and cached.get("subscribed"):
                    skipped += 1
                    progress.advance(task)
                    continue

                channel_match = self.ytmusic.search_artist(artist_name)
                if channel_match and channel_match.get("browseId"):
                    channel_id = channel_match["browseId"]
                    success = self.ytmusic.subscribe_artist(channel_id)
                    self.storage.save_artist_match(artist_id, channel_id, artist_name, subscribed=success)
                    if success:
                        subscribed += 1
                    else:
                        failed += 1
                else:
                    self.storage.log_unmatched("artist", artist_id, artist_name, "", "Artist channel not found on YT Music")
                    failed += 1

                progress.advance(task)
                time.sleep(0.15)

        console.print(f"[bold green]✔ Artist subscriptions complete![/bold green] (Subscribed: {subscribed}, Already Subscribed: {skipped}, Failed: {failed})")
        return {"subscribed": subscribed, "skipped": skipped, "failed": failed}

    def migrate_playlists(self, selected_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Migrates user playlists to YouTube Music."""
        console.print("\n[bold cyan]▶ Starting Playlists Migration...[/bold cyan]")
        all_playlists = self.spotify.get_user_playlists()

        if selected_ids:
            playlists_to_sync = [p for p in all_playlists if p["id"] in selected_ids]
        else:
            playlists_to_sync = all_playlists

        console.print(f"Found [bold green]{len(playlists_to_sync)}[/bold green] playlists to migrate.")

        results = {}

        for p in playlists_to_sync:
            p_id = p["id"]
            p_name = p["name"]
            total_tracks = p["total_tracks"]

            console.print(f"\n[bold yellow]📁 Migrating Playlist: '{p_name}' ({total_tracks} tracks)[/bold yellow]")

            # Check if YT Music playlist already exists in DB
            migrated_info = self.storage.get_migrated_playlist(p_id)
            if migrated_info:
                yt_playlist_id = migrated_info["ytmusic_playlist_id"]
            else:
                yt_playlist_id = self.ytmusic.create_playlist(
                    title=f"{p_name}",
                    description=p.get("description") or f"Migrated from Spotify playlist: {p_name}"
                )
                if yt_playlist_id:
                    self.storage.save_migrated_playlist(p_id, yt_playlist_id, p_name, total_tracks, 0)
                else:
                    console.print(f"[bold red]Failed to create playlist '{p_name}' on YT Music.[/bold red]")
                    continue

            vids_to_add = []
            synced_count = 0
            skipped_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Matching '{p_name}' tracks...", total=total_tracks)

                for track in self.spotify.get_playlist_tracks(p_id):
                    t_id = track["id"]
                    if self.storage.is_playlist_track_added(p_id, t_id):
                        skipped_count += 1
                        progress.advance(task)
                        continue

                    vid = self.match_track(track)
                    if vid:
                        vids_to_add.append((t_id, vid))
                    progress.advance(task)
                    time.sleep(0.05)

            if vids_to_add:
                console.print(f"[yellow]Adding {len(vids_to_add)} tracks to YouTube Music playlist '{p_name}'...[/yellow]")
                video_ids_only = [v[1] for v in vids_to_add]
                self.ytmusic.add_tracks_to_playlist(yt_playlist_id, video_ids_only)
                for t_id, vid in vids_to_add:
                    self.storage.mark_playlist_track_added(p_id, t_id, vid)
                synced_count = len(vids_to_add)

            self.storage.save_migrated_playlist(p_id, yt_playlist_id, p_name, total_tracks, synced_count + skipped_count)
            results[p_name] = {"total": total_tracks, "added": synced_count, "skipped": skipped_count}
            console.print(f"[bold green]✔ Playlist '{p_name}' migrated![/bold green] ({synced_count} added, {skipped_count} already present)")

        return results

    def generate_report(self, output_path: str = "migration_summary.json"):
        """Generates a detailed JSON and console summary report."""
        stats = self.storage.get_summary_stats()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        table = Table(title="🎉 Migration Summary Report", border_style="green")
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Migrated / Subscribed", style="bold green")
        table.add_row("Liked Songs", str(stats["likes_migrated"]))
        table.add_row("Playlists Migrated", str(stats["playlists_migrated"]))
        table.add_row("Artists Subscribed", str(stats["artists_migrated"]))
        table.add_row("Unmatched Items", str(stats["unmatched_items"]))
        console.print(table)
