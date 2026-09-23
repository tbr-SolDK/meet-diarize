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

Supported formats include MP4, MOV, MKV, AVI, WebM, WMV, WAV, MP3, M4A, AAC, FLAC, OGG, and WMA. FFmpeg normalizes each recording to a temporary WAV under `output\.audio\`; WhisperX writes VTT, SRT, and JSON transcripts under `output\`, preserving input subfolders. The original recordings are left unchanged.

The default language is Danish (`da`), model is `medium`, device is CPU, and compute type is `int8`. Override settings when needed:

```powershell
.\pipeline\run-meetings.ps1 -Language en -Model medium -OutputFormat vtt
```

Both `pipeline\convert-meetings.ps1` and `pipeline\diarize-meetings.ps1` can also be run separately. They support `-WhatIf` to preview actions.

## Offline use

The first run downloads WhisperX models and the diarization model. After those downloads complete, set `WHISPERX_OFFLINE=1` in `.env` to disable Hugging Face network access on later runs. Missing models will cause processing to fail rather than silently contacting Hugging Face.

## Transcript comparison tests

Run the lightweight transcript parser/alignment tests with the bootstrapped Python:

```powershell
& .\pipeline\.venv\Scripts\python.exe -m unittest .\pipeline\test_validate_transcripts.py
```
