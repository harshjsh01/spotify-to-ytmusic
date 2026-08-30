/**
 * Spotify DOM Auto-Scroll Extractor for Liked Songs & Playlists
 * Run this snippet while viewing https://open.spotify.com/collection/tracks (Liked Songs)
 */
(async function() {
    console.log("%c🎵 Spotify Track Auto-Extractor Starting...", "color: #1DB954; font-size: 16px; font-weight: bold;");

    let songsMap = new Map();

    function collectVisibleTracks() {
        let rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
        for (let row of rows) {
            let titleElem = row.querySelector('a[data-testid="internal-track-link"], div[dir="auto"] span');
            let artistElems = row.querySelectorAll('a[href*="/artist/"]');
            let durationElem = row.querySelector('div[data-encore-id="text"]:last-child') || row.querySelector('div:has(> span):last-child');

            let title = titleElem ? titleElem.textContent.trim() : "";
            let artists = Array.from(artistElems).map(a => a.textContent.trim()).filter(Boolean);
            
            if (title && artists.length > 0) {
                let key = `${title}---${artists.join(",")}`;
                if (!songsMap.has(key)) {
                    songsMap.set(key, {
                        id: key,
                        name: title,
                        artists: artists,
                        artist_str: artists.join(", ")
                    });
                }
            }
        }
    }

    // Scroll container
    let scrollContainer = document.querySelector('.main-view-container .os-viewport, div[data-overlayscrollbars-viewport="true"]') || window;
    
    console.log("📜 Auto-scrolling down to collect all tracks (Please wait ~10-15 seconds)...");
    
    let lastCount = 0;
    let unchangedAttempts = 0;

    while (unchangedAttempts < 5) {
        collectVisibleTracks();
        console.log(`  -> Collected ${songsMap.size} tracks so far...`);
        
        if (scrollContainer === window) {
            window.scrollBy(0, 1000);
        } else {
            scrollContainer.scrollBy(0, 1000);
        }

        await new Promise(r => setTimeout(r, 400));

        if (songsMap.size === lastCount) {
            unchangedAttempts++;
        } else {
            unchangedAttempts = 0;
            lastCount = songsMap.size;
        }
    }

    let likedSongs = Array.from(songsMap.values());
    console.log(`%c✔ Total tracks extracted: ${likedSongs.length}`, "color: #1DB954; font-size: 16px; font-weight: bold;");

    // Load existing artists if present
    let exportData = {
        liked_songs: likedSongs,
        followed_artists: [
            {"id": "Seedhe Maut", "name": "Seedhe Maut"},
            {"id": "Karan Aujla", "name": "Karan Aujla"},
            {"id": "Navaan Sandhu", "name": "Navaan Sandhu"},
            {"id": "Dhanda Nyoliwala", "name": "Dhanda Nyoliwala"},
            {"id": "Yo Yo Honey Singh", "name": "Yo Yo Honey Singh"},
            {"id": "Faris Shafi", "name": "Faris Shafi"},
            {"id": "Talal Qureshi", "name": "Talal Qureshi"},
            {"id": "Rawal", "name": "Rawal"},
            {"id": "Ikky", "name": "Ikky"},
            {"id": "aleemrk", "name": "aleemrk"},
            {"id": "Sonu Nigam", "name": "Sonu Nigam"},
            {"id": "Himesh Reshammiya", "name": "Himesh Reshammiya"},
            {"id": "Sez on the Beat", "name": "Sez on the Beat"},
            {"id": "Ab 17", "name": "Ab 17"}
        ],
        playlists: []
    };

    let blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "spotify_data.json";
    document.body.appendChild(a);
    a.click();
    console.log("%c🎉 Downloaded complete 'spotify_data.json' with all your liked songs!", "color: #1DB954; font-size: 16px; font-weight: bold;");
})();
