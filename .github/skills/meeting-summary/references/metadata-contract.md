# Recording metadata contract v1

The UTF-8 JSON sidecar `<stem>.meeting.json` is reusable **only for one
recording/source identity**. It is not a transcript, a global people directory,
an instruction file, or a place to store chain-of-thought. Machine keys/enums
remain English; human-readable values use resolved output language except
proper names and preserved source evidence.

## Required shape and validation

Validate before reuse and before saving. Reject invalid JSON, duplicate keys,
wrong field types, missing required fields, unsupported version, invalid
enums/language tags, impossible dates, inconsistent identity/mapping references
and missing provenance explicitly. Do not coerce strings into booleans or
silently fall back. Explain the problem and ask the user to repair or authorize
replacement; retain the original until authorized. Never mark failed validation
as successful reuse. Preserve unknown extension fields and user-edited values;
surface contradictions rather than overwriting confirmations.
User provenance must confirm the specific field, not a related fact: an
identity mapping is not attendance confirmation, and "follow the source
language" is policy, not a user-selected language override.

| Field | Required type / meaning |
| --- | --- |
| `schema_version` | Integer, exactly `1`. Other versions require explicit migration, not guessing. |
| `source` | Object with `path` (workspace-relative string where possible), `format` (`whisperx-json`, `vtt`, `srt`), `sha256` (64 lowercase hex characters for exact file bytes), `size_bytes` (nonnegative integer), `recording_key` (nonempty recording-specific string). |
| `meeting` | Object with fact objects `title`, `date`, `timezone`, `project`, `purpose`. Unknown values are `null`, never inferred defaults. Date value, if present, is ISO `YYYY-MM-DD`; timezone is separately evidenced, not implied. |
| `speaker_mappings` | Array of mapping objects defined below; empty allowed. |
| `attendance` | Optional array of confirmed attendee objects, including silent attendees; absence means no confirmed list, not nobody attended. |
| `audience` | Exactly `"internal"`. No external delivery implied. |
| `language` | Object with `source`, `resolved`, `choice`, `conflicts`, defined below. |
| `uncertainties` | Array of `{field, issue, question_status}`; strings, status `unasked`, `skipped`, `answered` or `unresolved`. |
| `review` | Object with `status`, `passes`, `coverage`, `reconciliation`, `post_review_changes`, defined below. |

A **fact object** is `{value, provenance, confirmed}`. `confirmed` is Boolean,
true only for an explicit user confirmation. `value` is a string or null.
`provenance` is an array (empty only for unknown null facts) with entries:
`{kind, reference, evidence}`. `kind` is `user`, `transcript`, `filename`, or
`metadata`; `reference` is a question/answer identifier, timestamp/segment,
basename or prior sidecar field; `evidence` is a concise factual note, not a
private reasoning trace. A `metadata` entry must retain original provenance,
not manufacture confirmation. Filename guesses always have `confirmed:false`;
confirmations append user provenance without removing their origin.
Reliable date anchoring requires explicit user confirmation or unambiguous
dated meeting evidence from the transcript, not just a filename candidate.

## Matching and stale sources

Compute SHA-256 and size from the selected transcript, not from media. Main
assistant may use a narrowly scoped local file hashing command if its tools
permit; never read credentials or recordings. Do not fabricate a digest from
text rendered by a tool. If exact byte hashing is unavailable, do not create
a reusable v1 sidecar: disclose the blocker and retain a marked draft only.
`recording_key` can be the original relative recording stem confirmed for this
source; do not reuse a company/project name as a recording key.

Reuse requires matching digest, size, format and recording identity. A move
with unchanged bytes still requires confirmation of identity before updating
the path. Same stem alone is not matching evidence. A changed digest/size,
different recording key, or alternate transcript format makes metadata stale.
Show the mismatch and ask whether it is a revision of the same recording.
If confirmed, revalidate each affected mapping/fact/language with source and
user; never automatically transfer previous speaker IDs. Preserve prior
source identity in optional `source_history`, mark invalidated confirmations
as unconfirmed until reconfirmed, and invalidate the old review. If identity is
not confirmed (including skip), do not apply old mappings. Do not destroy the
old sidecar without overwrite permission.

For a VTT/SRT to use JSON language evidence, an exact matching v1 sidecar must
identify this VTT/SRT source, and optional `language.source.companion` must hold
the companion's path, SHA-256, size and user-confirmed same-recording
association. Verify both files and language consistency. A neighboring JSON
basename or sidecar from another source alone is not reliable matching evidence.
A previous user-confirmed language on an exact matching source is reusable.

## Speaker mappings and attendance

Mapping shape:
`{speaker_ids, status, person, provenance, confirmed}`.

- `speaker_ids`: nonempty array of unique source IDs. An ID occurs in only one
  mapping; merge IDs in one mapping when they refer to the same person.
- `status`: `identified`, `unknown`, `uncertain`, or `mixed`.
- `person`: for `identified`, object with nonempty `name` and optional fact
  objects `role`, `organization`; otherwise null. Do not put a single confident
  person on a mixed ID; optional `candidates` may hold unconfirmed candidate
  names with provenance or timestamp-specific user confirmations.
- `provenance`: fact-style entries. `confirmed:true` requires user evidence;
  `identified` requires a user-confirmed name. Scores never confirm identities.
  Unknown/uncertain/mixed identity is not confirmed; user-confirmed mixedness
  can be noted in provenance without confirming a single identity.

