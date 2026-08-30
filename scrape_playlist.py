import requests
import json
import re

url = "https://open.spotify.com/embed/playlist/0V50Da6LqukljMWmvW5r7g"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers)
print("HTTP Status:", resp.status_code)

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
if match:
    data = json.loads(match.group(1))
    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
    name = entity.get("name", "Migrated Playlist")
    tracklist = entity.get("trackList", [])
    print(f"Playlist Name: '{name}'")
    print(f"Total Tracks Found in embed: {len(tracklist)}")
    for idx, t in enumerate(tracklist, 1):
        print(f"[{idx}] {t.get('title')} - {t.get('subtitle')}")
else:
    # Check open.spotify.com/playlist html
    print("Next data not found in embed. Checking main page...")
    r2 = requests.get("https://open.spotify.com/playlist/0V50Da6LqukljMWmvW5r7g", headers=headers)
    m2 = re.search(r'<script id="session" type="application/json">(.*?)</script>', r2.text)
    print("Session found in main page:", bool(m2))
