import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from rapidfuzz import fuzz
    def text_similarity(s1: str, s2: str) -> float:
        return fuzz.token_set_ratio(s1.lower(), s2.lower()) / 100.0
except ImportError:
    import difflib
    def text_similarity(s1: str, s2: str) -> float:
        return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def clean_title(title: str) -> str:
    """Cleans up noise in Spotify / YT Music titles for better search accuracy."""
    cleaned = title
    # Remove remastered tags, e.g. - 2011 Remaster, (Remastered 2020), (Live / Remastered 2013)
    cleaned = re.sub(r"[\(\[\-]\s*(?:[^\)\]]*\s*/\s*)?(?:\d{4}\s*)?remaster(?:ed)?(?:\s*\d{4})?\s*[\)\]]?", "", cleaned, flags=re.IGNORECASE)
    # Remove bonus track / deluxe / edition tags
    cleaned = re.sub(r"[\(\[\-]\s*(?:deluxe|bonus track|anniversary|expanded|special)\s*(?:edition|version)?\s*[\)\]]?", "", cleaned, flags=re.IGNORECASE)
    # Remove official audio / video tags
    cleaned = re.sub(r"[\(\[\-]\s*official\s*(?:audio|video|music video|lyric video|lyrics)?\s*[\)\]]?", "", cleaned, flags=re.IGNORECASE)
    # Remove standalone featuring in parens/brackets e.g. (feat. Artist)
    cleaned = re.sub(r"[\(\[\-]\s*(?:feat\.|featuring|ft\.)\s*[^)\]]+[\)\]]?", "", cleaned, flags=re.IGNORECASE)
    # Remove leading/trailing hyphens and whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned if cleaned else title


def parse_duration_to_seconds(duration_str: Optional[str]) -> Optional[int]:
    if not duration_str:
        return None
    parts = duration_str.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None
    return None


def calculate_match_score(
    spotify_title: str,
    spotify_artist: str,
    spotify_duration_ms: Optional[int],
    candidate: Dict[str, Any]
) -> float:
    """
    Computes a match score from 0.0 to 1.0 based on title, artist, and duration.
    """
    cand_title = candidate.get("title", "")
    cand_artists = [a.get("name", "") for a in candidate.get("artists", [])]
    cand_artist_str = " ".join(cand_artists)

    clean_s_title = clean_title(spotify_title)
    clean_c_title = clean_title(cand_title)

    title_sim = text_similarity(clean_s_title, clean_c_title)
    artist_sim = text_similarity(spotify_artist, cand_artist_str)

    score = (title_sim * 0.6) + (artist_sim * 0.4)

    # Duration comparison if available
    cand_duration_sec = candidate.get("duration_seconds")
    if not cand_duration_sec and "duration" in candidate:
        cand_duration_sec = parse_duration_to_seconds(candidate["duration"])

    if spotify_duration_ms and cand_duration_sec:
        spotify_sec = spotify_duration_ms / 1000.0
        diff = abs(spotify_sec - cand_duration_sec)
        if diff <= 5:
            score += 0.05
        elif diff > 30:
            # Significant duration mismatch (e.g. extended version or teaser)
            score -= 0.15

    return max(0.0, min(1.0, score))


def find_best_track_match(
    spotify_title: str,
    spotify_artist: str,
    spotify_duration_ms: Optional[int],
    candidates: List[Dict[str, Any]],
    min_confidence: float = 0.65
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Iterates over YT Music search candidates and returns the best match if above threshold.
    """
    best_candidate = None
    best_score = 0.0

    for cand in candidates:
        # Video ID must exist
        video_id = cand.get("videoId")
        if not video_id:
            continue

        score = calculate_match_score(spotify_title, spotify_artist, spotify_duration_ms, cand)
        if score > best_score:
            best_score = score
            best_candidate = cand

    if best_candidate and best_score >= min_confidence:
        return best_candidate, best_score

    return None
