# Acceptance evidence: 2026-10-02

Environment: isolated Windows worktree, Copilot CLI **1.0.90-5**. No model
override was used; live subprocesses inherited the locally configured model
(event records show `gpt-5.3-codex`). Only synthetic text was processed. No
recordings, credentials, transcription helpers, new dependencies or external
content tools were used. No existing user session was restarted.

## Four distinct evidence levels

| Level | Executed evidence | Outcome and limits |
| --- | --- | --- |
| 1. File/static contracts | Python standard-library checks of frontmatter's supported scalar/list shapes, local Markdown references, synthetic JSON and fenced JSON contracts; fixture hash/size; `git diff --check`; pipeline/ignore diff and source-byte comparisons | Passed. No YAML library was installed; frontmatter was checked as the restricted shape used here, and actual CLI loading provided parser evidence. These are not behavioral tests. |
| 2. Copilot discovery and permissions | `copilot skill list`; fresh `--agent meeting-assistant` and `--agent meeting-reviewer` configuration probes; actual reviewer `glob`, `rg`, `view` calls | Skill and both profiles loaded. Alias-only `search` did not expose concrete `rg`/`glob` in the initial probe; profiles now include those names. Intrinsic `skill`/`sql` remained despite profile allowlist; `--excluded-tools skill,sql` removed them. Final reviewer callable surface: `view`, `rg`, `glob`, parallel wrapper only; no shell, edit, delegation, questions or external tools. |
| 3. Actual delegated reviewer | Native JSONL `subagent.started`, `subagent.selected`, `subagent.completed` plus child read-tool events, not just model assertions | Seven independent test runs each invoked exactly one actual `meeting-reviewer` child; model selection inherited the session. Two deliberately unavailable/unresolved runs invoked zero. A direct `--agent meeting-reviewer` probe was not counted as delegation. |
| 4. End-to-end semantic behavior | Saved summaries/sidecars from English, Danish, metadata-reuse/correction, unavailable-review VTT and long-source runs; native source-read events; skipped-language SRT stop | Core English/Danish runs and reuse passed checked invariants. Unavailable review remained visibly draft in both artifacts; skipped language produced neither artifact. Long-source failures and corrections are detailed below; this is not a blanket guarantee that all model output is correct. |

Local ignored evidence is under `output\meeting-summary-validation\`, with
configuration probes at `output\meeting-summary-*-profile*.jsonl` and
`output\meeting-summary-profile-check.jsonl`. Evidence and generated meeting
artifacts are not committed. The prompts are recorded as `user.message`
`data.content` in each native JSONL event file; these are the exact `$prompt`
values supplied to the commands below.

## Executed commands

These invocation forms were executed from the worktree, with no model flag.
`$prompt` was the complete corresponding synthetic test prompt described above
and retained in that run's JSONL. The shared argument array below expands to
the exact flags supplied in each fresh process:

```powershell
copilot --version
copilot --help
copilot skill --help
copilot help permissions
copilot skill list

$localFlags = @(
  '--allow-all-tools', '--disable-builtin-mcps',
  '--disable-mcp-server', 'Atlassian Rovo MCP Server',
  '--disable-mcp-server', 'aspire',
  '--disable-mcp-server', 'microsoft-docs-mcp',
  '--disable-mcp-server', 'azure',
  '--output-format', 'json', '--no-color', '--stream', 'off',
  '--log-level', 'none'
)

# Final configuration-only reviewer probe.
copilot --agent meeting-reviewer --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-final-profile.jsonl

# Initial English and Danish full runs.
copilot --agent meeting-assistant --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\en\events.jsonl
copilot --agent meeting-assistant --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\da\events.jsonl

# New independent English rerun: exact-match metadata reuse, Robin correction,
# user extension preservation, explicit consent to replace both artifacts.
copilot --agent meeting-assistant --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\en\reuse-events.jsonl

# Independent faulty-draft reviews, before and after inventory improvement.
copilot --agent meeting-assistant --available-tools view,rg,glob,task,read_agent --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\fault-review.jsonl
copilot --agent meeting-assistant --available-tools view,rg,glob,task,read_agent --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\fault-inventory.jsonl

# Actual VTT workflow with delegation unavailable and explicit English answer.
copilot --agent meeting-assistant --available-tools view,rg,glob,powershell,apply_patch --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\unavailable\events.jsonl

# Read-only model branch evaluation, NOT full meeting runs.
copilot --agent meeting-assistant --available-tools view,rg,glob --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\branches.jsonl

