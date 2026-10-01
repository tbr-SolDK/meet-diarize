#!/usr/bin/env python3
"""Create a local, seekable transcript review page for a recording."""

from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path
from urllib.parse import quote

TIMING = re.compile(r"^(?:(\d{2}):)?(\d{2}):(\d{2})[.,](\d{3})\s+-->\s+\S+")
SPEAKER = re.compile(r"^\s*\[(SPEAKER_\d+)\]:\s*", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def read_cues(path: Path) -> list[tuple[float, str, str]]:
    cues = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for index, line in enumerate(lines):
        match = TIMING.match(line.strip())
        if not match:
            continue
        hours, minutes, seconds, milliseconds = (int(part or 0) for part in match.groups())
        start = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        text_lines = []
        for text_line in lines[index + 1:]:
            if not text_line.strip():
                break
            text_lines.append(text_line.strip())
        text = " ".join(text_lines)
        speaker = SPEAKER.match(text)
        label = speaker.group(1) if speaker else ""
        clean_text = " ".join(TAG.sub("", SPEAKER.sub("", text)).split())
        if clean_text:
            cues.append((start, label, clean_text))
    return cues


def write_review(transcript: Path, media: Path, report: Path) -> None:
    cues = read_cues(transcript)
    if not cues:
        raise ValueError(f"No spoken cues in {transcript}")
    media_url = quote(Path(os.path.relpath(media.resolve(), report.parent.resolve())).as_posix(), safe="/.")
    rows = "\n".join(
        f'<tr data-start="{start}" data-text="{html.escape(text.casefold(), quote=True)}">'
        f'<td><button type="button" class="seek" data-seek="{start}" aria-label="Play from {int(start // 3600):02}:{int(start // 60) % 60:02}:{int(start) % 60:02}">'
        f'{int(start // 3600):02}:{int(start // 60) % 60:02}:{int(start) % 60:02}</button></td>'
        f'<td class="speaker">{html.escape(label)}</td><td>{html.escape(text)}</td></tr>'
        for start, label, text in cues
    )
    title = html.escape(transcript.stem)
    page = f"""<!doctype html>
<html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Transcript review</title>
<style>
:root {{ color-scheme: light; --ink:#19232d; --paper:#f7f5ef; --accent:#01696f; --line:#c8c5bb; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px Georgia,serif; }}
main {{ max-width:1200px; margin:auto; padding:24px 20px 72px; }} h1 {{ font:600 24px/1.3 'Trebuchet MS',sans-serif; overflow-wrap:anywhere; }}
.player {{ position:sticky; top:0; z-index:2; padding:12px 0; background:var(--paper); border-bottom:1px solid var(--line); }}
video {{ display:block; width:100%; max-height:40vh; background:#111; }} input {{ width:100%; padding:10px; margin:16px 0; font:inherit; }}
table {{ width:100%; border-collapse:collapse; background:#fff; }} td {{ border-bottom:1px solid var(--line); padding:10px; vertical-align:top; line-height:1.5; }}
tr {{ cursor:pointer; }} tr:hover, tr.active {{ background:#e6ece9; }} .speaker {{ white-space:nowrap; font:13px 'Trebuchet MS',sans-serif; color:#52606d; }}
.seek {{ border:0; background:none; color:var(--accent); cursor:pointer; font:600 14px 'Trebuchet MS',sans-serif; padding:4px; }}
@media(max-width:600px) {{ main {{ padding:12px; }} h1 {{ font-size:18px; }} td {{ padding:8px 4px; }} .speaker {{ font-size:11px; }} }}
</style></head><body><main><h1>{title}</h1>
<div class="player"><video id="media" controls preload="metadata" src="{html.escape(media_url, quote=True)}"></video></div>
<input id="filter" type="search" placeholder="Søg i transskriptionen" aria-label="Søg i transskriptionen">
<table aria-label="Transskription"><tbody>{rows}</tbody></table>
</main><script>
const video=document.querySelector('#media'), rows=[...document.querySelectorAll('tbody tr')];
function seek(row) {{ video.currentTime=Number(row.dataset.start); video.play().catch(()=>{{}}); }}
rows.forEach(row=>row.addEventListener('click',()=>seek(row)));
document.querySelector('#filter').addEventListener('input',event=>{{
  const query=event.target.value.toLocaleLowerCase();
  rows.forEach(row=>{{ row.hidden=!row.dataset.text.includes(query); }});
}});
video.addEventListener('timeupdate',()=>{{
  const current=video.currentTime;
  rows.forEach((row,index)=>row.classList.toggle('active',current>=Number(row.dataset.start) && (index===rows.length-1 || current<Number(rows[index+1].dataset.start))));
}});
</script></body></html>"""
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(page, encoding="utf-8")
    print(f"Wrote {report}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    for path in (arguments.transcript, arguments.media):
        if not path.is_file():
            parser.error(f"File not found: {path}")
    write_review(arguments.transcript, arguments.media, arguments.output)


if __name__ == "__main__":
    main()