/**
 * Spotify 1-Click Library Extractor
 * Run this snippet in your Browser Console (F12 -> Console) on https://open.spotify.com
 * It extracts all your Liked Songs, Playlists, and Followed Artists into 'spotify_data.json'
 */
(async function() {
    console.log("%c🎵 Spotify Library Extractor Starting...", "color: #1DB954; font-size: 16px; font-weight: bold;");

    // 1. Get access token from active web player session
    let tokenResp = await fetch("https://open.spotify.com/get_access_token");
    let tokenData = await tokenResp.json();
    let token = tokenData.accessToken;
    if (!token) {
        console.error("Could not obtain access token. Make sure you are logged in on open.spotify.com.");
        return;
    }

    let authHeaders = { "Authorization": `Bearer ${token}` };

    // 2. Fetch User Profile
    let userResp = await fetch("https://api.spotify.com/v1/me", { headers: authHeaders });
    let userData = await userResp.json();
    let userName = userData.display_name || userData.id;
    console.log(`👤 Connected as: ${userName}`);

    let exportData = {
        user: userName,
        exported_at: new Date().toISOString(),
        liked_songs: [],
        followed_artists: [],
        playlists: []
    };

    // 3. Fetch Liked Songs
    console.log("💖 Fetching Liked Songs...");
    let nextTracksUrl = "https://api.spotify.com/v1/me/tracks?limit=50";
    while (nextTracksUrl) {
        let res = await fetch(nextTracksUrl, { headers: authHeaders });
        let data = await res.json();
        for (let item of (data.items || [])) {
            if (item.track) {
                exportData.liked_songs.push({
                    id: item.track.id,
                    name: item.track.name,
                    artists: item.track.artists.map(a => a.name),
                    artist_str: item.track.artists.map(a => a.name).join(", "),
                    album: item.track.album ? item.track.album.name : "",
                    duration_ms: item.track.duration_ms
                });
            }
        }
        nextTracksUrl = data.next;
    }
    console.log(`✔ Fetched ${exportData.liked_songs.length} liked songs.`);

    // 4. Fetch Followed Artists
    console.log("👤 Fetching Followed Artists...");
    let nextArtistsUrl = "https://api.spotify.com/v1/me/following?type=artist&limit=50";
    while (nextArtistsUrl) {
        let res = await fetch(nextArtistsUrl, { headers: authHeaders });
        let data = await res.json();
        let artistsObj = data.artists || {};
        for (let item of (artistsObj.items || [])) {
            exportData.followed_artists.push({
                id: item.id,
                name: item.name
            });
        }
        nextArtistsUrl = artistsObj.next;
    }
    console.log(`✔ Fetched ${exportData.followed_artists.length} followed artists.`);

    // 5. Fetch Playlists & their tracks
    console.log("📁 Fetching Playlists...");
    let nextPlaylistsUrl = "https://api.spotify.com/v1/me/playlists?limit=50";
    let playlistSummaries = [];
    while (nextPlaylistsUrl) {
        let res = await fetch(nextPlaylistsUrl, { headers: authHeaders });
        let data = await res.json();
        for (let p of (data.items || [])) {
            playlistSummaries.push({ id: p.id, name: p.name, description: p.description || "" });
        }
        nextPlaylistsUrl = data.next;
    }

    for (let pl of playlistSummaries) {
        console.log(`  -> Fetching tracks for playlist: '${pl.name}'...`);
        let plTracks = [];
        let nextPlTracksUrl = `https://api.spotify.com/v1/playlists/${pl.id}/tracks?limit=100`;
        while (nextPlTracksUrl) {
            let res = await fetch(nextPlTracksUrl, { headers: authHeaders });
            let data = await res.json();
            for (let item of (data.items || [])) {
                if (item.track) {
                    plTracks.push({
                        id: item.track.id,
                        name: item.track.name,
                        artists: item.track.artists ? item.track.artists.map(a => a.name) : [],
                        artist_str: item.track.artists ? item.track.artists.map(a => a.name).join(", ") : "",
                        album: item.track.album ? item.track.album.name : "",
                        duration_ms: item.track.duration_ms
                    });
                }
            }
            nextPlTracksUrl = data.next;
        }
        exportData.playlists.push({
            id: pl.id,
            name: pl.name,
            description: pl.description,
            tracks: plTracks
        });
    }

    // 6. Trigger Download of JSON
    let blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "spotify_data.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    console.log("%c🎉 Finished! 'spotify_data.json' has been downloaded. Move it to your 'youtube music' folder!", "color: #1DB954; font-size: 16px; font-weight: bold;");
})();
