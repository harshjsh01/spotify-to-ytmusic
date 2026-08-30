/**
 * Spotify Followed Artists 1-Click Extractor
 * 1. Go to https://open.spotify.com/collection/artists (or click 'Artists' filter in Your Library on the left).
 * 2. Run this snippet in your Browser Console (F12 -> Console).
 * 3. It auto-scrolls through all your followed artists and downloads 'artists_data.json'.
 */
(async function() {
    console.log("👤 Followed Artists Collector Starting...");
    let artistsMap = new Map();

    let scroller = document.querySelector('[data-overlayscrollbars-viewport]') || document.querySelector('.main-view-container') || window;
    let noChangeCount = 0;
    let lastCount = 0;

    for (let i = 0; i < 300; i++) {
        // Collect all artist links and cards
        document.querySelectorAll('a[href*="/artist/"]').forEach(a => {
            let name = a.textContent.trim();
            // Filter out empty, verified tags, or metadata
            if (name && !name.toLowerCase().includes("verified") && name.length > 1 && !name.toLowerCase().includes("artist")) {
                // Remove trailing words like "Artist" or numbers if appended
                name = name.replace(/\s*Artist\s*$/i, "").trim();
                let key = name.toLowerCase();
                if (!artistsMap.has(key)) {
                    artistsMap.set(key, { id: a.href, name: name });
                }
            }
        });

        console.log(`Artists collected: ${artistsMap.size}`);

        if (scroller === window) window.scrollBy(0, 1000);
        else scroller.scrollTop += 1000;

        await new Promise(res => setTimeout(res, 200));

        if (artistsMap.size === lastCount) {
            noChangeCount++;
            if (noChangeCount > 20 && artistsMap.size > 10) break; // Reached end of followed artists
        } else {
            noChangeCount = 0;
            lastCount = artistsMap.size;
        }
    }

    let allArtists = Array.from(artistsMap.values());
    console.log(`🎉 Total Artists Captured: ${allArtists.length}! Downloading artists_data.json...`);

    let exportData = {
        liked_songs: [],
        followed_artists: allArtists,
        playlists: []
    };

    let blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "artists_data.json";
    document.body.appendChild(a);
    a.click();
})();
