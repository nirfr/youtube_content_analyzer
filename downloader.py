"""Transcript downloader.

Reads channel_videos.json, fetches the English transcript for each video
(including auto-generated captions) and stores each one as a text file in
the transcripts/ folder. Videos without a transcript are logged to
failed_videos.json.
"""

import argparse
import datetime
import json
import os
import random
import sys
import time
from requests.exceptions import ConnectionError, Timeout

from requests import Session
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

LANGUAGES = ["en", "en-US", "en-GB"]
MIN_DELAY = 60
MAX_DELAY = 120
MAX_RETRIES = 3
RETRY_BACKOFF = 2

RAW_COOKIE_STRING = ""


def fetch_transcript_with_retry(api, video_id):
    """Fetch transcript with exponential backoff retry for transient errors."""
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            return fetch_transcript_text(api, video_id)
        except (ConnectionError, Timeout) as exc:
            last_exception = exc
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF ** attempt
                print(f"    Retry {attempt + 1}/{MAX_RETRIES - 1} after {wait_time}s...", end=" ", flush=True)
                time.sleep(wait_time)
            else:
                print()
        except Exception:
            raise
    raise last_exception


def parse_cookie_string(raw_cookie):
    """Parse a raw browser cookie string into a dict."""
    cookies = {}
    for pair in raw_cookie.split(";"):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def load_videos(path):
    """Load the list of videos from the scraper output file."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run scraper.py first to generate it."
        )

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    videos = data.get("videos", [])
    if not videos:
        raise ValueError(f"No videos found in {path}.")
    return videos


def fetch_transcript_text(api, video_id):
    """Return the transcript for a video as a single text string.

    Prefers manually created English transcripts, then falls back to
    auto-generated English captions. Raises on failure.
    """
    transcript_list = api.list(video_id)

    try:
        transcript = transcript_list.find_manually_created_transcript(LANGUAGES)
    except NoTranscriptFound:
        transcript = transcript_list.find_generated_transcript(LANGUAGES)

    fetched = transcript.fetch()
    return "\n".join(snippet.text for snippet in fetched if snippet.text)


def save_transcript(transcripts_dir, video_id, text):
    """Write the transcript text to transcripts/[video_id].txt."""
    path = os.path.join(transcripts_dir, f"{video_id}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def save_failed(failed_file, failed):
    """Persist the list of failed videos to failed_file."""
    with open(failed_file, "w", encoding="utf-8") as fh:
        json.dump(
            {"failed_count": len(failed), "videos": failed},
            fh,
            indent=2,
            ensure_ascii=False,
        )


def main():
    parser = argparse.ArgumentParser(description="Download transcripts for a YouTube channel.")
    parser.add_argument("channel", help="YouTube channel handle (e.g. starterstory)")
    args = parser.parse_args()

    channel_name = args.channel.lstrip("@")
    channel_dir = os.path.join("channels", channel_name)
    input_file = os.path.join(channel_dir, "channel_videos.json")
    transcripts_dir = os.path.join(channel_dir, "transcripts")
    failed_file = os.path.join(channel_dir, "failed_videos.json")

    try:
        videos = load_videos(input_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(transcripts_dir, exist_ok=True)

    if RAW_COOKIE_STRING:
        cookies = parse_cookie_string(RAW_COOKIE_STRING)
        session = Session()
        session.cookies.update(cookies)
        api = YouTubeTranscriptApi(http_client=session)
    else:
        api = YouTubeTranscriptApi()
    total = len(videos)
    succeeded = 0
    failed = []

    print(f"Processing {total} videos...\n")

    for index, video in enumerate(videos, start=1):
        video_id = video.get("video_id")
        title = video.get("title") or "(unknown title)"

        if not video_id:
            print(f"  [{index}/{total}] Skipping entry without a video ID.")
            continue

        # Skip videos we already downloaded so the script is resumable.
        existing = os.path.join(transcripts_dir, f"{video_id}.txt")
        if os.path.exists(existing):
            print(f"  [{index}/{total}] {video_id} - already downloaded, skipping.")
            succeeded += 1
            continue

        try:
            text = fetch_transcript_with_retry(api, video_id)
            save_transcript(transcripts_dir, video_id, text)
            succeeded += 1
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"  [{index}/{total}] {video_id} - transcript saved. [{timestamp}]")
        except (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        ) as exc:
            reason = type(exc).__name__
            print(f"  [{index}/{total}] {video_id} - no transcript ({reason}).")
            failed.append({**video, "reason": reason})
        except Exception as exc:  # noqa: BLE001 - keep processing remaining videos.
            reason = f"{type(exc).__name__}: {exc}"
            print(f"  [{index}/{total}] {video_id} - error ({reason}).")
            failed.append({**video, "reason": reason})

        # Randomized delay to reduce the chance of rate limiting.
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    save_failed(failed_file, failed)

    print("\nDone.")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed:    {len(failed)} (logged to {failed_file})")
    print(f"  Transcripts saved in: {transcripts_dir}/")


if __name__ == "__main__":
    main()
