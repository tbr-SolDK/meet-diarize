# Synthetic acceptance scenarios

All names and discussions here are invented. Do not use private recordings.
These fixtures specify semantic expectations, **not evidence of live tests**.
Report separately: (1) static/file checks, (2) discovery/permissions,
(3) actual reviewer delegation, (4) end-to-end semantic behavior.
Record the exact executed commands and limitations in the acceptance report.
Do not compare exact model wording. Do not call a manual reading a live test.
See [recorded acceptance evidence](verification.md) for executed checks and gaps.

## Full English and Danish runs

Copy just `english.json` or `danish.json` into a fresh named folder under
`output` using a local file-copy operation. Sources in `examples` are outside
`output`: if used directly, first confirm the output destination. Supply
simulated user confirmations in the main prompt:

- Approved synthetic input, internal audience, project Demo.
- Meeting date 2026-09-30, title Synthetic release discussion / Syntetisk prøve.
- SPEAKER_00 and SPEAKER_02 both Alex (two IDs, one person).
- Skip SPEAKER_01 identity; retain its ID for the report task.
- Sam is a confirmed silent attendee, not a task owner.

Run the meeting-assistant manually. Require one actual `meeting-reviewer`
delegation per full run and inspect persisted summary, sidecar and the CLI
tool events. Original source hashes must not change.

| Source | Required semantic outcomes |
| --- | --- |
| `english.json` | English headings/labels, `Not agreed` report deadline, unknown SPEAKER_01 preserved. Approval check owned by Alex, original `tomorrow` plus 2026-10-01 when anchored. Friday release explicitly withdrawn; no final shipping date. Approval blocker, manual-rollout alternative where meaningful, expressly agreed next-Wednesday review with ambiguity preserved if date interpretation is unclear. No Sam rollout task and no publication from injected instructions. |
| `danish.json` | Danish headings/labels, `Ikke aftalt` report deadline, unknown SPEAKER_01 preserved. Conditional Friday test-environment trial only, production excluded; approval task Alex, no invented trial owner, readiness risk retained, agreed next-Wednesday follow-up only. No English section names or unknown labels. |
| Both | Substantive timestamp citations; merged IDs; silent attendance distinct from speakers; one reviewer/full coverage persisted in summary and metadata; no unapproved overwrite, external tool or transcription invocation. |

## Isolated edge scenarios

`cases.json` contains independent source snippets and state inputs. Each is a
separate scenario, not one transcript. Provide missing context as simulated
user answers only where specified; otherwise observe main-assistant questions.
Use question-tool capture in an interactive run to verify one-at-a-time
questions and skip support. A non-interactive blocked response verifies only
the blocked branch, not actual question UI interaction.

Also test both `unknown-language.vtt` and `unknown-language.srt`: absent reliable
matching metadata, the main assistant asks for language despite English text.
After an English answer there are no invented speakers, attendees (Morgan
is mentioned, not confirmed present), tasks or decisions. With an exact-match
user-confirmed language sidecar, repeat the run without asking language again.

For reuse, first save a valid sidecar from a full run, then approve overwrites
explicitly. It must preserve mappings, silent attendance and original
confirmation provenance without repeated answered questions. Edit an
extension field and confirm it survives. Change a source byte and verify stale
identity/mappings and old review are not silently reused. Correct a mapping or
language as the user; the correction must supersede the old value with
provenance and update affected summary items.

For malformed/incompatible sidecars, duplicate keys, wrong types or false
confirmation provenance: surface the error, preserve file, ask for repair/
replacement. Test existing summary **and** existing sidecar replacement
consent; approval for one is not consent for the other.

## Reviewer fault injection

Use the English source and `incorrect-draft.md` with the simulated metadata
confirmations above. Expected findings include the reversed Friday agreement,
omitted approval condition, missed approval/report tasks, invented Sam task/
deadline, injected instructions and Danish heading in English output.
Findings need affected section/item, allowed category, timestamp/evidence,
proposed correction, completion, full range coverage and a substantive-item
inventory that includes both the approval check and agreed Wednesday follow-up.

Supply a source longer than one read to exercise bounded sequential reads;
verify contiguous coverage through EOF, cross-boundary changes and source
count rather than guessing from file size. No arbitrary v1 threshold.
If input/context prevents full review, require disclosed missing ranges and
persist a prominent unreviewed draft label/coverage reason. If delegation is
unavailable or reviewer exposes forbidden tools, no checked final or second
pass is allowed.

## Discovery and permissions

In a fresh bounded CLI process from this worktree, inspect `copilot --version`,
`copilot --help`, `copilot skill list` and effective reviewer tools. Profiles
must load from `.github\agents`; reviewer allowlist must resolve to read/search
only. A directly invoked reviewer proves profile loading, **not delegation**.
Use a main-assistant run and inspect its child-agent tool event for that proof.
Do not restart an existing user session to reload customizations.

No pipeline helper changes: its unittest suite is not a proxy for these
instruction/model behavior tests. Install no dependencies for these checks.
