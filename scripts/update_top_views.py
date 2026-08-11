#!/usr/bin/env python3
"""Refresh the three most-viewed public videos for the Video Library."""

import json
import re
import subprocess
import time
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_URL = "https://www.youtube.com/@tinuttslOfficial/videos"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "top-views.json"


def ytdlp_json(url, flat=False):
    command = ["yt-dlp", "--no-warnings", "--dump-single-json"]
    if flat:
        command.append("--flat-playlist")
    command.append(url)
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def fetch_public_view_count(video_id):
    request = Request(
        f"https://www.youtube.com/watch?v={video_id}&hl=en",
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
        },
    )
    with urlopen(request, timeout=20) as response:
        page = response.read().decode("utf-8", errors="ignore")
    match = re.search(r'"viewCount":"(\d+)"', page)
    if not match:
        raise RuntimeError(f"View count was unavailable for {video_id}")
    return int(match.group(1))


def main():
    channel = ytdlp_json(CHANNEL_URL, flat=True)
    videos = []
    for entry in channel.get("entries", []):
        video_id = entry.get("id")
        if not video_id:
            continue
        try:
            views = fetch_public_view_count(video_id)
        except Exception:
            continue
        videos.append({
            "title": entry.get("title") or "Untitled video",
            "views": int(views),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        })
        time.sleep(0.3)

    existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8")) if OUTPUT_PATH.exists() else {}
    if len(videos) < 3:
        if existing.get("videos"):
            return
        raise RuntimeError("Fewer than three public YouTube view counts were available")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel": CHANNEL_URL.replace("/videos", ""),
        "videos": sorted(videos, key=lambda video: video["views"], reverse=True)[:3],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
