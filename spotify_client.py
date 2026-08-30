from typing import List, Dict, Any, Generator, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth


SCOPES = [
    "user-library-read",
    "user-follow-read",
    "playlist-read-private",
    "playlist-read-collaborative"
]


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://127.0.0.1:8888/callback", cache_path: str = ".spotify_cache"):
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=" ".join(SCOPES),
            cache_path=cache_path,
            open_browser=True
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_user_profile(self) -> Dict[str, Any]:
        return self.sp.current_user()

    def get_liked_tracks(self) -> Generator[Dict[str, Any], None, None]:
        """Yields all tracks from the user's Liked Songs library with pagination."""
        offset = 0
        limit = 50
        while True:
            response = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            items = response.get("items", [])
            if not items:
                break
            for item in items:
                track = item.get("track")
                if track and track.get("id"):
                    yield {
                        "id": track["id"],
                        "name": track["name"],
                        "artists": [a["name"] for a in track.get("artists", [])],
                        "artist_str": ", ".join([a["name"] for a in track.get("artists", [])]),
                        "album": track.get("album", {}).get("name", ""),
                        "duration_ms": track.get("duration_ms", 0),
                        "added_at": item.get("added_at", "")
                    }
            offset += len(items)
            if not response.get("next"):
                break

    def get_liked_tracks_count(self) -> int:
        response = self.sp.current_user_saved_tracks(limit=1)
        return response.get("total", 0)

    def get_followed_artists(self) -> Generator[Dict[str, Any], None, None]:
        """Yields all followed artists with cursor pagination."""
        after = None
        limit = 50
        while True:
            response = self.sp.current_user_followed_artists(limit=limit, after=after)
            artists_data = response.get("artists", {})
            items = artists_data.get("items", [])
            if not items:
                break
            for item in items:
                yield {
                    "id": item["id"],
                    "name": item["name"],
                    "genres": item.get("genres", []),
                    "followers": item.get("followers", {}).get("total", 0)
                }
            after = artists_data.get("cursors", {}).get("after")
            if not after or not artists_data.get("next"):
                break

    def get_followed_artists_count(self) -> int:
        response = self.sp.current_user_followed_artists(limit=1)
        return response.get("artists", {}).get("total", 0)

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        """Returns all playlists belonging to or followed by the user."""
        playlists = []
        offset = 0
        limit = 50
        user_id = self.sp.current_user().get("id")

        while True:
            response = self.sp.current_user_playlists(limit=limit, offset=offset)
            items = response.get("items", [])
            if not items:
                break
            for p in items:
                # Include all playlists or flag owner
                playlists.append({
                    "id": p["id"],
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "total_tracks": p.get("tracks", {}).get("total", 0),
                    "is_owner": p.get("owner", {}).get("id") == user_id,
                    "public": p.get("public", False)
                })
            offset += len(items)
            if not response.get("next"):
                break
        return playlists

    def get_playlist_tracks(self, playlist_id: str) -> Generator[Dict[str, Any], None, None]:
        """Yields all tracks for a given playlist."""
        offset = 0
        limit = 100
        while True:
            response = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)
            items = response.get("items", [])
            if not items:
                break
            for item in items:
                track = item.get("track")
                if track and track.get("id"):
                    yield {
                        "id": track["id"],
                        "name": track["name"],
                        "artists": [a["name"] for a in track.get("artists", [])],
                        "artist_str": ", ".join([a["name"] for a in track.get("artists", [])]),
                        "album": track.get("album", {}).get("name", ""),
                        "duration_ms": track.get("duration_ms", 0),
                        "added_at": item.get("added_at", "")
                    }
            offset += len(items)
            if not response.get("next"):
                break
