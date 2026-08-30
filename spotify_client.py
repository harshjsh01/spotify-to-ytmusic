import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional


class SpotifyWebClient:
    """
    Spotify client using the Web Player session Bearer token or spotify_data.json.
    Works 100% for Free Spotify accounts without Spotify Developer App or Premium!
    """

    def __init__(self, token: Optional[str] = None, json_file: Optional[str] = "spotify_data.json"):
        self.token = token.replace("Bearer ", "").strip() if token else None
        self.json_data = None

        if json_file and Path(json_file).exists():
            with open(json_file, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "app-platform": "WebPlayer"
        }

    def get_user_profile(self) -> Dict[str, Any]:
        if self.json_data:
            return {"display_name": self.json_data.get("user", "Spotify User"), "id": "local"}
        resp = requests.get("https://api.spotify.com/v1/me", headers=self._get_headers())
        if resp.status_code == 200:
            return resp.json()
        return {"display_name": "Spotify User", "id": "web_user"}

    def get_liked_tracks(self) -> Generator[Dict[str, Any], None, None]:
        if self.json_data and "liked_songs" in self.json_data:
            for t in self.json_data["liked_songs"]:
                yield {
                    "id": t.get("id", t.get("name")),
                    "name": t["name"],
                    "artists": t.get("artists", [t.get("artist", "")]),
                    "artist_str": t.get("artist_str") or ", ".join(t.get("artists", [t.get("artist", "")])),
                    "album": t.get("album", ""),
                    "duration_ms": t.get("duration_ms", 0)
                }
            return

        url = "https://api.spotify.com/v1/me/tracks?limit=50"
        while url:
            resp = requests.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                break
            data = resp.json()
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

    def get_liked_tracks_count(self) -> int:
        if self.json_data and "liked_songs" in self.json_data:
            return len(self.json_data["liked_songs"])
        resp = requests.get("https://api.spotify.com/v1/me/tracks?limit=1", headers=self._get_headers())
        if resp.status_code == 200:
            return resp.json().get("total", 0)
        return 0

    def get_followed_artists(self) -> Generator[Dict[str, Any], None, None]:
        if self.json_data and "followed_artists" in self.json_data:
            for a in self.json_data["followed_artists"]:
                yield {
                    "id": a.get("id", a.get("name")),
                    "name": a["name"]
                }
            return

        url = "https://api.spotify.com/v1/me/following?type=artist&limit=50"
        while url:
            resp = requests.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                break
            data = resp.json()
            artists = data.get("artists", {})
            for item in artists.get("items", []):
                yield {
                    "id": item["id"],
                    "name": item["name"]
                }
            url = artists.get("next")

    def get_followed_artists_count(self) -> int:
        if self.json_data and "followed_artists" in self.json_data:
            return len(self.json_data["followed_artists"])
        resp = requests.get("https://api.spotify.com/v1/me/following?type=artist&limit=1", headers=self._get_headers())
        if resp.status_code == 200:
            return resp.json().get("artists", {}).get("total", 0)
        return 0

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        if self.json_data and "playlists" in self.json_data:
            return [
                {
                    "id": p.get("id", str(idx)),
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "total_tracks": len(p.get("tracks", []))
                }
                for idx, p in enumerate(self.json_data["playlists"])
            ]

        playlists = []
        url = "https://api.spotify.com/v1/me/playlists?limit=50"
        while url:
            resp = requests.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                break
            data = resp.json()
            for p in data.get("items", []):
                playlists.append({
                    "id": p["id"],
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "total_tracks": p.get("tracks", {}).get("total", 0)
                })
            url = data.get("next")
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

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
        while url:
            resp = requests.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                break
            data = resp.json()
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
