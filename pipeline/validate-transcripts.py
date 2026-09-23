#!/usr/bin/env python3
"""Compare a Teams WebVTT transcript with a WhisperX WebVTT transcript locally."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Iterable

TIMESTAMP = re.compile(
    r"(?:(?P<hours>\d{2}):)?(?P<minutes>\d{2}):(?P<seconds>\d{2})[.,](?P<milliseconds>\d{3})"
)
TIMING_LINE = re.compile(r"^(?P<start>\S+)\s+-->\s+(?P<end>\S+)")
TAG = re.compile(r"<[^>]+>")
WHISPERX_SPEAKER = re.compile(r"^\s*\[SPEAKER_\d+\]:\s*", re.IGNORECASE)
TOKEN = re.compile(r"[\wæøåÆØÅ]+", re.UNICODE)
DEFAULT_WINDOW_SECONDS = 20.0


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass
class WindowResult:
    start: float
    end: float
    reference_raw: str
    candidate_raw: str
    reference_tokens: list[str]
    candidate_tokens: list[str]
    substitutions: int
    deletions: int
    insertions: int
    matches: int
    overlap_seconds: float
    status: str

    @property
    def reference_count(self) -> int:
        return len(self.reference_tokens)

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_tokens)

    @property
    def errors(self) -> int:
        return self.substitutions + self.deletions + self.insertions

    @property
    def wer(self) -> float | None:
        return self.errors / self.reference_count if self.reference_count else None


def timestamp_to_seconds(value: str) -> float:
    match = TIMESTAMP.match(value)
    if not match:
        raise ValueError(f"Invalid WebVTT timestamp: {value}")
    parts = {name: int(number or 0) for name, number in match.groupdict().items()}
    return parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"] + parts["milliseconds"] / 1000


def format_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02}.{milliseconds:03}"


def parse_vtt(path: Path) -> list[Cue]:
    """Read common Teams and WhisperX VTT variants without third-party packages."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    cues: list[Cue] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line == "WEBVTT" or line.startswith("NOTE") or line.startswith("STYLE"):
            index += 1
            continue
        timing_match = TIMING_LINE.match(line)
        if not timing_match:
            index += 1
            if index >= len(lines):
                continue
            timing_match = TIMING_LINE.match(lines[index].strip())
            if not timing_match:
                continue
        start = timestamp_to_seconds(timing_match.group("start"))
        end = timestamp_to_seconds(timing_match.group("end"))
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index].strip())
            index += 1
        if end > start and text_lines:
            cues.append(Cue(start=start, end=end, text=" ".join(text_lines)))
    return cues


def clean_display_text(text: str) -> str:
    text = WHISPERX_SPEAKER.sub("", text)
    text = TAG.sub("", text)
    return " ".join(text.split())


def normalize_tokens(text: str) -> list[str]:
    cleaned = clean_display_text(text)
    cleaned = unicodedata.normalize("NFKC", cleaned).casefold()
    return TOKEN.findall(cleaned)


def overlapping_cues(cues: Iterable[Cue], start: float, end: float) -> list[Cue]:
    return [cue for cue in cues if cue.start < end and cue.end > start]


def cue_text(cues: Iterable[Cue]) -> str:
    return " ".join(clean_display_text(cue.text) for cue in cues)


def duration(cues: Iterable[Cue]) -> float:
    return sum(cue.end - cue.start for cue in cues)


def time_overlap(reference: list[Cue], candidate: list[Cue]) -> float:
    total = 0.0
    for reference_cue in reference:
        for candidate_cue in candidate:
            total += max(0.0, min(reference_cue.end, candidate_cue.end) - max(reference_cue.start, candidate_cue.start))
    return total


def edit_counts(reference: list[str], candidate: list[str]) -> tuple[int, int, int, int]:
    """Return substitutions, deletions, insertions, matches using Levenshtein backtracking."""
    operations = edit_operations(reference, candidate)
    return (
        sum(operation == "substitution" for operation, _, _ in operations),
        sum(operation == "deletion" for operation, _, _ in operations),
        sum(operation == "insertion" for operation, _, _ in operations),
        sum(operation == "match" for operation, _, _ in operations),
    )


