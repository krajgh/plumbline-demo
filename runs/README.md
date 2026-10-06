# The run records

These are the records of eight real runs of plumbline on `tasklist`, made between 2026-09-30 and 2026-10-06. They were copied from the working repository's `.plumbline/` folder. That folder is ignored by git there, and it is still ignored here (see `.gitignore`), so a session you start in this repository writes its own records under `.plumbline/`, never over these.

| Folder | Original run id | Result |
| --- | --- | --- |
| `feature-due-dates/` | `ccffe51-20260930T055131Z` | run 1: branch `due-dates`, commit `109e295` |
| `fix-overdue-bad-date/` | `109e295-20260930T092436Z` | run 2: branch `overdue-bad-date`, commit `cf98e93` |
| `fix-overdue-non-string/` | `cf98e93-20261005T103921Z` | run 3: branch `overdue-non-string`, commit `183da93` |
| `large-0-plan/` | `183da93-20261005T111104Z` | run 4a, the plan of a request of size L: no commit, because nothing is built at size L |
| `large-1-tags/` | `183da93-20261005T111543Z` | run 4b, part 1: branch `organize-tags`, commit `a061f09` |
| `large-2-priorities/` | `a061f09-20261005T135022Z` | run 4c, part 2: branch `organize-priorities`, commit `0f44eee` |
| `large-3-edit-remove/` | `0f44eee-20261005T151939Z` | run 4d, part 3: branch `organize-edit`, commit `917e870` |
| `feature-stats/` | `0f44eee-20261006T032301Z` | run 5: branch `stats`, commit `f288060` |
| `pass/` | | one pass record per commit, named by the commit's full hash. Each is a copy of its run's `reduce.json`, byte for byte. It also holds `c8436101a7f4583088f836f791c899e4ea9dc5da.override.json`, the override record for the merge commit `c843610`, which no run covers (branch `latest`). |

A run id is the commit the run was measured from, a dash, and the time the run began (UTC).

## What is in a run folder

| File | What it is |
| --- | --- |
| `intake.json` | The change class: file types, size, row and intent, and the commit the run is measured from. |
| `request.md` | The request the run began with, stored by plumbline. Runs 3 to 5 have one (from 0.5.0). For the three parts of run 4 it is the request the session wrote from the plan's split. |
| `plan.json` | The spec. In the fix runs it was supplied, not planned. In `large-0-plan/` it ends with the split proposal. |
| `spec-review.json`, `spec-review/round-1/` | The review of the spec against the request, for sizes M and L (runs 4a to 5). Run 5's record also carries `target_sha256`. |
| `tests.json` | The test-writer's record. |
| `test-review.json`, `test-review/round-N/` | The review of the tests. The size-M runs only: runs 1, 4b, 4c, 4d and 5. Run 5 has a `round-2/` as well. |
| `build.json` | The builder's note. |
| `verify.json` | The verifier's record. |
| `junit-tests.xml`, `junit-verify.xml` | What pytest reported when plumbline itself ran the test command, once for the tests gate and once for the verify gate. `large-0-plan/` has none: it ran no tests. |
| `review.json` | The merged review: findings, defenses, survivors, routes, gaps. |
| `review/round-N/` | The files of each review agent, which `review.json` was merged from. Run 5 has `round-1/` and `round-2/`. In runs 4b to 4d, which ran on 0.5.0, a review that ran again wrote over the first files, so only the last panel's files are kept. The same holds for `spec-review/` and `test-review/` in those runs. |
| `reduce.json` | The pass record: stage results, rounds, tokens, verdict. From 0.5.0 it also lists `open_findings` and `gaps`. `large-0-plan/` has none: it made no commit. |
| `ledger.jsonl` | The run's log, one JSON object per line. From 0.5.0 it has a `request` line, and a `leg` line each time a leg of the orchestrator ends. |

The README at the top of the repository says what each record holds.

## Paths inside the records

The records name each other by their original paths, `.plumbline/runs/<run id>/...` and `.plumbline/pass/<commit>.json`. That was their place in the working repository. Here they sit in the folders above. The names inside the files are unchanged, apart from the ten files described under "What was scrubbed".

## What was left out

- `.plumbline/runs/ACTIVE`: a pointer to the run in progress, not a record.
- `.plumbline/request.md` and `.plumbline/supplied-spec.json`: two files that sit beside the run folders in the working repository, not inside a run. The first is run 5's request, byte for byte the same as `feature-stats/request.md`. The second is the file a fix run's spec is supplied from. It now holds run 3's, with the same content as `fix-overdue-non-string/plan.json`, which plumbline wrote again in its own formatting. When the first build of this repository checked it, it held run 2's, which was byte for byte the same as `fix-overdue-bad-date/plan.json`.
- The test-writer's `stubs/` folder: scaffolding, and none was left at the end of any run.

