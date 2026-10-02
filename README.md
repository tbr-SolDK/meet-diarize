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

## Manual Copilot meeting minutes

This repository includes a `meeting-summary` skill and `meeting-assistant` /
`meeting-reviewer` custom agents for **manual, internal minutes**. Nothing runs
automatically after transcription, and the transcription scripts are unchanged.
Use a current authenticated Copilot CLI from this repository, with custom-agent
delegation and the question tool available:

```powershell
copilot skill list
copilot --agent meeting-assistant --excluded-tools skill,sql -i "Use /meeting-summary for output\team\2026-09-30-demo.json. This recording is approved for the configured Copilot processing. Load SKILL.md directly if the skill helper is unavailable."
```

Use one selected transcript, preferably WhisperX JSON. VTT/SRT are supported
but have unknown speaker attribution unless reliably established. The assistant
reads the complete source and matching metadata, asks only material missing
facts one at a time (skip allowed), drafts minutes, invokes exactly one
read-only reviewer, and reconciles its findings. Reusable confirmations avoid
repeated questions on the same unchanged recording.

**Language follows the meeting.** Reliable JSON `language` is used, but this
pipeline passes the user's transcription setting to WhisperX; it is not
guaranteed autodetection. Missing, invalid, conflicting or mixed language
requires a question, as does VTT/SRT without reliable matching metadata.
Danish and English are primary choices; another language can be supplied.
A user correction is authoritative. Skipping language stops drafting: there
is never a silent Danish default.

Outputs next to the source under `output\` preserve subfolders:
`<stem>.summary.md` contains timestamp-grounded minutes, and
`<stem>.meeting.json` contains versioned source identity, fact provenance,
recording-specific speaker mappings, optional confirmed attendance, language
choice and review state. Several speaker IDs may map to one person; mixed or
unknown IDs remain uncertain. Speaking and confirmed attendance (including
silent attendees) are separate. Missing owners/deadlines stay `Ikke aftalt` /
`Not agreed`; proposals and later reversed decisions are not final agreements.
Relative dates need a reliable meeting-date anchor. Originals are never edited.
Existing artifacts require overwrite consent; sources outside `output\`
require destination confirmation. Malformed, incompatible or stale sidecars
are surfaced rather than silently applied.

**Limits and privacy:** Local audio transcription does **not** mean local
Copilot inference. Ensure recordings are approved for the configured Copilot
processing before use. No credentials, private development recordings or other
external services are needed. This workflow does not publish, send messages,
create tasks externally, or commit meeting artifacts. Keep outputs under the
existing ignored `output\` tree; never force-add them. For an approved alternate
destination, arrange equivalent exclusions before saving.

The reviewer is configured with `read` / `search` aliases plus concrete local
`rg` / `glob` names. CLI 1.0.90-5 also exposes intrinsic `skill` / `sql` helpers
despite profile allowlists: the command above excludes those process-wide so
the reviewer is read/search-only (a parallel-read wrapper is harmless).
The assistant loads the skill file directly when the helper is excluded.
Verify effective tools
against installed CLI tool availability, not just YAML. Separate context is
not a truth guarantee, and review is against transcript text, not audio.
Unavailable delegation, unsafe permissions or incomplete source coverage permits
only a prominently marked **UNREVIEWED DRAFT** (or Danish equivalent), with
coverage and limitations persisted in both summary and sidecar. One reviewer
pass is mandatory for reviewed minutes; no self-review substitute or extra
chunk agents. A missing hashing capability prevents reusable metadata.

Shared policy and templates live in `.github\skills\meeting-summary\`;
role profiles live in `.github\agents\`. New profiles may require a fresh CLI
process; existing CLI skills can be reloaded with `/skills reload`.
See `examples\acceptance.md` under the skill for synthetic semantic checks,
including language questions, metadata reuse, injection, changed sources,
reversed decisions and partial/unavailable review. Distinguish static checks,
discovery/permissions, actual delegation and end-to-end behavior when reporting
verification. Manual fixture inspection does not prove live model behavior.
The dated execution record and unexercised checks are documented in
`examples\verification.md` under the skill; it includes discovered CLI permission
limitations and model errors caught during synthetic validation.
No new dependencies or executable summarization pipeline are installed.
