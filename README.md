# 🎵 Spotify to YouTube Music Auto-Migrator

An automated, smart, and resumable tool to migrate your **Liked Songs**, **Followed Artists**, and **Playlists** from Spotify to YouTube Music **without needing Spotify Developer Apps or Spotify Premium**.

---

## 🚀 Quick Setup & Usage Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 2. Export Your Spotify Liked Songs (Zero-Setup, Free Account Supported)

1. Open **[open.spotify.com](https://open.spotify.com)** in your browser (Chrome/Edge/Firefox) and log in.
2. In the left sidebar, click **"Liked Songs"** (the purple heart 💜).
3. Press **`F12`** to open Developer Tools ➔ click the **Console** tab.
4. Paste the following script and press **Enter**:

```javascript
(async function() {
    console.log("🎵 Full Liked Songs Collector Starting...");
    let songsMap = new Map();

    let scroller = document.querySelector('[data-overlayscrollbars-viewport]') || document.querySelector('.main-view-container') || window;
    let noChangeCount = 0;
    let lastCount = 0;

    for (let i = 0; i < 800; i++) {
        document.querySelectorAll('div[data-testid="tracklist-row"]').forEach(r => {
            let name = r.querySelector('a[data-testid="internal-track-link"], div[dir="auto"] span')?.textContent?.trim();
            let artists = Array.from(r.querySelectorAll('a[href*="/artist/"]')).map(a => a.textContent.trim()).filter(Boolean);
            if (name && artists.length) {
                let key = `${name} - ${artists.join(", ")}`;
                if (!songsMap.has(key)) {
                    songsMap.set(key, { name: name, artists: artists, artist_str: artists.join(", ") });
                }
            }
        });

        console.log(`Songs collected: ${songsMap.size}`);

        if (scroller === window) window.scrollBy(0, 1000);
        else scroller.scrollTop += 1000;

        await new Promise(res => setTimeout(res, 200));

        if (songsMap.size === lastCount) {
            noChangeCount++;
            if (noChangeCount > 25 && songsMap.size > 50) break;
        } else {
            noChangeCount = 0;
            lastCount = songsMap.size;
        }
    }

    let allSongs = Array.from(songsMap.values());
    console.log(`🎉 Total collected: ${allSongs.length} songs! Downloading...`);

    let blob = new Blob([JSON.stringify({ liked_songs: allSongs, followed_artists: [], playlists: [] }, null, 2)], { type: "application/json" });
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "liked_song_data.json";
    document.body.appendChild(a);
    a.click();
})();
```

5. The browser will auto-scroll, scan your tracks, and download **`liked_song_data.json`**.
6. Move `liked_song_data.json` into your project folder (or into a `data/` subfolder).

---

### 3. Connect YouTube Music (One-time)

1. Go to **[music.youtube.com](https://music.youtube.com)** in your browser and make sure you are logged in.
2. Press **`F12`** (Developer Tools) ➔ click the **Network** tab.
3. Filter by `browse` and click any tab on YouTube Music (e.g. Home or Explore).
4. Right-click the `browse` request ➔ **Copy** ➔ **Copy request headers**.
5. When running `python app.py`, paste your request headers into the prompt, press `Enter`, then type `DONE` and press `Enter` (saved automatically to `browser.json`).

---

### 4. Run Migration

Run the interactive CLI:
```bash
python app.py
```

Or run directly from the command line:

```bash
# Migrate Liked Songs directly
python app.py --likes

# Migrate Playlists only
python app.py --playlists

# Migrate Followed Artists only
python app.py --artists

# Migrate Everything (Full Migration)
python app.py --all
```

---

## ⚡ Features & How It Works

- **💖 Liked Songs Matching**: Searches YouTube Music using cleaned title & artist names with duration verification to like the exact songs on your YouTube Music account.
- **📁 Backup Playlist Creation**: In addition to liking the tracks, automatically creates a `Spotify Liked Songs (Migrated)` playlist on YouTube Music.
- **🛡️ Resumable Database (`migration_cache.db`)**: Every processed song and matched video ID is saved locally in SQLite. If stopped or interrupted, re-running instantly resumes right where it left off without duplicate API calls or searches.
- **📊 Summary Reports**: Generates detailed stats on matched, synced, and unmatched songs.