## What was scrubbed

Paths scrubbed for publication. 32 of the 167 record files were edited: the eight ledgers, the fourteen junit files and ten JSON records. The other 135 files are byte-for-byte what the runs wrote. The first build of this repository edited 6 files (runs 1 and 2), and the update that added runs 3 to 5 edited 26.

| What | Runs 1, 2 | Runs 3 to 5 | Became |
| --- | --- | --- | --- |
| Agent transcript paths (`transcript` and `session_transcript` in the agent lines of the ledgers, and `agent_transcript_path` and `session_transcript` in the `leg` lines). Each was an absolute path into the machine's Claude Code folder. | 60, in 30 lines | 286, in 143 lines (130 agent lines and 13 `leg` lines) | `"<transcript>"` |
| Session ids (`session_id` of those lines) | 30 | 143 | `<session-1>` to `<session-3>` in runs 1 and 2, and `<session-4>` to `<session-6>` in runs 3 to 5. The same placeholder means the same session. Run 1 had two sessions, run 2 one. Run 3 is `<session-4>`, runs 4a to 4d were all one session, `<session-5>`, and run 5 is `<session-6>`. |
| junit `hostname` attributes | 4 | 10 | `&lt;host&gt;` |
| junit `timestamp` attributes | 4 | 10 | `&lt;timestamp&gt;` |
| pytest temporary folders whose name carried the user name (in `junit-tests.xml`) | 2 | 12 | `/tmp/pytest-of-&lt;user&gt;/` |
| `file` fields that held the absolute path of a run's `plan.json` on the machine (the findings of a spec review, and the `open_findings` of a pass record) | 0 | 16, in 10 JSON files | the same path from the repository root, such as `.plumbline/runs/<run id>/plan.json`. That is how the records name each other. |

The `&lt;` and `&gt;` are XML's way of writing `<` and `>` inside the junit files.

Agent ids (`agent_id`) are kept. They tell one agent of a run from another, and they name nothing on a machine. The time of each ledger line (`at`) is kept: it is in UTC.

The override record holds the display name of the user who made it, the same name the commits carry. It is kept as it is.

## Do the hashes still match?

A ledger pins files by sha256 in three places: the `pass` line (the pass record, and every record it lists), the `merge` lines (the files a review merge was built from), and the newest line for each record (`record_sha256`). Most pins match. Two things keep some from matching, and both are listed here.

**Paths scrubbed for publication; hashes refer to the original files.** The ten edited JSON records are pinned by a ledger, so their pins refer to the original files, not to the edited ones. Only the `file` fields changed. The ten files are:

- the spec review of `large-0-plan/`, `large-3-edit-remove/` and `feature-stats/`: `spec-review.json` and `spec-review/round-1/prosecutor-requirements.json` in each (six files);
- `reduce.json` of `large-3-edit-remove/` and of `feature-stats/`;
- the two pass records that are copies of those, `pass/917e870e5f2f9925535c75fb1b050cdb304458d2.json` and `pass/f288060db11a8e2f629d5c2c226329415e22a8e7.json`.

Each of their pins equals the sha256 of the file as the working repository holds it. The ledgers and junit files that were edited are pinned by nothing.

**A review that ran again.** In runs 4b to 4d, which ran on 0.5.0, a review stage that ran again after a fix wrote into the same `round-1/` folder, over the first files. A `merge` line from before the re-run names a file as it was then, and that version was overwritten, so the pin cannot match. 0.5.1 writes a re-run into a new round folder, as run 5 shows. For each such file, the newest `merge` line does match.

The counts:

- Runs 1 and 2: 46 hashes on the `pass` and `merge` lines, and all 46 match. The newest `record_sha256` of each of 29 records matches the file.
- Runs 3 to 5: 195 hashes on the `pass` and `merge` lines. 108 match. 9 refer to the original of an edited file. 78 name an earlier version of a review file that a re-run overwrote (35 in run 4b, 23 in run 4c, 20 in run 4d). The newest `record_sha256` of each of 101 records: 95 match, and 6 refer to the original of an edited file. Run 4a made no commit, so it has `merge` lines and no `pass` line.

Older lines for a record that was rewritten after a failed gate name an earlier version of the file, which is not kept. In runs 1 to 5 the newest line for a record never names a version that is missing.

To check one, compare `sha256sum runs/feature-due-dates/plan.json` with the entry for `.plumbline/runs/ccffe51-20260930T055131Z/plan.json` in the last line of `runs/feature-due-dates/ledger.jsonl`.

## What you cannot redo

`plumbline.py tokens` reads the agent transcripts that a ledger points to, and the orchestrator's too (the `leg` lines). Those transcripts are not published, so the command cannot be run again on these ledgers. The token counts in each `reduce.json` stay as they were counted.
