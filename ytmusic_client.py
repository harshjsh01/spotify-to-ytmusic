import time
from typing import List, Dict, Any, Optional
from ytmusicapi import YTMusic


class YTMusicClient:
    def __init__(self, auth_file: str = "browser.json"):
        self.ytmusic = YTMusic(auth_file)

    def search_song(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches YouTube Music for songs and videos matching query."""
        results = []
        try:
            # First search songs
            song_results = self.ytmusic.search(query=query, filter="songs", limit=limit)
            if song_results:
                results.extend(song_results)
        except Exception:
            pass

        # If no songs or few results, search videos as fallback
        if len(results) < 2:
            try:
                video_results = self.ytmusic.search(query=query, filter="videos", limit=limit)
                if video_results:
                    results.extend(video_results)
            except Exception:
                pass

        return results

    def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Searches for an artist channel on YouTube Music."""
        try:
            results = self.ytmusic.search(query=artist_name, filter="artists", limit=3)
            if results:
                # Return the top artist result
                for r in results:
                    if r.get("browseId"):
                        return {
                            "name": r.get("artist", artist_name),
                            "browseId": r.get("browseId")
                        }
        except Exception:
            pass
        return None

    def rate_song_like(self, video_id: str) -> bool:
        """Sets the rating of a track to LIKE on YouTube Music."""
        try:
            self.ytmusic.rate_song(videoId=video_id, rating="LIKE")
            return True
        except Exception as e:
            # Some video types or rate limits might fail
            return False

    def subscribe_artist(self, channel_id: str) -> bool:
        """Subscribes to an artist channel on YouTube Music."""
        try:
            self.ytmusic.subscribe_artists([channel_id])
            return True
        except Exception:
            return False

    def create_playlist(self, title: str, description: str = "", privacy_status: str = "PRIVATE") -> Optional[str]:
        """Creates a new playlist on YouTube Music and returns playlist ID."""
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=title,
                description=description,
                privacy_status=privacy_status
            )
            return playlist_id
        except Exception:
            return None

    def add_tracks_to_playlist(self, playlist_id: str, video_ids: List[str]) -> bool:
        """Adds video IDs in chunks of 50 to avoid API payload limits."""
        if not video_ids:
            return True
        chunk_size = 50
        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i:i + chunk_size]
            try:
                self.ytmusic.add_playlist_items(playlistId=playlist_id, videoIds=chunk, duplicates=False)
                time.sleep(0.5)  # Slight throttle to be polite to YT API
            except Exception:
                # Try adding individually if chunk fails
                for vid in chunk:
                    try:
                        self.ytmusic.add_playlist_items(playlistId=playlist_id, videoIds=[vid], duplicates=False)
                        time.sleep(0.2)
                    except Exception:
                        pass
        return True