# Actual SRT selected-source run, explicit user skip of unresolved language.
copilot --agent meeting-assistant --available-tools view,rg,glob --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\unresolved\events.jsonl

# Independent long-source runs, each with one reviewer, not repeat passes.
copilot --agent meeting-assistant --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\long\events.jsonl
copilot --agent meeting-assistant --excluded-tools skill,sql -p $prompt @localFlags > output\meeting-summary-validation\long-visible\events.jsonl

git --no-pager diff --check
git --no-pager diff --exit-code -- pipeline .gitignore
git check-ignore output\meeting-summary-validation\en\english.summary.md output\meeting-summary-validation\en\english.meeting.json
```

Standard-library Python commands also parsed event records, counted actual
delegations, checked saved language/review fields, citation shape, unknown/
merged IDs, silent Sam, exact extension preservation, Robin correction, source
hash/size and byte equality. They asserted that skipped-language artifacts
were absent and unavailable-review status/reason remained in saved artifacts.
These assertions checked required shape/invariants rather than exact wording.
The existing pipeline unittest suite was not run: no executable helper changed.

## Observed semantics and corrective iterations

English minutes retained the approval blocker, withdrawn Friday release,
report task with unknown `SPEAKER_01` and `Not agreed` deadline, next-Wednesday
follow-up and no injected Sam rollout/publication. The reviewer caught the
author's initial `Not agreed` owner for an explicit unknown-speaker commitment;
the main assistant corrected it before saving. The template was clarified so
unidentified ownership is distinct from absent ownership.

Danish minutes used Danish headings/labels despite the English test prompt,
kept the test-environment/approval conditions and production exclusion,
unknown report owner, `Ikke aftalt` deadline, readiness risk and agreed follow-up.
Both initial sources remained byte-identical to their fixtures.

The English reuse run applied the explicit Robin correction to both merged
IDs, retained prior provenance/confirmation, preserved `user_notes` exactly,
kept silent Sam, archived earlier review state and used one new reviewer for
the new run. Replacement consent was supplied in the test prompt; this does
not demonstrate the interactive overwrite question UI.

The initial deliberately incorrect draft reviewer detected ten issues, but
missed the omitted approval-check task and agreed follow-up. The contract was
tightened with a required substantive-item inventory. A fresh independent
one-pass fault test then returned both missing tasks, follow-up, conditions,
reversal, unsupported injected task and wrong-language heading, with complete
8-segment coverage and timestamp-grounded findings.

The first long-input run falsely claimed main-assistant full coverage after
script reads discarded content and only partial/head-tail text was exposed.
Native event inspection caught this. Its saved summary and sidecar were
corrected to **UNREVIEWED DRAFT**, `source_complete:false`, with the missing
main range/limitation persisted; an invented task prerequisite was removed.
The shared contract now explicitly rejects count/hash/discard-loop coverage.

A fresh long-input run exposed all **1194 lines / 198 segments / 51571 bytes**
to both main assistant and reviewer via twelve contiguous `view` ranges
through EOF. This was established from native tool events, **not**
assistant-written custom coverage events appended to the log. The later
withdrawal superseded the initial release intent and no invented approval-task
prerequisite remained. However, the output incorrectly promoted Alex's
confirmed identity mapping to confirmed attendance and recorded language
policy as a user choice. Validation removed those inferences and recorded the
post-review corrections in the saved sidecar. Full read coverage passed;
the raw run was **not a perfect semantic pass**. One reviewer is not a truth
guarantee.

## Remaining live-check gaps

The noninteractive CLI probes did not expose `ask_user`. Actual interactive
one-at-a-time Danish/English/freeform/skip questions, missing-fact and overwrite
dialogs were **not exercised**; the documented usage is interactive `-i`.
They must not be claimed verified from prose branch responses.

The 16-case read-only branch evaluation correctly described the required
missing/invalid/conflicting/mixed-language and VTT/SRT gates, skipped language,
mixed IDs, unanchored relative date, malformed/incompatible metadata, false
confirmation, stale source, user correction, declined overwrite and partial/
unavailable-review branches. This is live model-response evidence, **not**
persisted end-to-end execution of every case. Its Boolean answers for cases
without source context were sometimes inconsistent (`may_draft:true` beside
unknown language); do not treat those responses as a passing workflow test.

Actual malformed-sidecar repair, duplicate-key rejection, changed-source
revalidation, declined-overwrite file preservation, VTT/SRT matching-companion
reuse and naturally incomplete-review persistence were not fully exercised.
Their required behavior is specified in the shared contracts and fixtures;
static specifications do not prove it. Synthetic validation disclosed both
real model errors above rather than asserting universal correctness.
