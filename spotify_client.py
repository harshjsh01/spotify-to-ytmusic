import requests
from typing import List, Dict, Any, Generator, Optional
import json
import re


class SpotifyNoDevClient:
    """
    Spotify client that works WITHOUT Spotify Developer App / Premium.
    Supports:
    1. sp_dc session cookie authentication (automatic token retrieval)
    2. Direct JSON export file loading
    3. Public playlist scraping
    """

    def __init__(self, sp_dc: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None):
        self.sp_dc = sp_dc
        self.json_data = json_data
        self.access_token = None
        if self.sp_dc:
            self._authenticate_with_sp_dc()

    def _authenticate_with_sp_dc(self):
        """Fetches temporary Web Player access token using sp_dc cookie."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"sp_dc={self.sp_dc}"
        }
        resp = requests.get("https://open.spotify.com/get_access_token", headers=headers)
        if resp.status_code != 200:
            raise ValueError("Invalid sp_dc cookie or session expired. Please copy a fresh sp_dc cookie.")
        data = resp.json()
        self.access_token = data.get("accessToken")
        if not self.access_token:
            raise ValueError("Could not extract access token from Spotify session.")

    def _api_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.access_token:
            raise ValueError("No active Spotify session.")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise ValueError(f"Spotify API error: {resp.status_code} - {resp.text}")
        return resp.json()

    def get_user_profile(self) -> Dict[str, Any]:
        if self.json_data:
            return {"display_name": self.json_data.get("user", "Spotify User"), "id": "local_export"}
        return self._api_get("https://api.spotify.com/v1/me")

    def get_liked_tracks(self) -> Generator[Dict[str, Any], None, None]:
        if self.json_data and "liked_songs" in self.json_data:
            for track in self.json_data["liked_songs"]:
                yield {
                    "id": track.get("id", track.get("name")),
                    "name": track["name"],
                    "artists": track.get("artists", [track.get("artist", "")]),
                    "artist_str": track.get("artist_str") or ", ".join(track.get("artists", [track.get("artist", "")])),
                    "album": track.get("album", ""),
                    "duration_ms": track.get("duration_ms", 0)
                }
            return

        url = "https://api.spotify.com/v1/me/tracks"
        params = {"limit": 50, "offset": 0}
        while url:
            data = self._api_get(url, params=params)
            for item in data.get("items", []):
                t = item.get("track")
                if t and t.get("id"):
                    yield {
                        "id": t["id"],
                        "name": t["name"],
                        "artists": [a["name"] for a in t.get("artists", [])],
                        "artist_str": ", ".join([a["name"] for a in t.get("artists", [])]),
                        "album": t.get("album", {}).get("name", ""),
                        "duration_ms": t.get("duration_ms", 0)
                    }
            url = data.get("next")
            params = None

    def get_liked_tracks_count(self) -> int:
        if self.json_data and "liked_songs" in self.json_data:
            return len(self.json_data["liked_songs"])
        data = self._api_get("https://api.spotify.com/v1/me/tracks", params={"limit": 1})
        return data.get("total", 0)

    def get_followed_artists(self) -> Generator[Dict[str, Any], None, None]:
        if self.json_data and "followed_artists" in self.json_data:
            for artist in self.json_data["followed_artists"]:
                yield {
                    "id": artist.get("id", artist.get("name")),
                    "name": artist["name"]
                }
            return

        url = "https://api.spotify.com/v1/me/following"
        params = {"type": "artist", "limit": 50}
        while url:
            data = self._api_get(url, params=params)
            artists_data = data.get("artists", {})
            for item in artists_data.get("items", []):
                yield {
                    "id": item["id"],
                    "name": item["name"]
                }
            url = artists_data.get("next")
            params = None

    def get_followed_artists_count(self) -> int:
        if self.json_data and "followed_artists" in self.json_data:
            return len(self.json_data["followed_artists"])
        data = self._api_get("https://api.spotify.com/v1/me/following", params={"type": "artist", "limit": 1})
        return data.get("artists", {}).get("total", 0)

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        if self.json_data and "playlists" in self.json_data:
            return [
                {
                    "id": p.get("id", str(idx)),
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "total_tracks": len(p.get("tracks", [])),
                    "tracks": p.get("tracks", [])
                }
                for idx, p in enumerate(self.json_data["playlists"])
            ]

        playlists = []
        url = "https://api.spotify.com/v1/me/playlists"
        params = {"limit": 50, "offset": 0}
        while url:
            data = self._api_get(url, params=params)
            for p in data.get("items", []):
                playlists.append({
                    "id": p["id"],
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "total_tracks": p.get("tracks", {}).get("total", 0)
                })
            url = data.get("next")
            params = None
        return playlists

    def get_playlist_tracks(self, playlist_id: str) -> Generator[Dict[str, Any], None, None]:
        if self.json_data and "playlists" in self.json_data:
            for p in self.json_data["playlists"]:
                if p.get("id") == playlist_id or str(self.json_data["playlists"].index(p)) == playlist_id:
                    for t in p.get("tracks", []):
                        yield {
                            "id": t.get("id", t.get("name")),
                            "name": t["name"],
                            "artists": t.get("artists", [t.get("artist", "")]),
                            "artist_str": t.get("artist_str") or ", ".join(t.get("artists", [t.get("artist", "")])),
                            "album": t.get("album", ""),
                            "duration_ms": t.get("duration_ms", 0)
                        }
            return

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        params = {"limit": 100, "offset": 0}
        while url:
            data = self._api_get(url, params=params)
            for item in data.get("items", []):
                t = item.get("track")
                if t and t.get("id"):
                    yield {
                        "id": t["id"],
                        "name": t["name"],
                        "artists": [a["name"] for a in t.get("artists", [])],
                        "artist_str": ", ".join([a["name"] for a in t.get("artists", [])]),
                        "album": t.get("album", {}).get("name", ""),
                        "duration_ms": t.get("duration_ms", 0)
                    }
            url = data.get("next")
            params = None
