import time
import sys
from ytmusicapi import YTMusic
from migrate_playlist_url import extract_spotify_playlist
from matcher import clean_title, find_best_track_match
from storage import Storage

yt = YTMusic("browser.json")
storage = Storage()
playlist_id = "PLcAHnBvVhlcM"

print("1. Scraping Spotify Rabbit Playlist (100 tracks)...")
name, tracks = extract_spotify_playlist("https://open.spotify.com/playlist/0V50Da6LqukljMWmvW5r7g")
print(f"Total Spotify tracks extracted: {len(tracks)}")

# Get current tracks in YT Music playlist
pl_data = yt.get_playlist(playlist_id, limit=200)
existing_tracks = pl_data.get("tracks", [])
existing_titles = set(t.get("title", "").lower() for t in existing_tracks)
print(f"Current tracks in YouTube Music Rabbit playlist: {len(existing_tracks)}")

missing_vids = []
for idx, t in enumerate(tracks, 1):
    title = t["title"]
    artists = t["artists"]
    artist_str = ", ".join(artists)

    # Check cache first
    cache_key = f"rabbit_{title}_{artist_str}"
    cached = storage.get_track_match(cache_key)
    vid = None
    if cached and cached.get("video_id"):
        vid = cached["video_id"]
    else:
        main_artist = artists[0] if artists else ""
        query = f"{clean_title(title)} {main_artist}".strip()
        candidates = yt.search(query, filter="songs", limit=5)
        match_res = find_best_track_match(title, main_artist, t.get("duration_ms"), candidates)
        if match_res:
            cand, conf = match_res
            vid = cand.get("videoId")
            storage.save_track_match(cache_key, vid, title, artist_str, cand.get("title", ""), "", conf)

    if vid:
        # Check if already added
        if not storage.is_playlist_track_added("rabbit_pl", cache_key):
            missing_vids.append((cache_key, title, vid))

print(f"2. Found {len(missing_vids)} tracks to add to YouTube Music.")

# Add tracks in batches of 15
chunk_size = 15
for i in range(0, len(missing_vids), chunk_size):
    chunk = missing_vids[i:i + chunk_size]
    vids = [v[2] for v in chunk]
    print(f"Adding batch {i+1} to {i+len(chunk)}...")
    try:
        res = yt.add_playlist_items(playlistId=playlist_id, videoIds=vids, duplicates=False)
        for cache_key, title, vid in chunk:
            storage.mark_playlist_track_added("rabbit_pl", cache_key, vid)
        time.sleep(1.0)
    except Exception as e:
        print(f"Batch failed: {e}. Adding individually...")
        for cache_key, title, vid in chunk:
            try:
                yt.add_playlist_items(playlistId=playlist_id, videoIds=[vid], duplicates=False)
                storage.mark_playlist_track_added("rabbit_pl", cache_key, vid)
                time.sleep(0.5)
            except Exception:
                pass

final_pl = yt.get_playlist(playlist_id, limit=200)
print(f"🎉 Final tracks in Rabbit playlist: {len(final_pl.get('tracks', []))}")
