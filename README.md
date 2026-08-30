# 🎵 Spotify to YouTube Music Auto-Migrator

An automated, intelligent, and resumable Python tool to migrate your **Liked Songs**, **Followed Artists**, and **Playlists** from Spotify to YouTube Music without manual effort.

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Tool
```bash
python app.py
```

---

## 🔑 Authentication Setup (One-time)

### 1. Spotify Credentials
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in and click **"Create app"**.
   - **App name**: `MusicMigrator` (or any name)
   - **Redirect URI**: `http://127.0.0.1:8888/callback` *(Exact URL)*
   - Select **Web API**, accept terms, and click **Save**.
3. Go to **Settings** in your app and copy your **Client ID** and **Client Secret**.
4. The tool will prompt for these on first run and save them automatically in `.env`.

### 2. YouTube Music Authentication
When prompted by the tool:
1. Open [music.youtube.com](https://music.youtube.com) in your browser (Chrome/Edge/Firefox) and make sure you are logged in.
2. Press **F12** (Developer Tools) ➔ click the **Network** tab.
3. Filter by `browse` or click anywhere on the YouTube Music page.
4. Right-click any `browse` or `next` POST request ➔ **Copy** ➔ **Copy request headers**.
5. Paste them into the terminal when prompted (and type `DONE`). This creates `browser.json`.

---

## 🚀 Features

- **💖 Liked Songs Migration**:
  - Automatically searches each Spotify liked track on YouTube Music with high-accuracy title & duration matching.
  - Rates each matched song as **LIKE** on YouTube Music (appearing in your YouTube Music "Liked Music" auto-playlist).
  - Also optionally creates a backup playlist `Spotify Liked Songs (Migrated)` on YouTube Music.
- **👤 Followed Artists**:
  - Searches for each artist's official YouTube Music artist channel and automatically subscribes to them.
- **📁 Custom Playlists**:
  - Recreates all your Spotify playlists on YouTube Music.
  - Matches and adds all songs in batch.
  - Option to migrate all playlists at once or choose specific ones.
- **🛡️ Resumable & Safe (SQLite Cache)**:
  - Tracks every migrated song and playlist in local SQLite database (`migration_cache.db`).
  - If stopped or interrupted, rerunning will instantly resume without re-downloading or creating duplicate tracks.
- **📊 Detailed Report**:
  - Outputs summary statistics and logs any unmatched songs into `migration_summary.json`.

---

## 🛠️ Command-Line Usage

You can also run specific tasks directly via CLI flags:

```bash
# Run full migration (Likes + Artists + Playlists)
python app.py --all

# Migrate Liked Songs only
python app.py --likes

# Migrate Playlists only
python app.py --playlists

# Migrate Followed Artists only
python app.py --artists
```
