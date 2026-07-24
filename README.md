# YouTube Content Analyzer

Extract and download transcripts from a specific YouTube channel.

The pipeline has two steps:

1. **`scraper.py`** – Uses `yt-dlp` to fetch all video metadata (URL, title,
   upload date, video ID) from a YouTube channel and saves it to
   `channels/<channel>/channel_videos.json`.
2. **`downloader.py`** – Reads the channel's `channel_videos.json`, fetches the
   English transcript (including auto-generated captions) for each video with
   `youtube-transcript-api`, and saves each transcript to
   `channels/<channel>/transcripts/[video_id].txt`. Videos without a transcript
   are logged to `channels/<channel>/failed_videos.json`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the scripts sequentially:

```bash
# Step 1 - build channel_videos.json for a channel
python scraper.py <channel_handle>

# Step 2 - download transcripts
python downloader.py <channel_handle>

# Example
python scraper.py starterstory
python downloader.py starterstory
```

## Configuration

- Pass the YouTube channel handle as a positional argument (with or without
  the leading `@`).
- Each channel's data is stored under `channels/<channel>/`.
- `downloader.py` is resumable: it skips videos whose transcript file already
  exists, and adds a randomized delay between requests.

## Output

```
channels/
  <channel_handle>/
    channel_videos.json   – scraped video metadata
    transcripts/          – one .txt file per video with a transcript
    failed_videos.json    – videos that had no transcript or errored out
```
