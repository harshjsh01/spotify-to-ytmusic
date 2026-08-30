/**
 * Spotify Liked Songs 1-Click Extractor
 * Run this snippet in your Browser Console (F12 -> Console) on https://open.spotify.com/collection/tracks
 * It auto-scrolls down through all your songs and downloads 'liked_song_data.json'.
 */
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
