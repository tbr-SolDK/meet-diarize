# Meeting Transcription

Transcribe recorded meetings locally with WhisperX. Drop recordings into `input\`, run one PowerShell script, and find transcripts in `output\`. Audio processing and speaker diarization run on this computer; the Hugging Face token is used to access the diarization model.

## Setup

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and run PowerShell from this project directory:

```powershell
.\pipeline\bootstrap-local.ps1
Copy-Item .env.example .env
```

Add a Hugging Face read token to `.env` as `HF_TOKEN`. The token needs access to `pyannote/speaker-diarization-community-1`. Keep `.env` private; it is ignored by Git.

## Transcribe meetings

Put recordings in `input\` (subfolders are supported), then run:

```powershell
.\pipeline\run-meetings.ps1
```

Supported formats include MP4, MOV, MKV, AVI, WebM, WMV, WAV, MP3, M4A, AAC, FLAC, OGG, and WMA. FFmpeg normalizes each recording to a WAV under `output\.audio\`; the extracted audio is kept after transcription. WhisperX writes VTT, SRT, and JSON transcripts under `output\`, preserving input subfolders. The original recordings are left unchanged. As the last step, `run-meetings.ps1` creates a `.review.html` file next to each VTT transcript. Open it in a browser to search the text and click a line to play the matching part of the original recording. Keep `input\` and `output\` in place so the local video link works. Review pages require `-OutputFormat vtt` or `-OutputFormat all` (the default).

At startup, the script asks which language is spoken in the meeting or recording. Enter a WhisperX language code, such as `da` for Danish, `en` for English, or `de` for German. There is no default language, and an empty answer prompts again. The selected language applies to all recordings in that run and is passed to WhisperX for transcription and alignment. Supply `-Language` to skip the prompt, for example when running unattended. Override other settings when needed:

```powershell
.\pipeline\run-meetings.ps1 -Language en -Model medium -OutputFormat vtt
```

Both `pipeline\convert-meetings.ps1` and `pipeline\diarize-meetings.ps1` can also be run separately. They support `-WhatIf` to preview actions. When running `diarize-meetings.ps1` directly, `-Language` is required; PowerShell prompts if it is omitted in an interactive session. For a single existing recording, run `pipeline\review-transcripts.py --transcript <path-to-vtt> --media <path-to-recording> --output <path-to-review.html>` with the bootstrapped Python.

## Offline use

The first run downloads WhisperX models and the diarization model. After those downloads complete, set `WHISPERX_OFFLINE=1` in `.env` to disable Hugging Face network access on later runs. Missing models will cause processing to fail rather than silently contacting Hugging Face.

## Transcript review and comparison tests

Run the lightweight review and comparison tests with the bootstrapped Python:

```powershell
& .\pipeline\.venv\Scripts\python.exe -m unittest discover -s .\pipeline -p 'test_*.py'
```

`pipeline\validate-transcripts.py` remains available for optional Teams-versus-WhisperX comparisons when a Teams reference VTT is available; the review page does not require one.
