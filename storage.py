import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).parent / "migration_cache.db"


class Storage:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._shared_conn:
            return self._shared_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Track matches cache (Spotify ID -> YT Music Video ID)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS track_matches (
                    spotify_id TEXT PRIMARY KEY,
                    ytmusic_video_id TEXT,
                    spotify_title TEXT,
                    spotify_artist TEXT,
                    ytmusic_title TEXT,
                    ytmusic_artist TEXT,
                    confidence REAL,
                    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Artist matches cache (Spotify ID -> YT Music Channel ID)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artist_matches (
                    spotify_id TEXT PRIMARY KEY,
                    ytmusic_channel_id TEXT,
                    artist_name TEXT,
                    subscribed INTEGER DEFAULT 0,
                    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Liked songs migration tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrated_likes (
                    spotify_id TEXT PRIMARY KEY,
                    ytmusic_video_id TEXT,
                    migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Playlist migration tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrated_playlists (
                    spotify_playlist_id TEXT PRIMARY KEY,
                    ytmusic_playlist_id TEXT,
                    playlist_name TEXT,
                    total_tracks INTEGER DEFAULT 0,
                    synced_tracks INTEGER DEFAULT 0,
                    migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Playlist tracks tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    spotify_playlist_id TEXT,
                    spotify_track_id TEXT,
                    ytmusic_video_id TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (spotify_playlist_id, spotify_track_id)
                )
            """)

            # Unmatched items log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unmatched_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT, -- 'track' or 'artist'
                    spotify_id TEXT,
                    name TEXT,
                    artist TEXT,
                    reason TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    # Track match caching
    def get_track_match(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ytmusic_video_id, ytmusic_title, ytmusic_artist, confidence FROM track_matches WHERE spotify_id = ?", (spotify_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "video_id": row[0],
                    "title": row[1],
                    "artist": row[2],
                    "confidence": row[3]
                }
        return None

    def save_track_match(self, spotify_id: str, video_id: Optional[str], s_title: str, s_artist: str, yt_title: str, yt_artist: str, confidence: float):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO track_matches (spotify_id, ytmusic_video_id, spotify_title, spotify_artist, ytmusic_title, ytmusic_artist, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (spotify_id, video_id, s_title, s_artist, yt_title, yt_artist, confidence))
            conn.commit()

    # Liked songs status
    def is_like_migrated(self, spotify_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM migrated_likes WHERE spotify_id = ?", (spotify_id,))
            return cursor.fetchone() is not None

    def mark_like_migrated(self, spotify_id: str, video_id: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO migrated_likes (spotify_id, ytmusic_video_id) VALUES (?, ?)", (spotify_id, video_id))
            conn.commit()

    # Artist subscription status
    def get_artist_match(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ytmusic_channel_id, artist_name, subscribed FROM artist_matches WHERE spotify_id = ?", (spotify_id,))
            row = cursor.fetchone()
            if row:
                return {"channel_id": row[0], "artist_name": row[1], "subscribed": bool(row[2])}
        return None

    def save_artist_match(self, spotify_id: str, channel_id: Optional[str], artist_name: str, subscribed: bool = False):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO artist_matches (spotify_id, ytmusic_channel_id, artist_name, subscribed)
                VALUES (?, ?, ?, ?)
            """, (spotify_id, channel_id, artist_name, 1 if subscribed else 0))
            conn.commit()

    # Playlists
    def get_migrated_playlist(self, spotify_playlist_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ytmusic_playlist_id, playlist_name, total_tracks, synced_tracks FROM migrated_playlists WHERE spotify_playlist_id = ?", (spotify_playlist_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "ytmusic_playlist_id": row[0],
                    "name": row[1],
                    "total_tracks": row[2],
                    "synced_tracks": row[3]
                }
        return None

    def save_migrated_playlist(self, spotify_playlist_id: str, ytmusic_playlist_id: str, name: str, total_tracks: int, synced_tracks: int):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO migrated_playlists (spotify_playlist_id, ytmusic_playlist_id, playlist_name, total_tracks, synced_tracks)
                VALUES (?, ?, ?, ?, ?)
            """, (spotify_playlist_id, ytmusic_playlist_id, name, total_tracks, synced_tracks))
            conn.commit()

    def is_playlist_track_added(self, spotify_playlist_id: str, spotify_track_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM playlist_tracks WHERE spotify_playlist_id = ? AND spotify_track_id = ?", (spotify_playlist_id, spotify_track_id))
            return cursor.fetchone() is not None

    def mark_playlist_track_added(self, spotify_playlist_id: str, spotify_track_id: str, video_id: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO playlist_tracks (spotify_playlist_id, spotify_track_id, ytmusic_video_id) VALUES (?, ?, ?)", (spotify_playlist_id, spotify_track_id, video_id))
            conn.commit()

    # Unmatched logging
    def log_unmatched(self, item_type: str, spotify_id: str, name: str, artist: str, reason: str):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO unmatched_items (item_type, spotify_id, name, artist, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (item_type, spotify_id, name, artist, reason))
            conn.commit()

    def get_summary_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM migrated_likes")
            likes_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM migrated_playlists")
            playlists_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM artist_matches WHERE subscribed = 1")
            artists_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM unmatched_items")
            unmatched_count = cursor.fetchone()[0]

            return {
                "likes_migrated": likes_count,
                "playlists_migrated": playlists_count,
                "artists_migrated": artists_count,
                "unmatched_items": unmatched_count
            }
