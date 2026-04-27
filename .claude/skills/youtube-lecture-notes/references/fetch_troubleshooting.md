# Fetch Troubleshooting

Decision tree for when `scripts/fetch_transcript.py` fails. The script tries to handle each of these automatically, but if it can't, here's what to try by hand.

## SSL: CERTIFICATE_VERIFY_FAILED

The script checks for `/etc/ssl/certs/ca-certificates.crt` (Debian/Ubuntu/WSL), `/etc/pki/tls/certs/ca-bundle.crt` (RHEL), `/etc/ssl/cert.pem` (macOS / Alpine), then falls back to `certifi.where()`. If all of those fail:

```bash
# manually point at any valid CA bundle
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE
```

If `certifi` isn't installed:
```bash
uv pip install -p .venv-yt-notes/bin/python certifi
# or:
pip install certifi
```

## ensurepip is not available

System Python 3.10 on Debian/Ubuntu often ships without `ensurepip`. The script will use `uv` if it's on `$PATH`. If you don't have either:

```bash
# install uv (one-line, no sudo)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or install the system venv package:
```bash
sudo apt install python3-venv
```

## TranscriptsDisabled

The uploader turned off captions. Options, in order of effort:

1. **Supadata** — paid hosted API with AI-generated transcript fallback. Best if you need a few videos and don't want to set up Whisper.
2. **yt-dlp + Whisper** — fully local, fully free, ~real-time on a GPU.
   ```bash
   yt-dlp -x --audio-format mp3 -o '%(id)s.%(ext)s' "<url>"
   pip install -U faster-whisper
   python -c "
   from faster_whisper import WhisperModel
   m = WhisperModel('large-v3', device='cuda', compute_type='float16')
   segs, info = m.transcribe('<videoid>.mp3', language='en', vad_filter=True)
   for s in segs:
       print(f'[{s.start:.1f}-{s.end:.1f}] {s.text}')
   "
   ```
3. **Manual** — paste a few minutes from the YouTube auto-caption pane (Settings → Subtitles → Show transcript).

## NoTranscriptFound

The video has captions in some language other than the ones you asked for. List what's available:

```python
from youtube_transcript_api import YouTubeTranscriptApi
print(list(YouTubeTranscriptApi().list("<videoid>")))
```

Then re-run with `--lang <code> --lang en` to fall back through preferences. The `a.<code>` prefix means "auto-generated in <code>".

## Rate-limited (429 / RequestBlocked)

`youtube-transcript-api` has no built-in retry. Options:

- Wait. The throttle is per-IP and lifts in minutes.
- Run via a proxy with `GenericProxyConfig`:
  ```python
  from youtube_transcript_api.proxies import GenericProxyConfig
  api = YouTubeTranscriptApi(proxy_config=GenericProxyConfig(http_url="http://...", https_url="..."))
  ```
- For batch work (many videos), use Supadata or pace yourself ≥ 1 s between calls.

## VideoUnavailable

Could be: private, region-locked, deleted, or wrong ID. Try the URL in a browser (in incognito) to disambiguate. If it's region-locked, route through a proxy in the right region.

## The transcript is garbage / mistranscribed

Auto-generated captions on heavy-accent / domain-jargon talks (e.g., academic ML lectures with names) can be rough. Two paths:

- **Re-fetch with a manual track** if the uploader provided one. Manual captions are usually a separate `language_code` (e.g., `en` vs `a.en`).
- **Re-transcribe with Whisper.** Larger models (`large-v3`) handle accents and domain jargon much better than YouTube's baseline.
