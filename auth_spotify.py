import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

SCOPES = [
    "user-library-read",
    "user-follow-read",
    "playlist-read-private",
    "playlist-read-collaborative"
]

auth_manager = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=" ".join(SCOPES),
    cache_path=".spotify_cache",
    open_browser=True
)

print("\n------------------------------------------------------------")
print("1. Open this link in your browser to authorize:")
print(auth_manager.get_authorize_url())
print("------------------------------------------------------------\n")
print("Waiting for you to click 'Agree' in your browser...")

sp = spotipy.Spotify(auth_manager=auth_manager)
user = sp.current_user()
print(f"\n✔ Successfully authenticated Spotify for user: {user.get('display_name')} ({user.get('id')})")
print("Total Liked Songs:", sp.current_user_saved_tracks(limit=1).get("total", 0))
