"""Channel scraper.

Fetches all video metadata (URL, title, upload date, video ID) from a
YouTube channel using yt-dlp and stores the result in channel_videos.json.
"""

import argparse
import json
import os
import sys

from yt_dlp import YoutubeDL


def fetch_channel_videos(channel_url):
    """Return a list of video metadata dicts for the given channel URL."""
    ydl_opts = {
        # Do not download the videos, only extract metadata.
        "skip_download": True,
        # Only pull the flat playlist first, then resolve entries lazily.
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    # Use the /videos tab so we only pull uploaded videos.
    videos_url = channel_url.rstrip("/") + "/videos"

    videos = []
    print(f"Fetching video list from: {videos_url}")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(videos_url, download=False)

    if not info:
        raise RuntimeError("yt-dlp returned no data for the channel.")

    entries = info.get("entries") or []
    # Some channels nest entries (tabs -> playlist -> videos); flatten them.
    entries = list(_flatten_entries(entries))

    total = len(entries)
    print(f"Found {total} entries. Extracting metadata...")

    for index, entry in enumerate(entries, start=1):
        if not entry:
            continue

        video_id = entry.get("id")
        if not video_id:
            print(f"  [{index}/{total}] Skipping entry without a video ID.")
            continue

        video = {
            "video_id": video_id,
            "title": entry.get("title"),
            "url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
            "upload_date": entry.get("upload_date"),
        }
        videos.append(video)
        print(f"  [{index}/{total}] {video_id} - {video['title']}")

    return videos


def _flatten_entries(entries):
    """Recursively yield leaf entries from a possibly nested entry list."""
    for entry in entries:
        if entry and entry.get("entries"):
            yield from _flatten_entries(entry["entries"])
        else:
            yield entry


def main():
    parser = argparse.ArgumentParser(description="Scrape video metadata from a YouTube channel.")
    parser.add_argument("channel", help="YouTube channel handle (e.g. starterstory)")
    args = parser.parse_args()

    channel_name = args.channel.lstrip("@")
    channel_url = f"https://www.youtube.com/@{channel_name}"
    output_dir = os.path.join("channels", channel_name)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "channel_videos.json")

    try:
        videos = fetch_channel_videos(channel_url)
    except Exception as exc:  # noqa: BLE001 - top-level guard for CLI usage.
        print(f"ERROR: Failed to fetch channel videos: {exc}", file=sys.stderr)
        sys.exit(1)

    if not videos:
        print("No videos were found. Nothing to save.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "channel_url": channel_url,
        "video_count": len(videos),
        "videos": videos,
    }

    try:
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"ERROR: Could not write {output_file}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nSaved {len(videos)} videos to {output_file}")


if __name__ == "__main__":
    main()
