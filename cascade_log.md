# Cascade Log

- **Create YouTube transcript extraction project** — Added `requirements.txt`, `scraper.py` (fetches channel video metadata to `channel_videos.json`), `downloader.py` (downloads English transcripts to `transcripts/` and logs failures to `failed_videos.json`), `README.md`, and `.gitignore`.
- **Fix downloader ParseError on every video** — Root cause was outdated `youtube-transcript-api` 0.6.3; upgraded to 1.x and updated `downloader.py` to the new instance-based API. Verified transcript fetching now works.
- **Add cookie authentication to downloader** — Parsed raw Chrome cookie string into a dict, injected it into a `requests.Session`, and passed as `http_client` to `YouTubeTranscriptApi` for authenticated requests.
- **Increase delay to avoid IP block** — Changed delay from 0.5–1.5s to 5–15s between requests after YouTube blocked the IP at ~30 requests.
- **Make cookie usage optional** — If `RAW_COOKIE_STRING` is empty, the downloader runs without cookies.
- **Update cookie & simplify format** — Replaced multi-line cookie constant with a single-line string for easy paste-and-replace.
- **Multi-channel support** — Renamed `transcripts/` to `transcripts_starterstory/`, refactored `scraper.py` and `downloader.py` to accept a channel handle as a CLI argument, and store all per-channel data under `channels/<channel>/`.
- **Consolidate legacy files** — Moved `channel_videos.json`, `failed_videos.json`, and `transcripts_starterstory/` into `channels/starterstory/` and cleaned up `.gitignore`.
- **Create batch processing script** — Added `process_all_channels.sh` to iterate through all channel directories, run scraper.py and downloader.py for each, with error handling and progress reporting.
- **Add delay between actions** — Added 5-second sleep after each scraper and downloader call in process_all_channels.sh.
- **Add timestamp to downloader output** — Added hh:mm:ss timestamp to transcript saved message in downloader.py for better progress tracking.
- **Implement retry mechanism for transient network errors** — Added exponential backoff retry (max 3 attempts, 2s backoff) for `ConnectionError` and `Timeout` exceptions in downloader.py to recover from transient YouTube API disconnections.
