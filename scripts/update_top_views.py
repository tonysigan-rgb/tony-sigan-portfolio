#!/usr/bin/env python3
"""Refresh the three most-viewed public videos for the Video Library."""

import json
import subprocess
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


def main():
    channel = ytdlp_json(CHANNEL_URL, flat=True)
    videos = []
    for entry in channel.get("entries", []):
        video_id = entry.get("id")
        if not video_id:
            continue
        details = ytdlp_json(f"https://www.youtube.com/watch?v={video_id}")
        views = details.get("view_count")
        if views is None:
            continue
        videos.append({
            "title": details.get("title") or entry.get("title") or "Untitled video",
            "views": int(views),
            "url": details.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": details.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel": CHANNEL_URL.replace("/videos", ""),
        "videos": sorted(videos, key=lambda video: video["views"], reverse=True)[:3],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
