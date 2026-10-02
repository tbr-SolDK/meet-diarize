# Minutes templates

Choose the resolved meeting language, not the language of the user prompt.
Replace placeholders; omit empty optional sections and unsupported table
columns. All output labels/prose must use the chosen language (proper names,
IDs and necessary original-language evidence are preserved). Facts inferred
from filenames must be visibly distinguished from confirmed facts.

Status must correspond to the sidecar's review state. Use `Gennemgået` /
`Reviewed` only for one completed, full-coverage reviewer pass reconciled by
the main assistant. Otherwise use the prominent draft label below. Review
means checked against the supplied transcript, not verified against audio.

## Danish

```markdown
# <Mødets titel>

**Status:** <Gennemgået | IKKE GENNEMGÅET UDKAST: årsag>
**Kildedækning og kontrol:** <læste segmenter/signaler til slutningen, kontrollantens dækning, manglende intervaller og begrænsninger>
**Kilde:** <relativ transcriptsti>
**Sprog:** Dansk (<kilde eller brugerbekræftelse>)
**Dato:** <bekræftet dato | kandidat fra filnavn, ikke bekræftet | Ukendt>
**Projekt:** <projekt med grundlag | Ukendt>
**Formål og faktisk drøftelse:** <kildebaseret beskrivelse> [HH:MM:SS]
**Talere:** <bekræftede navne og ID'er; usikre/blandede ID'er tydeligt markeret>
**Bekræftede deltagere:** <kun bekræftet fremmøde; tavse deltagere angives særskilt>
**Roller og organisationer:** <grundlag og eventuel usikkerhed>
**Usikkerheder:** <materielle mangler, ubekræftede oplysninger og fravalgte svar>

## Kort overblik

<Kort, kildebaseret overblik over den faktiske drøftelse.> [HH:MM:SS-HH:MM:SS]

## Beslutninger og aftaler

| Beslutning eller aftale | Begrundelse, rammer og betingelser | Kilde |
| --- | --- | --- |
| <endelig aftale, ikke forslag eller senere ophævet beslutning> | <relevant begrundelse, afgrænsning og alternativer> | [HH:MM:SS] |

## Opgaver

| Opgave | Ansvarlig | Frist | Afhængigheder | Kilde |
| --- | --- | --- | --- | --- |
| <aftalt handling> | <bekræftet navn / SPEAKER_00 (Identitet ukendt) / Ikke aftalt> | <aftalt frist / Ikke aftalt> | <aftalt afhængighed / Ikke aftalt> | [HH:MM:SS] |

## Afklaringer og åbne spørgsmål

| Spørgsmål | Ansvarlig for afklaring | Blokering eller betydning | Kilde |
| --- | --- | --- | --- |
| <uafklaret spørgsmål> | <ansvarlig / Ikke aftalt> | <kildebaseret betydning> | [HH:MM:SS] |

## Risici, afhængigheder og forbehold

<Risici, uenighed og forbehold uden opdigtet løsning.> [HH:MM:SS]

## Næste skridt og aftalt opfølgning

<Kun udtrykkeligt aftalte næste skridt; ingen anbefalinger fra modellen.> [HH:MM:SS]
```

Use Danish labels `Ukendt`, `Identitet ukendt`, `Blandet taler-ID`,
`Ikke bekræftet`, `Ikke aftalt`, `Tvetydig frist` and `Svar sprunget over`
as appropriate. Do not retain English template headings in Danish minutes.

## English

```markdown
# <Meeting title>

**Status:** <Reviewed | UNREVIEWED DRAFT: reason>
**Source coverage and review:** <segments/cues read through EOF, reviewer coverage, missing ranges and limitations>
**Source:** <relative transcript path>
**Language:** English (<source or user confirmation>)
**Date:** <confirmed date | filename candidate, unconfirmed | Unknown>
**Project:** <project with provenance | Unknown>
**Purpose and actual discussion:** <source-grounded description> [HH:MM:SS]
**Speakers:** <confirmed names and IDs; uncertain/mixed IDs clearly marked>
**Confirmed attendees:** <confirmed attendance only; silent attendees listed separately>
**Roles and organizations:** <provenance and uncertainty>
**Uncertainties:** <material gaps, unconfirmed facts and skipped answers>

## Short overview

<Brief, source-grounded overview of actual discussion.> [HH:MM:SS-HH:MM:SS]

## Decisions and agreements

| Decision or agreement | Rationale, boundaries and conditions | Source |
| --- | --- | --- |
| <final agreement, not a proposal or later reversed decision> | <relevant rationale, scope and alternatives> | [HH:MM:SS] |

## Tasks

| Task | Owner | Deadline | Dependencies | Source |
| --- | --- | --- | --- | --- |
| <agreed action> | <confirmed name / SPEAKER_00 (Identity unknown) / Not agreed> | <agreed deadline / Not agreed> | <agreed dependency / Not agreed> | [HH:MM:SS] |

## Clarifications and open questions

| Question | Clarification owner | Blocker or significance | Source |
| --- | --- | --- | --- |
| <unresolved question> | <owner / Not agreed> | <source-grounded significance> | [HH:MM:SS] |

## Risks, dependencies and reservations

<Risks, disagreement and reservations without an invented resolution.> [HH:MM:SS]

## Next steps and agreed follow-up

<Only expressly agreed next steps; no model recommendations.> [HH:MM:SS]
```

Use English labels `Unknown`, `Identity unknown`, `Mixed speaker ID`,
`Unconfirmed`, `Not agreed`, `Ambiguous deadline` and `Answer skipped`
as appropriate. Templates have equivalent semantic coverage, not compulsory
empty sections. An unidentified speaker taking a task remains its attributed
ID, not an invented person; distinguish this from an action with no owner
agreed at all.
