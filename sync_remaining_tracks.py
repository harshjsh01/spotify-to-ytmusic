import time
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ytmusicapi import YTMusic
from migrate_playlist_url import extract_spotify_playlist
from matcher import clean_title, find_best_track_match

yt = YTMusic("browser.json")
playlist_id = "PLcAHnBvVhlcM"

print("1. Fetching playlist status on YouTube Music...")
current_pl = yt.get_playlist(playlist_id, limit=200)
existing_tracks = current_pl.get("tracks", [])
existing_titles = set(t["title"].lower() for t in existing_tracks)
print(f"Current tracks in YouTube Music playlist: {len(existing_tracks)}")

print("2. Fetching Spotify tracks...")
name, tracks = extract_spotify_playlist("https://open.spotify.com/playlist/0V50Da6LqukljMWmvW5r7g")
print(f"Total Spotify tracks: {len(tracks)}")

# Find missing tracks
missing_vids = []
for idx, t in enumerate(tracks, 1):
    title = t["title"]
    artists = t["artists"]
    artist_str = ", ".join(artists)

    # Search YT
    main_artist = artists[0] if artists else ""
    query = f"{clean_title(title)} {main_artist}".strip()
    candidates = yt.search(query, filter="songs", limit=5)
    match_res = find_best_track_match(title, main_artist, t.get("duration_ms"), candidates)
    if match_res:
        cand, conf = match_res
        vid = cand.get("videoId")
        if vid:
            # Check if this video is already in the playlist
            if cand.get("title", "").lower() not in existing_titles and title.lower() not in existing_titles:
                missing_vids.append((title, vid))

print(f"3. Found {len(missing_vids)} missing tracks to add to YouTube Music.")

# Add missing tracks in chunks of 10
chunk_size = 10
for i in range(0, len(missing_vids), chunk_size):
    chunk = missing_vids[i:i + chunk_size]
    vids = [v[1] for v in chunk]
    titles = [v[0] for v in chunk]
    print(f"Adding batch {i+1}-{i+len(chunk)}: {', '.join(titles[:3])}...")
    try:
        yt.add_playlist_items(playlistId=playlist_id, videoIds=vids, duplicates=False)
        time.sleep(1.0)
    except Exception as e:
        print(f"Batch failed: {e}. Adding individually...")
        for name_s, vid in chunk:
            try:
                yt.add_playlist_items(playlistId=playlist_id, videoIds=[vid], duplicates=False)
                time.sleep(0.5)
            except Exception:
                pass

# Verify final count
final_pl = yt.get_playlist(playlist_id, limit=200)
print(f"\n🎉 Final tracks in YouTube Music 'Rabbit' playlist: {len(final_pl.get('tracks', []))}")