Attendance entries: `{name, speaking, speaker_ids, role, organization,
provenance, confirmed}`. `speaking` is `true`, `false` or `null` (unknown);
`speaker_ids` is an array, empty for silent attendees; role/organization are
fact objects. All attendance entries require `confirmed:true` and user
provenance. A speaker mapping does not independently confirm attendance.
Named people discussed in the transcript are not necessarily present.
VTT/SRT without reliable IDs normally have no mappings; say attribution is
unknown instead of creating fictitious `SPEAKER_00` labels.

## Languages

- `source`: `{value, provenance, reliability}`; value is a valid language tag
  such as `da`, `en` or null; reliability is `reliable`, `missing`, `invalid`,
  `conflicting`, or `mixed`. Retain malformed raw input separately as optional
  `raw_value`, not as a valid language code. Provenance records the JSON root
  field, matching sidecar/companion or observed conflict, not autodetection.
  Codes must denote a recognized language; placeholders `auto`, `unknown`,
  `mixed` and arbitrary strings are invalid, even if syntactically tag-like.
- `resolved`: valid language tag or null. No default; null prevents drafting.
- `choice`: `{kind, provenance}` where kind is `json`, `user`, or `unresolved`.
  `json` requires reliable matching source evidence; `user` requires explicit
  current or retained user confirmation. This also applies to VTT/SRT.
- `conflicts`: array of concise evidence notes (empty when none).

Missing/invalid/conflicting/mixed evidence requires the main assistant to ask.
A user answer overrides conflicting evidence but does not erase it. A skipped
answer leaves `resolved:null`, `choice.kind:"unresolved"`. Do not make a
sidecar's `resolved` value authoritative if matching or provenance fails.

## Review state

`status`: `pending`, `reviewed`, `unreviewed-draft`, or `blocked`.
`passes`: integer `0` or `1`, number of reviewer invocations (including a failed
attempt). Never greater than one for this run.
`coverage`: `{source_complete, reviewer_complete, missing_ranges}` with
Booleans and an array of source ranges. `reviewed` requires both true, one
pass, and all findings/inventory items reconciled. `reconciliation`: array of concise
`{finding_id, outcome, evidence}` with outcome `corrected`, `rejected`, or
`uncertainty-retained`. `post_review_changes`: array of concise fact changes
and affected sections; empty when none. Preserve earlier run history in
optional `review_history` instead of claiming two passes in the current run.
Do not store reviewer chain-of-thought or unnecessary quotations.

## Synthetic valid example

This example uses the exact bytes of `examples\english.json`; its hash/size
must be recomputed if that fixture changes. Example names are fictional,
and confirmations below are simulated user answers, not inferred identities.

```json
{
  "schema_version": 1,
  "source": {
    "path": ".github\\skills\\meeting-summary\\examples\\english.json",
    "format": "whisperx-json",
    "sha256": "9741ef296d624db1cf4bf8afacd4b5c0fdf0b18309b095200de2cfdf2358f9ff",
    "size_bytes": 1319,
    "recording_key": "synthetic-english"
  },
  "meeting": {
    "title": {"value": "Synthetic release discussion", "provenance": [{"kind": "user", "reference": "test-setup", "evidence": "User supplied title"}], "confirmed": true},
    "date": {"value": "2026-09-30", "provenance": [{"kind": "user", "reference": "test-setup", "evidence": "User confirmed meeting date"}], "confirmed": true},
    "timezone": {"value": null, "provenance": [], "confirmed": false},
    "project": {"value": "Demo", "provenance": [{"kind": "user", "reference": "test-setup", "evidence": "Synthetic project"}], "confirmed": true},
    "purpose": {"value": "Discuss release readiness", "provenance": [{"kind": "transcript", "reference": "[00:00:00]", "evidence": "Release discussion"}], "confirmed": false}
  },
  "speaker_mappings": [
    {"speaker_ids": ["SPEAKER_00", "SPEAKER_02"], "status": "identified", "person": {"name": "Alex"}, "provenance": [{"kind": "user", "reference": "test-setup", "evidence": "User mapped both IDs to Alex"}], "confirmed": true},
    {"speaker_ids": ["SPEAKER_01"], "status": "unknown", "person": null, "provenance": [], "confirmed": false}
  ],
  "attendance": [
    {"name": "Sam", "speaking": false, "speaker_ids": [], "role": {"value": null, "provenance": [], "confirmed": false}, "organization": {"value": null, "provenance": [], "confirmed": false}, "provenance": [{"kind": "user", "reference": "test-setup", "evidence": "User confirmed silent attendee"}], "confirmed": true}
  ],
  "audience": "internal",
  "language": {
    "source": {"value": "en", "provenance": [{"kind": "transcript", "reference": "language", "evidence": "WhisperX root language, consistent with source"}], "reliability": "reliable"},
    "resolved": "en",
    "choice": {"kind": "json", "provenance": [{"kind": "transcript", "reference": "language", "evidence": "Reliable JSON language"}]},
    "conflicts": []
  },
  "uncertainties": [{"field": "speaker_mappings.SPEAKER_01", "issue": "Identity unknown", "question_status": "skipped"}],
  "review": {
    "status": "pending",
    "passes": 0,
    "coverage": {"source_complete": true, "reviewer_complete": false, "missing_ranges": []},
    "reconciliation": [],
    "post_review_changes": []
  }
}
```
