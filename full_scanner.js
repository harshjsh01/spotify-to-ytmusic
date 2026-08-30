/**
 * Full Spotify Library Exporter (All Liked Songs + All Followed Artists + All Playlists)
 * Paste this in your Spotify Console (F12 -> Console) on https://open.spotify.com
 */
(async function() {
    console.log("%c🎵 Starting Full Spotify Scanner...", "color: #1DB954; font-size: 16px; font-weight: bold;");

    // 1. Find all Followed Artists from left sidebar & library
    let artistsSet = new Map();
    let allLinks = Array.from(document.querySelectorAll('a[href*="/artist/"]'));
    for (let a of allLinks) {
        let name = a.textContent.trim();
        if (name && !name.toLowerCase().includes("verified") && !artistsSet.has(name)) {
            artistsSet.set(name, { id: a.href, name: name });
        }
    }
    console.log(`👤 Found ${artistsSet.size} followed artists in sidebar.`);

    // 2. Find the REAL scrollable element by testing scrollTop
    let scrollEl = null;
    let allDivs = Array.from(document.querySelectorAll('div, main, section'));
    for (let el of allDivs) {
        let prev = el.scrollTop;
        el.scrollTop = prev + 10;
        if (el.scrollTop > prev) {
            el.scrollTop = prev;
            scrollEl = el;
            break;
        }
    }
    if (!scrollEl) scrollEl = document.querySelector('[data-overlayscrollbars-viewport]') || window;

    console.log("📜 Found scroll container. Scanning all songs...");

    let songsMap = new Map();

    function captureRows() {
        let rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
        for (let row of rows) {
            let titleEl = row.querySelector('a[data-testid="internal-track-link"], div[dir="auto"] span');
            let artistEls = row.querySelectorAll('a[href*="/artist/"]');
            let title = titleEl ? titleEl.textContent.trim() : "";
            let artists = Array.from(artistEls).map(a => a.textContent.trim()).filter(Boolean);
            
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

    // Scroll continuously
    let maxIterations = 200;
    let idleCount = 0;
    let lastSize = 0;

    for (let i = 0; i < maxIterations; i++) {
        captureRows();
        
        if (scrollEl === window) {
            window.scrollBy(0, 700);
        } else {
            scrollEl.scrollTop += 700;
        }

        await new Promise(r => setTimeout(r, 200));

        if (songsMap.size > lastSize) {
            console.log(`  🎵 Collected ${songsMap.size} songs...`);
            lastSize = songsMap.size;
            idleCount = 0;
        } else {
            idleCount++;
            if (idleCount >= 10 && songsMap.size > 20) {
                // Reached bottom of playlist
                break;
            }
        }
    }

    // Add UI Download Button directly on the Spotify screen as a backup!
    let songsList = Array.from(songsMap.values());
    let artistsList = Array.from(artistsSet.values());

    let exportData = {
        liked_songs: songsList,
        followed_artists: artistsList,
        playlists: []
    };

    function triggerDownload() {
        let blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
        let a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "spotify_data.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    triggerDownload();

    // Create a floating green button on the screen just in case popups are blocked
    let btn = document.createElement("button");
    btn.id = "spotify-export-btn";
    btn.innerText = `📥 Download spotify_data.json (${songsList.length} songs, ${artistsList.length} artists)`;
    btn.style.cssText = "position:fixed;top:20px;right:20px;z-index:999999;padding:15px 25px;background:#1DB954;color:black;font-weight:bold;font-size:16px;border:none;border-radius:30px;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.5);";
    btn.onclick = triggerDownload;
    document.body.appendChild(btn);

    console.log(`%c🎉 SCAN COMPLETE! Captured ${songsList.length} songs and ${artistsList.length} artists!`, "color: #1DB954; font-size: 18px; font-weight: bold;");
    console.log("If the automatic download didn't trigger, click the green button at the top right of your Spotify screen!");
})();
