# The run records

These are the records of two real runs of plumbline on `tasklist`, made on 2026-09-30. They were copied from the working repository's `.plumbline/` folder. That folder is ignored by git there, and it is still ignored here (see `.gitignore`), so a session you start in this repository writes its own records under `.plumbline/`, never over these.

| Folder | Original run id | Result |
| --- | --- | --- |
| `feature-due-dates/` | `ccffe51-20260930T055131Z` | branch `due-dates`, commit `109e295` |
| `fix-overdue-bad-date/` | `109e295-20260930T092436Z` | branch `overdue-bad-date`, commit `cf98e93` |
| `pass/` | | one pass record per commit, named by the commit's full hash. Each is a byte-for-byte copy of its run's `reduce.json`. |

## What is in a run folder

| File | What it is |
| --- | --- |
| `intake.json` | The change class: file types, size, row and intent, and the commit the run is measured from. |
| `plan.json` | The spec. In the fix run it was supplied, not planned. |
| `tests.json` | The test-writer's record. |
| `test-review.json`, `test-review/round-1/` | The review of the tests. Feature run only: the fix row has no test review. |
| `build.json` | The builder's note. |
| `verify.json` | The verifier's record. |
| `junit-tests.xml`, `junit-verify.xml` | What pytest reported when plumbline itself ran the test command, once for the tests gate and once for the verify gate. |
| `review.json` | The merged review: findings, defenses, survivors, routes, gaps. |
| `review/round-1/` | The files of each review agent, which `review.json` was merged from. |
| `reduce.json` | The pass record: stage results, rounds, tokens, verdict. |
| `ledger.jsonl` | The run's log, one JSON object per line. |

The README at the top of the repository says what each record holds.

## Paths inside the records

The records name each other by their original paths, `.plumbline/runs/<run id>/...` and `.plumbline/pass/<commit>.json`. That was their place in the working repository. Here they sit in the folders above. The names inside the files are unchanged, so that the hashes still match.

## What was left out

- `.plumbline/runs/ACTIVE`: a pointer to the run in progress, not a record.
- `.plumbline/supplied-spec.json`: the file the fix run's spec was supplied from. It is byte-for-byte the same as `fix-overdue-bad-date/plan.json`.
- The test-writer's `stubs/` folder: scaffolding, and none was left at the end of either run.

## What was scrubbed

Paths scrubbed for publication. Six files were edited: the two ledgers and the four junit files. The other 33 files are byte-for-byte what the runs wrote.

| What | Count | Became |
| --- | --- | --- |
| Agent transcript paths (`transcript` and `session_transcript`, in 30 agent lines of the ledgers). Each was an absolute path into the machine's Claude Code folder. | 60 | `"<transcript>"` |
| Session ids (`session_id` of those 30 lines) | 30 | `<session-1>`, `<session-2>`, `<session-3>`. The same placeholder means the same session. The feature run had two sessions, the fix run one. |
| junit `hostname` attributes | 4 | `&lt;host&gt;` |
| junit `timestamp` attributes | 4 | `&lt;timestamp&gt;` |
| pytest temporary folders in `fix-overdue-bad-date/junit-tests.xml`, whose name carried the user name | 2 | `/tmp/pytest-of-&lt;user&gt;/` |

The `&lt;` and `&gt;` are XML's way of writing `<` and `>` inside the junit files.

Agent ids (`agent_id`) are kept. They tell one agent of a run from another, and they name nothing on a machine. The time of each ledger line (`at`) is kept: it is in UTC.

## Do the hashes still match?

Yes. None of the six edited files is pinned by a hash. The ledgers pin the other files in two ways, and both check out:

- The `pass` line and the `merge` lines of each ledger hold 46 hashes of files in this folder (the pass record, the records it lists, and the parts of each review merge). All 46 match.
- The newest `record_sha256` for each of 29 records matches the file. Older lines for a record that was rewritten after a failed gate name an earlier version of the file, which is not kept.

To check one, compare `sha256sum runs/feature-due-dates/plan.json` with the entry for `.plumbline/runs/ccffe51-20260930T055131Z/plan.json` in the last line of `runs/feature-due-dates/ledger.jsonl`.

## What you cannot redo

`plumbline.py tokens` reads the agent transcripts that a ledger points to. Those transcripts are not published, so the command cannot be run again on these ledgers. The token counts in each `reduce.json` stay as they were counted.