def edit_operations(reference: list[str], candidate: list[str]) -> list[tuple[str, str | None, str | None]]:
    """Align tokens for both counting and the side-by-side review display."""
    rows, columns = len(reference) + 1, len(candidate) + 1
    matrix = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        matrix[row][0] = row
    for column in range(columns):
        matrix[0][column] = column
    for row in range(1, rows):
        for column in range(1, columns):
            matrix[row][column] = min(
                matrix[row - 1][column] + 1,
                matrix[row][column - 1] + 1,
                matrix[row - 1][column - 1] + (reference[row - 1] != candidate[column - 1]),
            )

    row, column = len(reference), len(candidate)
    operations: list[tuple[str, str | None, str | None]] = []
    while row or column:
        if row and column and matrix[row][column] == matrix[row - 1][column - 1] + (reference[row - 1] != candidate[column - 1]):
            if reference[row - 1] == candidate[column - 1]:
                operations.append(("match", reference[row - 1], candidate[column - 1]))
            else:
                operations.append(("substitution", reference[row - 1], candidate[column - 1]))
            row -= 1
            column -= 1
        elif row and matrix[row][column] == matrix[row - 1][column] + 1:
            operations.append(("deletion", reference[row - 1], None))
            row -= 1
        else:
            operations.append(("insertion", None, candidate[column - 1]))
            column -= 1
    return list(reversed(operations))


def build_windows(reference: list[Cue], candidate: list[Cue], window_seconds: float) -> list[WindowResult]:
    latest_end = max((cue.end for cue in [*reference, *candidate]), default=0.0)
    results: list[WindowResult] = []
    start = 0.0
    while start < latest_end:
        end = min(start + window_seconds, latest_end)
        reference_slice = overlapping_cues(reference, start, end)
        candidate_slice = overlapping_cues(candidate, start, end)
        reference_raw = cue_text(reference_slice)
        candidate_raw = cue_text(candidate_slice)
        reference_tokens = normalize_tokens(reference_raw)
        candidate_tokens = normalize_tokens(candidate_raw)
        substitutions, deletions, insertions, matches = edit_counts(reference_tokens, candidate_tokens)
        overlap = time_overlap(reference_slice, candidate_slice)
        if not reference_tokens and not candidate_tokens:
            status = "empty"
        elif not reference_tokens or not candidate_tokens:
            status = "unmatched"
        elif substitutions + deletions + insertions == 0:
            status = "match"
        else:
            status = "difference"
        results.append(
            WindowResult(
                start=start,
                end=end,
                reference_raw=reference_raw,
                candidate_raw=candidate_raw,
                reference_tokens=reference_tokens,
                candidate_tokens=candidate_tokens,
                substitutions=substitutions,
                deletions=deletions,
                insertions=insertions,
                matches=matches,
                overlap_seconds=overlap,
                status=status,
            )
        )
        start = end
    return results


def summarize(reference: list[Cue], candidate: list[Cue], windows: list[WindowResult]) -> dict[str, object]:
    populated = [window for window in windows if window.status != "empty"]
    reference_tokens = sum(window.reference_count for window in populated)
    candidate_tokens = sum(window.candidate_count for window in populated)
    substitutions = sum(window.substitutions for window in populated)
    deletions = sum(window.deletions for window in populated)
    insertions = sum(window.insertions for window in populated)
    matches = sum(window.matches for window in populated)
    denominator_precision = matches + insertions + substitutions
    denominator_recall = matches + deletions + substitutions
    precision = matches / denominator_precision if denominator_precision else 1.0
    recall = matches / denominator_recall if denominator_recall else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    reference_duration = duration(reference)
    candidate_duration = duration(candidate)
    overlapping_duration = time_overlap(reference, candidate)
    overlap_ratio = overlapping_duration / reference_duration if reference_duration else 0.0
    disagreement = [window for window in populated if window.status != "match"]
    return {
        "reference_cues": len(reference),
        "candidate_cues": len(candidate),
        "reference_speech_seconds": round(reference_duration, 3),
        "candidate_speech_seconds": round(candidate_duration, 3),
        "temporal_overlap_seconds": round(overlapping_duration, 3),
        "reference_temporal_coverage": round(overlap_ratio, 4),
        "reference_tokens": reference_tokens,
        "candidate_tokens": candidate_tokens,
        "matches": matches,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "word_error_rate": round((substitutions + deletions + insertions) / reference_tokens, 4) if reference_tokens else None,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "windows_compared": len(populated),
        "windows_with_differences": len(disagreement),
        "unmatched_windows": sum(window.status == "unmatched" for window in populated),
    }


