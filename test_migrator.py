import unittest
from pathlib import Path
import tempfile
import os

from matcher import clean_title, parse_duration_to_seconds, calculate_match_score, find_best_track_match
from storage import Storage


class TestMatcherAndStorage(unittest.TestCase):
    def test_clean_title(self):
        self.assertEqual(clean_title("Bohemian Rhapsody - 2011 Remaster"), "Bohemian Rhapsody")
        self.assertEqual(clean_title("Starboy (feat. Daft Punk)"), "Starboy")
        self.assertEqual(clean_title("Blinding Lights (Official Video)"), "Blinding Lights")
        self.assertEqual(clean_title("Hotel California (Live / Remastered 2013)"), "Hotel California")
        self.assertEqual(clean_title("In the End [Official Music Video]"), "In the End")

    def test_parse_duration(self):
        self.assertEqual(parse_duration_to_seconds("3:45"), 225)
        self.assertEqual(parse_duration_to_seconds("1:02:15"), 3735)
        self.assertIsNone(parse_duration_to_seconds(None))
        self.assertIsNone(parse_duration_to_seconds("invalid"))

    def test_calculate_match_score(self):
        spotify_title = "Starboy"
        spotify_artist = "The Weeknd"
        spotify_duration_ms = 230000

        candidate = {
            "videoId": "d380UOWxRnE",
            "title": "Starboy",
            "artists": [{"name": "The Weeknd"}],
            "duration": "3:50",
            "duration_seconds": 230
        }

        score = calculate_match_score(spotify_title, spotify_artist, spotify_duration_ms, candidate)
        self.assertGreaterEqual(score, 0.90)

    def test_find_best_track_match(self):
        candidates = [
            {
                "videoId": "wrong123",
                "title": "Something Completely Different",
                "artists": [{"name": "Other Artist"}],
                "duration": "4:00"
            },
            {
                "videoId": "correct123",
                "title": "Shape of You",
                "artists": [{"name": "Ed Sheeran"}],
                "duration": "3:53",
                "duration_seconds": 233
            }
        ]

        best_match = find_best_track_match("Shape of You", "Ed Sheeran", 233000, candidates)
        self.assertIsNotNone(best_match)
        cand, score = best_match
        self.assertEqual(cand["videoId"], "correct123")
        self.assertGreaterEqual(score, 0.85)

    def test_storage_operations(self):
        store = Storage(db_path=":memory:")

        # Test track match caching
        self.assertIsNone(store.get_track_match("sp_123"))
        store.save_track_match("sp_123", "yt_456", "Song A", "Artist B", "Song A", "Artist B", 0.95)
        match = store.get_track_match("sp_123")
        self.assertIsNotNone(match)
        self.assertEqual(match["video_id"], "yt_456")

        # Test liked tracks tracking
        self.assertFalse(store.is_like_migrated("sp_123"))
        store.mark_like_migrated("sp_123", "yt_456")
        self.assertTrue(store.is_like_migrated("sp_123"))

        # Test playlist tracking
        self.assertIsNone(store.get_migrated_playlist("pl_1"))
        store.save_migrated_playlist("pl_1", "yt_pl_1", "My Playlist", 10, 5)
        pl_info = store.get_migrated_playlist("pl_1")
        self.assertIsNotNone(pl_info)
        self.assertEqual(pl_info["ytmusic_playlist_id"], "yt_pl_1")

        self.assertFalse(store.is_playlist_track_added("pl_1", "sp_123"))
        store.mark_playlist_track_added("pl_1", "sp_123", "yt_456")
        self.assertTrue(store.is_playlist_track_added("pl_1", "sp_123"))

        # Test stats
        stats = store.get_summary_stats()
        self.assertEqual(stats["likes_migrated"], 1)
        self.assertEqual(stats["playlists_migrated"], 1)


if __name__ == "__main__":
    unittest.main()