def html_report(report: dict[str, object]) -> str:
    summary = report["summary"]
    rows = report["windows"]
    metrics = [
        (
            "F1 agreement",
            f"{summary['f1']:.1%}",
            "Det afbalancerede mål for ord, som de to transskriptioner er enige om. Det medtages som det bedste samlede signal, fordi det vægter både manglende og ekstra ord.",
        ),
        (
            "Word error rate",
            f"{summary['word_error_rate']:.1%}" if summary["word_error_rate"] is not None else "n/a",
            "Andelen af referenceord, der kræver indsættelse, sletning eller erstatning for at ligne kandidatteksten. Det viser omfanget af tekstlige afvigelser, men er ikke en absolut WhisperX-fejlrate.",
        ),
        (
            "Reference coverage",
            f"{summary['reference_temporal_coverage']:.1%}",
            "Den del af Teams-referencens taletid, der tidsmæssigt overlapper WhisperX. Det medtages for at opdage manglende eller forskudte afsnit, som et rent ordmål kan skjule.",
        ),
        (
            "Reference words",
            str(summary["reference_tokens"]),
            "Antal normaliserede ord fra Teams-referencen, som indgår i sammenligningen. Det viser datamængden bag procenttallene og gør rapporter fra korte og lange møder sammenlignelige.",
        ),
        (
            "Differences",
            f"{summary['windows_with_differences']} / {summary['windows_compared']}",
            "Antal tidsvinduer med mindst én tekstafvigelse ud af alle vinduer med tale. Det viser, hvor bredt afvigelserne er fordelt, og hvilke vinduer der bør gennemgås med lyd.",
        ),
    ]
    metric_html = "".join(
        "<section class='metric'><span>{label}</span><strong>{value}</strong><p>{description}</p></section>".format(
            label=html.escape(label), value=html.escape(value), description=html.escape(description)
        )
        for label, value, description in metrics
    )
    row_html = []
    for item in rows:
        if item["status"] == "empty":
            continue
        error_rate = item["word_error_rate"]
        error_text = "n/a" if error_rate is None else f"{error_rate:.1%}"
        start = item["start"]
        row_html.append(
            "<tr class='{status}' data-start='{start}' data-end='{end}'>"
            "<td>{range}</td><td>{status}</td><td>{wer}</td><td>{operations}</td>"
            "<td>{reference}</td><td>{candidate}</td>"
            "<td><button type='button' data-seek='{start}'>Play</button></td></tr>".format(
                status=html.escape(item["status"]),
                start=start,
                end=item["end"],
                range=html.escape(f"{item['start_label']} - {item['end_label']}"),
                wer=error_text,
                operations=html.escape(f"S {item['substitutions']} / D {item['deletions']} / I {item['insertions']}"),
                reference=html.escape(item["reference_raw"]),
                candidate=html.escape(item["candidate_raw"]),
            )
        )
    media = report.get("media_relative_path")
    media_html = (
        f"<aside class='player-dock' aria-label='Floating media player'><span>Local recording</span><video id='media' controls preload='metadata' src='{html.escape(media)}'></video></aside>"
        if media
        else "<p class='notice'>No media file was supplied. Re-run with <code>--media</code> to enable playback.</p>"
    )
    source = report["source"]
    return f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Transcript validation report</title>
<style>
:root {{ color-scheme: light; --ink:#19232d; --paper:#f7f5ef; --accent:#01696f; --warn:#ad5f00; --bad:#a32d2d; --line:#c8c5bb; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px Georgia, serif; }}
main {{ max-width:1500px; margin:auto; padding:32px 24px 56px; }} h1,h2 {{ font-family:"Trebuchet MS",sans-serif; margin:0 0 8px; }} .lede {{ max-width:980px; line-height:1.45; }}
.metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin:24px 0; }} .metric {{ background:#fff; border:1px solid var(--line); padding:14px; border-radius:6px; }} .metric span {{ display:block; font:13px "Trebuchet MS",sans-serif; }} .metric strong {{ display:block; font:28px "Trebuchet MS",sans-serif; margin-top:4px; }} .metric p {{ font:14px/1.35 "Trebuchet MS",sans-serif; margin:10px 0 0; color:#3d4b55; }}
 .method {{ max-width:980px; background:#e6ece9; border-left:4px solid var(--accent); padding:16px 18px; margin:0 0 28px; }} .method h2 {{ font-size:18px; }} .method p {{ margin:8px 0 0; line-height:1.45; }}
.player-dock {{ position:fixed; right:20px; bottom:20px; width:min(360px,calc(100vw - 40px)); z-index:10; padding:10px; border:1px solid var(--line); border-radius:6px; background:#fff; box-shadow:0 8px 24px #19232d3d; }} .player-dock span {{ display:block; margin-bottom:5px; font:13px "Trebuchet MS",sans-serif; }} video {{ width:100%; display:block; background:#000; }} .toolbar {{ display:flex; gap:12px; flex-wrap:wrap; margin:22px 0 10px; font-family:"Trebuchet MS",sans-serif; }} input {{ padding:8px; min-width:260px; }} label {{ padding:7px 0; }}
.table-wrap {{ overflow:auto; border:1px solid var(--line); background:#fff; }} table {{ border-collapse:collapse; width:100%; min-width:1000px; }} th,td {{ text-align:left; vertical-align:top; padding:10px; border-bottom:1px solid var(--line); }} th {{ position:sticky; top:0; background:#e6ece9; font:13px "Trebuchet MS",sans-serif; }} tr.match {{ opacity:.58; }} tr.unmatched {{ background:#fff0ed; }} tr.difference {{ background:#fffaf0; }} tr.active-window {{ outline:3px solid var(--accent); outline-offset:-3px; }} button {{ background:var(--accent); color:#fff; border:0; padding:7px 10px; border-radius:4px; cursor:pointer; }} .notice {{ padding:12px; border-left:4px solid var(--warn); background:#fff5d9; }} footer {{ margin-top:20px; font:13px "Trebuchet MS",sans-serif; color:#52606d; }}
@media (max-width:640px) {{ .player-dock {{ left:10px; right:10px; bottom:10px; width:auto; }} }}
</style>
</head>
<body><main>
<h1>Transcript agreement report</h1>
<p class='lede'>Comparison of independently generated Teams and WhisperX transcripts. Scores measure agreement, not absolute recognition accuracy. Speaker labels and cue boundaries are intentionally ignored.</p>
<div class='metrics'>{metric_html}</div>
<section class='method'><h2>Hvad måles, og hvorfor?</h2><p>Rapporten opdeler mødet i tidsvinduer og sammenligner normaliserede ord, når Teams- og WhisperX-teksten overlapper i tid. Speaker-tags, tegnsætning og forskellige cue-grænser tæller ikke som afvigelser. Formålet er at finde passager, hvor de to uafhængige transskriptioner er uenige, så de kan verificeres mod optagelsen. Teams-VTT er evidens, ikke facit, så tallene måler transskriptionsenighed og ikke den faktiske tale med absolut sikkerhed.</p></section>
{media_html}
<div class='toolbar'><input id='filter' type='search' placeholder='Filter text or status'><label><input id='hide-matches' type='checkbox'> Hide exact matches</label></div>
<div class='table-wrap'><table><thead><tr><th>Time</th><th>Status</th><th>WER</th><th>Edits</th><th>Teams reference</th><th>WhisperX candidate</th><th>Audio</th></tr></thead><tbody>{''.join(row_html)}</tbody></table></div>
<footer>Reference: {html.escape(source['reference_vtt'])}<br>Candidate: {html.escape(source['candidate_vtt'])}<br>Generated: {html.escape(report['generated_at'])}</footer>
</main><script>
const filter=document.querySelector('#filter'), hideMatches=document.querySelector('#hide-matches'), rows=[...document.querySelectorAll('tbody tr')];
function filterRows() {{ const needle=filter.value.toLowerCase(); rows.forEach(row=>{{ const visible=(!hideMatches.checked||!row.classList.contains('match')) && row.textContent.toLowerCase().includes(needle); row.hidden=!visible; }}); }}
filter.addEventListener('input',filterRows); hideMatches.addEventListener('change',filterRows);
const media=document.querySelector('#media');
function setActiveWindow() {{ if(!media) return; const current=media.currentTime; rows.forEach(row=>row.classList.toggle('active-window', current >= Number(row.dataset.start) && current < Number(row.dataset.end))); }}
if(media) {{ media.addEventListener('timeupdate',setActiveWindow); media.addEventListener('seeked',setActiveWindow); }}
document.querySelectorAll('[data-seek]').forEach(button=>button.addEventListener('click',()=>{{ if(!media) return; media.currentTime=Number(button.dataset.seek); media.play().catch(()=>{{}}); setActiveWindow(); }}));
</script></body></html>"""


def relative_media_path(media: Path | None, output: Path) -> str | None:
    if media is None:
        return None
    return Path(__import__("os").path.relpath(media.resolve(), output.parent.resolve())).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path, help="Teams or other reference WebVTT")
    parser.add_argument("--candidate", required=True, type=Path, help="WhisperX diarized WebVTT")
    parser.add_argument("--media", type=Path, help="Optional local MP4 or WAV used by the report")
    parser.add_argument("--output-dir", type=Path, default=Path("validation-reports"))
    parser.add_argument("--name", help="Report file stem; default derives from candidate filename")
    parser.add_argument("--window-seconds", type=float, default=DEFAULT_WINDOW_SECONDS)
    arguments = parser.parse_args()
    if arguments.window_seconds <= 0:
        parser.error("--window-seconds must be positive")
    for path in (arguments.reference, arguments.candidate):
        if not path.is_file():
            parser.error(f"File not found: {path}")
    if arguments.media and not arguments.media.is_file():
        parser.error(f"Media file not found: {arguments.media}")

    reference = parse_vtt(arguments.reference)
    candidate = parse_vtt(arguments.candidate)
    if not reference or not candidate:
        parser.error("Both VTT files must contain at least one spoken cue")
    windows = build_windows(reference, candidate, arguments.window_seconds)
    window_data = []
    for window in windows:
        item = asdict(window)
        item["start_label"] = format_timestamp(window.start)
        item["end_label"] = format_timestamp(window.end)
        item["word_error_rate"] = window.wer
        window_data.append(item)
    output_dir = arguments.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    name = arguments.name or arguments.candidate.stem
    report_path = output_dir / f"{name}.html"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"reference_vtt": str(arguments.reference), "candidate_vtt": str(arguments.candidate)},
        "media_relative_path": relative_media_path(arguments.media, report_path) if arguments.media else None,
        "normalization": "NFKC, casefold, markup/speaker removal, punctuation-insensitive tokenization",
        "summary": summarize(reference, candidate, windows),
        "windows": window_data,
    }
    json_path = output_dir / f"{name}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(html_report(report), encoding="utf-8")
    summary = report["summary"]
    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"F1 agreement: {summary['f1']:.1%}; WER: {summary['word_error_rate']:.1%}; coverage: {summary['reference_temporal_coverage']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
