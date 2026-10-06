# plumbline-demo

Real runs of the [plumbline](https://github.com/krajgh/plumbline) pipeline for Claude Code, on a tiny to-do list program, with the records they wrote.

## What this is

`tasklist` is a tiny to-do list for the command line. It is written in Python 3.11+ and uses only the standard library.

```
$ python -m tasklist add "Buy milk"
added 1
$ python -m tasklist list
[ ] 1 Buy milk
$ python -m tasklist done 1
done 1
```

[plumbline](https://github.com/krajgh/plumbline) is a Claude Code plugin. It sends a change through a pipeline of subagents: plan, spec review, tests, test review, build, verify and review. A small change skips some of these stages. Each stage writes a typed JSON record. A mechanical gate checks that record before the next stage starts.

This repository has adopted plumbline: `plumbline.toml` is committed. It also holds the records of eight real runs, made in the Claude Code desktop app between 2026-09-30 and 2026-10-06: two on plumbline 0.4.x, a fix on the orchestrator that came with 0.5.0, a request of size L run as a plan and three parts, and a feature on a dev copy of 0.5.1, tested before its release. Seven of the eight ended in a commit. The plan of the size-L request builds nothing, as plumbline does at that size. Eight runs on one small program are a few data points, not a benchmark.

### The runs

| Run | Request | Intent, size | plumbline | Branch | Rounds that failed | Questions to the user | Open at the pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | due dates | feature, M | 0.4.0, then 0.4.1 | `due-dates` | 1 | 3 | 8 findings, 3 gaps (not recorded) |
| 2 | a malformed stored due date crashes `list --overdue` | fix, S | 0.4.2 | `overdue-bad-date` | 1 | 1 | 3 findings, 4 gaps (not recorded) |
| 3 | a stored due date that is not a string crashes `list --overdue` | fix, S | 0.5.0 dev copy | `overdue-non-string` | 0 | 1 | 1 finding, 3 gaps |
| 4a | tags, priorities, and edit and remove, as one request: the plan | feature, L | 0.5.0 | none: nothing is built at size L | 0 | 1 | 2 findings (carried into the parts) |
| 4b | part 1: tags | feature, M | 0.5.0 | `organize-tags` | 1 | 4 | 3 findings, 4 gaps |
| 4c | part 2: priorities | feature, M | 0.5.0 | `organize-priorities` | 2 | 2 | 0 findings, 2 gaps |
| 4d | part 3: edit and remove | feature, M | 0.5.0 | `organize-edit` | 0 | 1 | 4 findings, 3 gaps |
| 5 | a `stats` command | feature, M | 0.5.1 dev copy | `stats` | 0 | 3 | 5 findings, 0 gaps |

How to read the table:

- *Rounds that failed* counts the times a gate rejected a stage's work and the stage ran again. A gate check made too early, while an agent was still editing its record, is left out: the ledgers hold 10 of them in run 4b and 2 in run 4c. So is the plan gate failure in run 1's ledger, which was a miscount, described in run 1.
- *Questions to the user* counts the decisions the session asked the user to make, taken from the sessions' transcripts. It leaves out Claude Code's own check before it acts on a pasted request, and the questions about merging and pushing between runs. In run 1 the questions were what to do when the planner could not hand its report back (the user stopped the session), whether to delete the test-writer's stubs (yes), and whether to fix the findings or ship (ship). In run 2 it was whether to fix the non-string crash first or push as it was (push).
- *Open at the pass* is what the run left open: the findings that were not BLOCKING, and the detective's gaps. The versions in runs 1 and 2 did not copy them to the pass record, so for those two the counts come from the review records. From run 3 on, the pass record lists them.

| Branch | What it holds |
| --- | --- |
| `main` | The starting point, tasklist 0.1.0 adopted by plumbline (commit `ccffe51`), plus two commits that add this README, the licence files and the records in `runs/`. |
| `start` | The starting point alone (commit `ccffe51`), without this README or the records. Use it to try a request yourself. |
| `due-dates` | The result of run 1 (commit `109e295`). |
| `overdue-bad-date` | The result of run 2 (commit `cf98e93`). It builds on `due-dates`. |
| `overdue-non-string` | The result of run 3 (commit `183da93`). It builds on `overdue-bad-date`. |
| `organize-tags` | Part 1 of run 4, tags (commit `a061f09`). It builds on `overdue-non-string`. |
| `organize-priorities` | Part 2 of run 4, priorities (commit `0f44eee`). It builds on `organize-tags`. |
| `organize-edit` | Part 3 of run 4, edit and remove (commit `917e870`). It builds on `organize-priorities`. |
| `stats` | The result of run 5 (commit `f288060`). It builds on `organize-priorities`, not on `organize-edit`. |
| `latest` | Every feature, merged: `stats` merged into `organize-edit` (commit `c843610`). No run covers this merge. An override record does. |

## The requests

Each request below was pasted into a Claude Code session as it is written here. The three parts of run 4 are the exception: the session wrote each part's request from the plan's split, and each one is in its run's `request.md`.

In a review, prosecutors look for what is wrong. Each one files findings, and each finding carries a quote of the code and a case that fails. Defenders then try to refute each finding with a quote. A detective, who runs last, lists what is missing. Every finding has a severity:

- BLOCKING: it breaks a stated acceptance criterion, loses data, exposes a secret, or breaks the main path.
- MAJOR: wrong behaviour on a realistic path, with limited reach or a workaround.
- MINOR: an edge case, or an inconsistency.

Only a BLOCKING finding stops a run.

From 0.5.0, the panel of three defenders is called in only when a finding is BLOCKING. Otherwise one "screening" defender answers all the findings. A defender that concedes a finding can also claim that it is worse than filed. Runs 1 and 2 used three defenders every time.

### Run 1: a feature

```
/plumbline:run Work on a new branch `due-dates`. Add due dates to tasks:
1. `add` takes an optional `--due YYYY-MM-DD` and stores the date with the task.
2. A malformed or impossible date (for example `2026-02-30` or `tomorrow`) is refused: exit code 2, one line on stderr naming the value, and nothing is stored.
3. `list` shows a task's due date after its title, as `[ ] 3 Pay rent (due 2026-10-01)`; tasks without a due date print exactly as today.
4. `list --overdue` shows only open tasks whose due date is before today, oldest due date first; how "today" is supplied must be testable without the real clock.
5. Task files written by version 0.1.0 (no due dates) still load, list and complete exactly as before.
Expect size M: code plus tests of roughly 100 to 200 lines.
```

- **Result.** Branch `due-dates`, commit `109e295`: 5 files, 260 lines added and 7 removed. Size M. All 38 tests pass: 17 that were there already and 21 new cases.
- **Records.** `runs/feature-due-dates/`.

**Stages and rounds.** A round is one attempt at a stage, which its gate then accepts or rejects. The number in brackets is the most rounds the pipeline allows.

| Stage | Who | Rounds | What it did |
| --- | --- | --- | --- |
| intake | the main session | 1 | Classified the change: code, intent feature, size M. The size was declared up front and measured again at the pass: M both times. |
| plan | 1 planner | 1 (2) | Wrote the spec: 6 acceptance criteria, 8 interfaces, 6 risks. |
| tests | 1 test-writer | 2 (3) | Wrote 11 tests (21 cases), each failing before the code existed. Round 1 failed its gate: the stub check said not every test failed on an assertion. |
| test-review | 1 prosecutor | 1 (2) | Reviewed the tests: 4 findings, none blocking. |
| build | 1 builder | 1 | Changed `tasklist/core.py`, `tasklist/cli.py` and `README.md`. It never saw the tests. |
| verify | 2 verifiers | 1 (3) | Ran the tests and the checks: 38 passed. The first verifier stopped: the test-writer's stub files made the change measure as size L, and plumbline builds nothing at L. |
| review | 5 prosecutors, 3 defenders, 1 detective | 1 (3) | 4 findings, none blocking, and 3 gaps. |
| reduce | the main session | 1 | Wrote the pass record for `109e295`. |

The pass record (`reduce.json`) counts every attempt, so it shows tests 3 and verify 2. The test-writer was resumed a third time after the build, to remove its stub files. The first verifier counts as an attempt.

The run began on plumbline 0.4.0, in a session that was not in auto mode. The planner could not hand its report back and stopped four times. 0.4.0 counted each stop as a round, so the plan gate said "round 4 of 2". plumbline 0.4.1 counts agents, not stops, and the run was resumed in a session in auto mode. The stub trouble led to the fixes in 0.4.2. plumbline's hooks, which enforce each agent's role, denied 24 calls. 9 stopped real overreach, such as the builder globbing the repository root, which would have shown it the tests. The other 15 were agents trying a command their role does not allow.

**Review.** The tests review and the final review found 4 findings each.

| | BLOCKING | MAJOR | MINOR |
| --- | --- | --- | --- |
| Tests review (1 lens) | 0 | 1 | 3 |
| Final review (5 lenses) | 0 | 1 | 3 |

The tests review found a missing test for the clock fallback (MAJOR). Its three MINOR findings: only one bad `TASKLIST_TODAY` value is tested, no CLI test covers the tie-break by id, and no test checks that `overdue_tasks` never reads the clock.

The final review found:

- `correctness-1`, MINOR: a malformed due date in the task file crashes `list --overdue` with a `KeyError`, or wrongly blames `TASKLIST_TODAY`. The boundaries lens found the same bug (`boundaries-1`, MINOR).
- `tests-1`, MAJOR: no test covers `TASKLIST_TODAY` unset or empty, which should fall back to the real clock.
- `tests-2`, MINOR: the date tests leave out non-ASCII digits and trailing newlines, so a weaker date check would go unnoticed.

The security and data lenses found nothing. All 3 defenders conceded all 4 findings: 12 verdicts, no refutation. The detective found 3 gaps:

- A `--due` value that starts with a dash, such as `--due -5`, gets argparse's own usage error, not the one-line error the spec asks for.
- No test pins which error wins when the title is blank and the due date is bad.
- No test checks that `overdue_tasks` never reads the clock or the environment.

**Time and tokens.**

- About 18 minutes of active machine time: plan 1.4 min, tests 3.4 min (plus about 2 min to remove the stubs), test review 0.8 min, build 0.6 min, verify 1.2 min, review 4.7 min. The second session ran 46 minutes. About 30 of them went on waiting for the user at the keyboard. The test command takes under a second.
- The 15 agents wrote at least 42K output tokens, took in 416K fresh input tokens and read 2.7M tokens from the cache.
- The main session, which orchestrates the run, wrote 26K output tokens, wrote 114K tokens to the cache and read 5.3M from it.

Fresh input is input the model takes in anew: plain input, or input written to the prompt cache. A cache read is input served from the cache, which costs less. The agents' output counts are lower bounds, because some messages never recorded their final count. Agents run on small models. The main session runs on a larger one, and it is the biggest spender: it holds about two thirds of all the cache reads.

**Open items.** No finding was BLOCKING, so none had to be fixed. The number of tests stayed at 38 from the first measured run to the pass. The session asked whether to fix the findings first or ship as is, and the answer was ship as is. All 8 findings (some of them the same gap, found twice) and all 3 gaps were open when the run passed. The second run fixed the one bug behind `correctness-1` and `boundaries-1`. It touched nothing else on this list.

### Run 2: a fix

The request was pasted after a line of the user's own.

```
/plumbline:run The intent is fix. Work on a new branch `overdue-bad-date` from main. `list --overdue` mishandles a task whose stored due date is malformed (for example a hand-edited "due": "soon"): with TASKLIST_TODAY unset it crashes with a KeyError traceback, and with TASKLIST_TODAY set and valid it wrongly reports "invalid TASKLIST_TODAY". Expected: exit code 2 and one line on stderr naming the task's id and its bad due date; the TASKLIST_TODAY error only when that variable is set and invalid. Expect size S.
```

- **Result.** Branch `overdue-bad-date`, commit `cf98e93`: 2 files, 42 lines added and 1 removed. Size S. All 40 tests pass: the 38 from the first run and 2 new cases.
- **Records.** `runs/fix-overdue-bad-date/`.

**Stages and rounds.** The fix intent skips the planner and asks for tests that fail on today's code.

| Stage | Who | Rounds | What it did |
| --- | --- | --- | --- |
| intake | the main session | 1 | Classified the change: code, intent fix, size S. The size was declared up front and measured again at the pass: S both times. |
| plan | nobody | 0 | The spec was supplied from a file. It has one acceptance criterion. |
| tests | 1 test-writer | 2 (3) | Wrote 1 test (2 cases) that fails on today's code. Round 1 failed its gate: it had a guard case that already passed. |
| build | 1 builder | 1 | Changed `tasklist/cli.py`: 8 lines added, 1 removed. |
| verify | 1 verifier | 1 (3) | Ran the tests and the checks: 40 passed. |
| review | 2 prosecutors, 3 defenders, 1 detective | 1 (3) | 3 findings, all MINOR, and 4 gaps. |
| reduce | the main session | 1 | Wrote the pass record for `cf98e93`. |

This run used plumbline 0.4.2. It began from a `main` that held the feature: the session first fast-forwarded `main` to `due-dates` and pushed it, because plumbline measures a change from the remote's default branch. The push gate refused the one command that merged and pushed at once, as designed. The push on its own was allowed.

**Review.** 3 findings: 0 BLOCKING, 0 MAJOR, 3 MINOR. All 3 defenders conceded all 3 findings: 9 verdicts, no refutation. The detective found 4 gaps.

**Time and tokens.**

- About 6.5 minutes of pipeline time. The whole session took 9 minutes, including the merge and push of `main`.
- There were 9 agents and 10 stops, because the test-writer was resumed for round 2. The agents wrote at least 17.5K output tokens, took in 157K fresh input tokens and read 1.15M tokens from the cache.
- The main session made 36 calls: 13K output tokens, 58K written to the cache and 2.3M read from it.

**Open items.** The run passed with 3 findings and 4 gaps open, on purpose. plumbline 0.4.2 does not carry them forward. The pass record lists none of them, and git ignores `.plumbline/`, so they stay in this run's `review.json` and nowhere else. The session reports them once, in its chat. plumbline 0.5.0 changed that: a pass record now lists them (see run 3). Here they are.

The findings, all MINOR:

- `correctness-1`: a stored due date that is not a string, such as `null` or a number, makes `list --overdue` crash with a `TypeError` traceback, not the one-line error.
- `tests-1`: the test checks the task id with a bare `"1" in line`, so a wrong id, or any message that contains a 1, would pass.
- `tests-2`: no test covers a done task with a malformed due date, or a file with several tasks.

The prosecutor rated the crash MINOR. But the finding names AC-1 as its rule, and two of the three defenders wrote that the crash fails AC-1. A broken acceptance criterion is BLOCKING by the rubric above. A defense record had no field for severity, so the gate never saw this. 0.5.0 added one: a defender that concedes a finding can now claim a higher severity.

The detective's gaps:

- A well-formed but impossible stored date such as `2026-02-30`, and an empty string, are not tested.
- No test shows that a done task's bad date is ignored, or that a file with several tasks names the right id.
- The non-string crash above.
- With several malformed tasks, the first one in file order is named, not the lowest id, and no test pins that. No test combines an invalid `TASKLIST_TODAY` with a malformed stored date either.

Run 3 fixed the non-string crash, and nothing else on this list.

### Run 3: a fix, run by the orchestrator

The request was pasted after a line of the user's own, as in run 2. It asks for the fix that run 2 left open.

```
/plumbline:run The intent is fix. Work on a new branch `overdue-non-string` from main. `list --overdue` still crashes with a traceback when a stored due date is not a string (for example a hand-edited "due": null or "due": 20261001), because only ValueError is caught. Expected: the same handling as any malformed due date: exit code 2 and one line on stderr naming the task's id and its bad due date. Expect size S.
```

- **Result.** Branch `overdue-non-string`, commit `183da93`: 2 files, 22 lines added and 1 removed. Size S. All 42 tests pass: the 40 from before and 2 new cases.
- **Records.** `runs/fix-overdue-non-string/`.

**What was new: the orchestrator.** This is the first run made with the orchestrator, which came with plumbline 0.5.0. The run used a dev copy, about twenty minutes before the release. Until then the main session, the one the user talks to, did the control work as well: it launched each agent, ran each gate and read each report, and each of those was a turn that read the whole context again, on a large model. From 0.5.0 the main session settles the intent and the size, starts the run, and launches `plumbline:orchestrator` in the background with the run's id. The orchestrator is a smaller model. In one *leg* it launches the stage agents, runs the gates, merges the reviews and sends a stage back when its gate fails. It hands back a report of at most 15 lines when every gate has passed, or when a decision comes up that only the user can make. The main session then asks the user, and commits and records the pass. The stage records are the same as before. The ledger gains a `leg` line each time a leg ends, and the pass record counts the orchestrator's tokens apart.

**Stages and rounds.**

| Stage | Who | Rounds | What it did |
| --- | --- | --- | --- |
| intake | the main session | 1 | Classified the change: code, intent fix, size S. The size was declared up front and measured again at the pass: S both times. |
| plan | nobody | 0 | The spec was supplied, with one acceptance criterion, as in run 2. |
| tests | 1 test-writer | 1 (3) | Wrote 1 test (2 cases) that fails on today's code: 42 tests, 2 of them failing. |
| build | 1 builder | 1 | Changed one line of `tasklist/core.py`. `parse_date`, the function every due date goes through, now rejects a value that is not a string with the same error as any other bad date. |
| verify | 1 verifier | 1 (3) | Ran the tests and the checks: 42 passed. |
| review | 2 prosecutors, 1 screening defender, 1 detective | 1 (3) | 1 finding, MINOR, and 3 gaps. |
| reduce | the main session | 1 | Wrote the pass record for `183da93`. |

The orchestrator's one leg took about 6 minutes, from the start of the run to the end of the review. The user then chose to ship, and the pass was recorded. The ledger spans about 8 minutes.

**What the orchestrator changed, measured.** Run 2 is the nearest comparison: a fix of the same size and intent, run by the main session alone. They are different bugs, and each is one run.

| | Run 2 (0.4.2, no orchestrator) | Run 3 (0.5.0, orchestrator) |
| --- | --- | --- |
| Main session: calls | 36 | 15 |
| Main session: cache reads, cache writes, output | 2.29M, 58K, 13.2K | 0.69M, 31K, 4.7K |
| Orchestrator: calls; cache reads | none | 13; 0.28M |
| Stage agents | 9, with 1.15M cache reads | 7, with 0.64M cache reads |
| Defenders | 3 | 1 (a screening defender) |
| Rounds | tests 2, verify 1, review 1 | tests 1, verify 1, review 1 |
| Open items after the pass | in the chat only | on the pass record |

The main session's cache reads fell by 70%, and they are the reads on the most expensive model. All cache reads together fell from 3.44M to 1.61M, and only 0.69M of the new total is the large model's. The orchestrator needed 13 calls for its whole leg. A leg needs only the run's id, because the run's state is on disk, and its context started at 13K tokens against 39K to 41K for the main session. The stage agents' drop has other causes too: run 2's tests stage took 2 rounds where this one took 1, and 0.5.0 sends one screening defender where run 2 sent three. So this is one run each, on different bugs: a direction, not a measure. The agents' output counts are lower bounds, as in run 1.

**Review.** 1 finding: 0 BLOCKING, 0 MAJOR, 1 MINOR. The screening defender conceded it. The detective found 3 gaps.

**Open items.** The user was asked whether to ship or to fix the open items first, and chose to ship. This time the items were kept: the pass record lists them (`open_findings` and `gaps`), and `plumbline.py open` prints them. The finding is `tests-1`, MINOR: the test checks the task id with a bare `"7" in lines[0]`, the same loose check as run 2's `tests-1`. The gaps: no test calls `parse_date` directly with a value that is not a string; only `null` and an integer are tested, not `true`, a list, a dict or a float; and no test covers a done task with a due date that is not a string.

### Run 4: a request of size L, as a plan and three parts

**What size L means.** plumbline sizes a change by its changed lines, added and removed. S is up to 50, M is up to 400, and L is more. (0.5.0 counted every line alike. 0.5.1 counts a line of a test file as half: see part 1.) At size L plumbline builds nothing. It runs the intake, the plan and the spec review, and the planner's spec ends with a `split_proposal`: changes of size M or smaller. Each part then runs as a run of its own, on its own branch.

The spec review is new in 0.5.0, for sizes M and L. Nothing else checks the spec against the request, and everything after the plan is checked against the spec, so a misread request would pass every gate. plumbline stores the request in the run (`request.md`). A prosecutor with the `requirements` lens compares it with the spec's acceptance criteria and test plan, and a screening defender answers the findings.

The request, pasted after a line of the user's own:

```
/plumbline:run Work on a new branch `organize` from main. Add tags, priorities, and edit and remove to tasklist:
1. `add` takes `--tag NAME`, which may be repeated; tags are stored with the task. A tag is lowercase letters, digits and dashes; anything else is refused with exit code 2, one line on stderr naming the value, and nothing stored.
2. `tag ID NAME` adds a tag to an existing task and `untag ID NAME` removes one; an unknown id exits 2 with one line on stderr.
3. `list --tag NAME` shows only tasks carrying that tag, and combines with `--all` and `--overdue`. `list` prints a task's tags after its title and due date, as `#work #home`.
4. `add` takes `--priority high|normal|low`, default `normal`; any other value is refused like a bad tag.
5. `list` orders open tasks by priority (high, then normal, then low), then by id, and marks a high-priority task with `!` before its title; `list --overdue` keeps its oldest-due-first order.
6. `edit ID` changes only the fields it is given: `--title`, `--due DATE` or `--no-due`, `--priority`. An unknown id or an invalid value exits 2 and changes nothing.
7. `remove ID` deletes a task and prints `removed ID`; an unknown id exits 2.
8. Task files written by earlier versions (no tags, no priority) still load, list, complete and edit as before, and a task without tags or a priority prints exactly as today.
Expect size L: code and tests well over 400 lines. Propose a split.
```

#### Run 4a: the plan

- **Result.** No commit, so there is no pass record. **Records.** `runs/large-0-plan/`.
- **What it did.** The intake declared size L. One planner wrote the spec: 8 acceptance criteria, 12 interfaces, 13 test scenarios, 6 risks and a split into three changes. The spec review's prosecutor filed 2 findings, both MINOR, and the screening defender conceded both. No gate failed. The run took about 3 minutes.
- **The split.**
  1. Tags, size M.
  2. Priorities, size S or M.
  3. Edit and remove, size M. It needs part 2, to validate `--priority`.
- **The two findings.** `requirements-1`: AC-5 also sorts `list --all` by priority, although the request orders only open tasks. `requirements-2`: the test for an empty tag checks that the error line "contains the value", and every line contains an empty one.
- **The question to the user.** The session showed the split and the two findings, and asked how to proceed: accept the split, fix the findings first, or stop. The user answered in their own words: start part 1 on a new branch from `main`, and carry the two findings into the parts' requests. Each finding went into the request of the part it belongs to.

#### The parts

Each part had to start from a `main` that held the parts before it. plumbline measures a change from the remote's default branch, and this way it measured each part alone. Before each part the user had the session fast-forward `main` to the previous result and push it.

Rounds per stage, as the pass records count them:

| Stage | Part 1: tags | Part 2: priorities | Part 3: edit and remove |
| --- | --- | --- | --- |
| plan | 1 | 2 | 1 |
| spec review | 1 | 1 | 1 |
| tests | 6 | 4 | 2 |
| test review | 1 | 1 | 1 |
| build | 3 | 1 | 1 |
| verify | 7 | 2 | 2 |
| review | 1 | 1 | 1 |

These count every attempt, the fix legs the user chose included, so they run higher than the rounds that failed (see the table of runs). A review's round is its record's round, so a review panel that ran again after a fix still counts as round 1: the panel ran 3 times in part 1, and twice in each of parts 2 and 3.

#### Part 1: tags

- **Result.** Branch `organize-tags`, commit `a061f09`: 3 files, 398 lines added and 2 removed, 279 of the added lines in tests. Size M. All 105 tests pass: the 42 from before and 63 new cases.
- **Records.** `runs/large-1-tags/`.
- **Gates and rounds.** One round failed. Verify failed on its first attempt: 3 of 79 tests failed. The bug was in the tests: the helper that takes a task id out of a `list` line took the wrong word. The orchestrator sent the work back to the test-writer, and the code needed no change. In the fix leg the orchestrator also checked the tests gate 10 times in 30 seconds, while the test-writer was still editing its record. Six of those checks ran the test command. No round was counted, because no agent had stopped in between, but the work was wasted. 0.5.1 checks a record's trace before it runs any command, and gives the orchestrator a `wait` command for an agent it woke by a message.
- **The size, and the first question.** plumbline then measured the change at 404 lines, over M's 400, and the orchestrator handed back. 284 of the 404 lines were tests (`tests/test_tags.py`) and 120 were code. A well-tested part had crossed into size L on its tests alone, and splitting a feature because its tests are thorough is backwards. 0.5.1 changed the measure: a test line counts as half, so the same part measures 262 and stays size M. The session asked the user what to do: split tags again, trim the tests under 400, or stop. The user chose to trim the tests, the option the session described as the cheaper way, because the change was only 4 lines over.
- **The second question.** After the trim every gate passed, and the review left 7 findings and 4 gaps open, none BLOCKING. Most were about `protect_dashes`, a function that rewrote the command line so that a tag could start with a dash. It had no tests (MAJOR). It turned `tag --help` into a task id, protected only the last word, and glued `--tag --due` together. A stored `"tags"` value that is not a list also gave a wrong match or a crash. The user chose to fix first: delete `protect_dashes` rather than patch it, because argparse already takes `--tag=-x` (and `--` for `tag` and `untag`), and treat a malformed stored `tags` the way a malformed due date is treated: exit 2 and one line naming the task.
- **The third question.** The fix leg passed every gate (92 tests, about 383 lines), and the orchestrator recommended shipping. The main session tried the result first and found the instruction only half met: plain `list` still crashed with a traceback on `"tags": 5`, and printed `#a #b` for `"tags": "ab"`. It asked again, and the user chose to finish the job. 0.5.1 changed the orchestrator's report: it now says, item by item, whether the user's decision is fully met, and recommends shipping only when it is.
- **The fourth question.** Every gate passed (105 tests), and only missing tests were open. The user chose to ship.
- **Time.** 129 minutes on the clock, 94 of them waiting for the user.
- **Open at the pass.** 3 findings, all MINOR, and 4 gaps. The findings: the spec review's `requirements-1` (how a tag that starts with a dash reaches the program); no test of a malformed stored `tags` on a done task under `list --all` or `--overdue`; and no test of `--overdue` together with `--tag` when a stored due date is bad. The gaps: no test lists a finished task that carries tags; `untag` removes only the first copy of a duplicated tag; no test pins which error wins in `list --overdue` when a bad due date and bad tags sit on different tasks; and no test pins the order of the checks in `add`.

#### Part 2: priorities

- **Result.** Branch `organize-priorities`, commit `0f44eee`: 3 files, 242 lines added and 5 removed, 201 of the added lines in tests. Size M. All 143 tests pass: the 105 from before and 38 new cases.
- **Records.** `runs/large-2-priorities/`.
- **The old `list --all` order.** The first spec changed `list --all` for old files: open tasks first, then done tasks by id. An old file with task 1 open, task 2 done and task 3 open used to list 1, 2, 3, and would now list 1, 3, 2. That breaks item 8 of the request, which says a task without tags or a priority "prints exactly as today". The tests already written for it rewrote two existing expectations to match. The request that the session wrote for this part had told the planner to state how `list --all` orders done tasks, and the planner answered with a new order, not the one that keeps old output. The main session saw the rewritten expectations in the test diff and asked the user. The test review had not run yet, so it is not known whether the pipeline would have caught this alone. The options were: priority, then id, for every task shown, done ones included (so an old file lists in id order, as today); plain id order under `--all`; or keep the spec. The user chose the first, and the planner ran again.
- **Gates and rounds.** Two rounds failed. The first round of the tests stage failed its gate, because the stub check said not every test failed when it ran. After the replan, the spec review's gate refused: the prosecutor's record had changed after merge-review read it, because the review had run again into `round-1/`, over the first files. (0.5.1 gives a review that runs again a new round folder.) The ledger also holds 2 early checks of the tests gate, made while the test-writer was still revising.
- **The questions.** Two: the `list --all` order above, and the last report. Every gate had passed (141 tests), and what was open was test-only, the largest item a MAJOR: no test of a bad stored priority on a done task under `--all`. The user chose to add that test and ship, which took the suite to 143 tests.
- **Time.** 35 minutes on the clock, 15 of them waiting for the user.
- **Open at the pass.** No findings, and 2 gaps: no test that a bad stored priority on a done task is reported by `list --all --tag X`, and no test that `add --priority high` with `--due` and `--tag` keeps all three.

#### Part 3: edit and remove

- **Result.** Branch `organize-edit`, commit `917e870`: 3 files, 254 lines added, 166 of them in tests. Size M. All 162 tests pass: the 143 from before and 19 new cases.
- **Records.** `runs/large-3-edit-remove/`.
- **Gates and rounds.** No round failed. In the pass record, tests 2 and verify 2 count the fix leg that the user chose.
- **The question.** One. Every gate had passed (162 tests), and what was open was test-only. The largest item was a MAJOR from the test review: the success tests ran only on bare tasks, so nothing pinned that `edit` leaves a task's other keys alone. The user chose to add that test and ship.
- **A stale review.** The fix leg did add the test: the committed tests edit a task that carries a due date, tags, a priority and a done state. But the test review did not run again over the changed tests, and 0.5.0's `pass` did not notice. So the pass record still lists the MAJOR as open, although it was fixed. 0.5.1 closes this: a review of the tests or of the plan records a hash of what it read (`target_sha256`). Its gate, and `pass`, fail once that has changed, and the review has to run again as the next round.
- **Time.** 16 minutes on the clock, 1 of them waiting for the user.
- **Open at the pass.** 4 findings and 3 gaps. The findings: the stale MAJOR above, and 3 MINOR ones. The spec's test plan never checks an empty-string option such as `--title ''`. A core test would not catch a partial edit. No test pins that an unknown id is reported before a missing option. The gaps: no test applies several valid options in one edit; no test of an unknown id together with `--due` and `--no-due`; and the strictness of `--priority` and `--due` inputs (`HIGH`, `' high'`, a date with a leading space) is not pinned.

#### What the whole sequence cost

A request of size L, run with the orchestrator as a plan and three size-M parts, changed about 900 lines (nearly three quarters of them tests) in 4.4 hours on the clock. About 75 minutes of that was machine time. The rest was the user answering eight questions and starting each part. It read about 23 million tokens from the cache, 5.3M of them in the main session, so that session's share fell from two thirds in run 1's size-M feature to under a quarter. A part read between 4.5 and 11 million, and two thirds of the reads of the orchestrator and the agents came in fix rounds that the user chose: 6 of the 8 answers sent a part back. That is one run, so a direction rather than a measure.

**What the folders hold.** In parts 1 to 3 a review that ran again after a fix wrote its files over the first panel's, because 0.5.0 re-used `round-1/`. Each review folder (`spec-review/`, `test-review/` and `review/`) therefore holds the last panel only. The first panel's findings, such as part 1's seven, are known only from the question the user was asked: the ledger's hashes show that the first files existed, not what they said. 0.5.1 writes a re-run into a new round folder, as run 5's `round-2/` folders show.

### Run 5: a feature, on a dev copy of 0.5.1

This run tested a dev copy of 0.5.1 in a new session, before the release. The request is a feature of size M over all three fields the earlier runs added (tags, priority and due date), so it touches their conventions. Item 5 leaves one question open on purpose: does a malformed value on a done task stop `stats`? The request was pasted after a line of the user's own.

```
/plumbline:run Work on a new branch `stats` from main. Add a `stats` command to tasklist:
1. `stats` prints, one per line and in this order: `open: N`, `done: N`, `high: N`, `normal: N`, `low: N` (open tasks by priority), and `overdue: N` (open tasks whose due date is before today, as `list --overdue` decides it, with TASKLIST_TODAY honoured).
2. Then one line per tag carried by an open task, as `#tag: N`, ordered by count (highest first), then by tag name.
3. `stats --tag NAME` limits every figure to tasks carrying that tag, and prints no per-tag lines.
4. An empty or missing task file prints the six count lines with 0 and exits 0.
5. A malformed stored value (due date, tags or priority) is reported the way `list` reports it: exit 2, one line on stderr naming the task by id, nothing on stdout.
6. Task files written by earlier versions (no tags, no priority, no due date) count as normal priority with no tags.
Expect size M.
```

- **Result.** Branch `stats`, commit `f288060`: 3 files, 248 lines added, 53 of code and 195 of tests. Size M: in 0.5.1 the change weighs 151 lines, because a test line counts as half. All 173 tests pass: the 143 from the commit it was built from and 30 new cases.
- **Records.** `runs/feature-stats/`.
- **Built from part 2, not part 3.** `stats` was branched from `main` as it stood, which held parts 1 and 2 (commit `0f44eee`) but not part 3. The intake question said so, and the user confirmed. The reason is in "What the dev test found" below.

**Stages and rounds.** Every gate passed in round 1 of the first leg. The user then chose to fix the open test gaps, so a second leg ran the tests, the test review, verify and the review again, as round 2.

| Stage | Who, in each round | Rounds | What it did |
| --- | --- | --- | --- |
| intake | the main session | 1 | Classified the change: code, intent feature, size M. The session asked the user to confirm. |
| plan | 1 planner | 1 | Wrote the spec: 8 acceptance criteria, 3 interfaces, 5 risks. |
| spec review | 1 prosecutor, 1 screening defender | 1 | 2 findings, both MINOR, both conceded. |
| tests | 1 test-writer, then another | 2 (3) | The first leg took the suite to 162 tests. The second added 11 cases: 173. |
| test review | 1 prosecutor | 2 (2) | Round 1: 4 findings, all MINOR. Round 2: 2 findings, MINOR. |
| build | 1 builder | 1 | Changed `tasklist/core.py` and `tasklist/cli.py`. It never saw the tests. |
| verify | 1 verifier | 2 (3) | Ran the tests and the checks: 162 passed in round 1, 173 in round 2. |
| review | 5 prosecutors, 1 screening defender, 1 detective | 2 (3) | Round 1: 2 findings and 2 gaps. Round 2: 1 finding. All MINOR. |
| reduce | the main session | 1 | Wrote the pass record for `f288060`. |

**The questions.** Three. First, the intake: feature, size M. Then, with every gate green, whether to fix or ship. Open were gaps in the tests (a duplicated tag in one task; the order of the checks between tags, due date and priority; an empty `TASKLIST_TODAY`; `--tag` with a bad value on a task outside the tag; the exact wording of an error) and one reading of the request, below. The user chose to fix the tests first. After round 2 the session asked once more, and the user chose to ship.

**One reading of the request.** Item 5 says a malformed stored value is reported the way `list` reports it, and does not mention done tasks. The planner chose: open tasks are always checked, and a done task's tags only under `--tag`. Plain `list` does not check the done tasks it hides either. The spec review still filed it as a MINOR finding, that the spec narrows what the request says, and it stands among the open items.

**What the dev test found.** Two things. Both are fixed in the published 0.5.1.

1. *A stale-review check that uncovered commits passed under 0.5.0.* 0.5.1 adds a check that a review of the plan or of the tests runs again when the plan or the tests change after it. Each such review record now carries a hash of what it read (`target_sha256`). The user's first message in the session asked it to fast-forward `main` to part 3 and push it. `status` said that part 3's commit was not covered: its spec review and test review had been merged under 0.5.0 and carried no hash, and the new check read that as stale. Merging them again was refused, and nothing was pushed. The session asked whether to run both reviews again or to push without coverage, and the user went on to the next request. The fix: a review record with no hash is not checked for staleness, and every review that 0.5.1 merges carries one. The session went on to build `stats` from `main` as it was.
2. *A `wait` that timed out twice on an agent that had already stopped.* A message that wakes an agent returns at once, so 0.5.1 gives the orchestrator a `wait` command that returns when that agent has stopped. In the second leg the orchestrator started a fresh test-writer in the foreground. It stopped within a minute. The orchestrator then ran `wait` for it anyway, as its prompt said to after a message. `wait` looked for a stop after its own start, and for an agent that has already stopped none ever comes. It timed out after 9 minutes, the orchestrator ran it again, and it timed out again. That cost 18 minutes, 73% of the leg. The command makes no model calls while it blocks, but each wait outlasted the prompt cache, so the orchestrator wrote about 24K tokens to the cache again, twice. The fix: `wait` returns at once for an agent that has stopped, and the prompt says that `wait` follows a message only, never a foreground launch.

The rest of 0.5.1 held. No gate failed. The reviews that ran again went into new folders (`review/round-2/`, `test-review/round-2/`). The spec review and the test review carry `target_sha256`. No open item was stale.

**Time and tokens.** 63 minutes on the clock, 28 of them waiting for the user and 18 lost to the `wait` timeouts. The main session made 14 calls and read 0.76M tokens from the cache. For part 3 of run 4 these were 10 calls and 1.15M. The orchestrator ran 2 legs, with 36 calls and 134K of fresh input, 48K of it the two cache re-writes after the `wait` timeouts. The 24 stage agents read 2.58M. All cache reads came to 4.29M, 18% of them in the large model. It is one run, and the user's choices decided the second leg. The agents' output counts are lower bounds.

**Open items.** 5 findings, all MINOR, and no gaps. Two are from the spec review: the done-task reading above, and that AC-8 puts the branch requirement in a test (`git branch --show-current` is `stats`), which a unit test cannot reliably observe. Two are from the second test review: no test that a done task's bad due date or priority is ignored under `--tag`, and no test of "first offending task by id" with two offenders in one field. One is from the second review, and is the first of those two again.

### The merge: an override

`stats` and `organize-edit` (part 3) were built from the same commit, `0f44eee`, so neither holds the other's change. Merging them, in a session on the published 0.5.1, made a commit, `c843610`, that no run covers. Git joined the two sets of changes without a conflict, and all 192 tests pass on the result. But plumbline's push gate lets a commit be pushed only if it has a pass record or an override record, and it refused this one. The session offered two ways out: run the pipeline on the merge, or make an override.

An override is a record that the user, not the pipeline, decided that a commit may be pushed, with the reason. The user typed `/plumbline:override` with the reason "merge of two separately passed branches (organize-edit and stats)". The record is `runs/pass/c8436101a7f4583088f836f791c899e4ea9dc5da.override.json`. It holds the commit, the reason, who made it, the time, and the stages that had not passed (none). It covers that one commit and nothing else, and it does not say the commit was reviewed. Only the user can make one: the model cannot start the command, and plumbline's hooks refuse any agent, and the main session, that tries to run it. Branch `latest` is this commit.

## What the records are

Every record is a file in a run's folder under `runs/`: `feature-due-dates/`, `fix-overdue-bad-date/`, `fix-overdue-non-string/`, `large-0-plan/` to `large-3-edit-remove/`, and `feature-stats/`. `runs/README.md` explains the folders and what was scrubbed before they were published.

**Spec** (`plan.json`). Written by the planner before any test or code exists. In the fix runs it was supplied. It holds the goal, the non-goals, the acceptance criteria with how to check each, the interfaces, a test plan and the risks. At size L it ends with a `split_proposal`: the changes the work should be cut into (see `large-0-plan/plan.json`). Everything after it is checked against it.

**Request** (`request.md`). The request the run began with, stored by plumbline so that the spec review can compare the spec with it. Its hash goes into the ledger before the file exists, so it cannot be edited unnoticed. Runs from 0.5.0 on have one. For the three parts of run 4 it is the request the session wrote from the plan's split.

**Spec review** (`spec-review.json`, and one file per agent in `spec-review/round-1/`). The review of the spec against the request, for sizes M and L. It has the shape of the review of the code, below: a prosecutor with the `requirements` lens files findings (`prosecutor-requirements.json`), and a screening defender gives a verdict on each (`screen-1.json`). There is no detective. A finding of this review goes back to the planner. Each finding names the line of `plan.json` it is about, and carries a quote. In run 5 the record also carries `target_sha256`, the hash of the `plan.json` it read, so that a later change to the plan makes the review stale.

**Tests record** (`tests.json`, and `test-review.json` in the size-M runs). Written by the test-writer. It lists each test by file and name, the criteria it covers and a one-line scenario. It also holds the stub check: did each new test fail, on an assertion, before the code existed? `test-review.json` is the review of those tests.

**Review record** (`review.json`, and one file per agent in `review/round-1/`). The prosecutors' files hold their findings. The defenders' files hold one verdict per finding: conceded, or refuted with a quote. The detective's file holds the gaps. `review.json` merges them. It lists the findings, the defenses, the findings that survived, who each goes to (the builder or the test-writer), how many are BLOCKING, and the gaps. From 0.5.0 a screening defender's file is `screen-1.json`. A review that runs again after a fix gets a new folder from 0.5.1 (`round-2/` in run 5). 0.5.0 wrote it over round 1.

**Verify record** (`verify.json`, and `junit-verify.xml`). The verifier ran the test command and the mechanical checks: secrets, symlinks, absolute home paths. The record holds the test counts, whether the run is green, and a hash of the change that was checked. plumbline also runs the test command itself at each gate, and keeps pytest's report: `junit-tests.xml` and `junit-verify.xml`.

**Ledger** (`ledger.jsonl`). The run's log. It is only appended to, one line per event: the intake, each agent's stop with the hash of the record it left, each review merge, each gate with the problems it found, each measured test run, and the final pass. This is how plumbline knows who wrote what. A record that no agent's line traces to fails its gate. From 0.5.0 the ledger also holds a `request` line (the hash of `request.md`) and a `leg` line each time a leg of the orchestrator ends, which names that leg's agent. A `leg` line is how plumbline counts what the orchestrator spent, apart from the stage agents.

**Pass record** (`reduce.json`, and a copy of it in `runs/pass/`). Written by the main session at the end. It lists every stage with its record, gate and rounds, the tokens each model used, and the verdict. plumbline's push gate lets a commit be pushed only if it has a pass record or an override. From 0.5.0 it also lists what the run left open: `open_findings`, the findings that survived the review and were not BLOCKING, and `gaps`, the detective's gaps. The review's own files stay in `.plumbline/`, which git ignores, so without this they would be lost with the working copy. `plumbline.py open` prints them. The tokens of the orchestrator's legs are counted apart, as `orchestration`. Run 4a has no pass record, because it made no commit.

**Override record** (`runs/pass/c8436101a7f4583088f836f791c899e4ea9dc5da.override.json`). What the user writes when a commit has no passing run and the user decides it may be pushed anyway. It holds the commit, the reason, who made it, the time, and `stages_skipped`. See "The merge" above.

**Intake and build** (`intake.json`, `build.json`). The intake record is the change class: file types, size, row and intent, and the commit the change is measured from. The build note is the builder's list of files changed, criteria addressed and assumptions.

## Try it yourself

You need Claude Code, `git`, `python3` 3.11 or newer, and [uv](https://docs.astral.sh/uv/), which the test command in `plumbline.toml` uses.

1. **Install ponytail and plumbline 0.5.1.** plumbline depends on [ponytail](https://github.com/DietrichGebert/ponytail), another Claude Code plugin. These are the commands from [plumbline's README](https://github.com/krajgh/plumbline):

   ```
   claude plugin marketplace add DietrichGebert/ponytail
   claude plugin marketplace add krajgh/plumbline
   claude plugin install plumbline@plumbline
   ```

   Do this before you open a session, because plugins load when a session starts. The first session may tell you to set `PONYTAIL_SUBAGENT_MATCHER`. plumbline's README says how. The runs above used 0.4.x, 0.5.0 and two dev copies, so a run of yours will differ in the details: the models vary, and the published 0.5.1 carries the fixes that the dev test in run 5 led to.

2. **Pick a request and a starting point.** Each request builds on the result of an earlier one, so each starts from a different branch. Here is one example each of a feature, a fix and a request of size L:

   | To try | Paste | Start from |
   | --- | --- | --- |
   | a feature, size M | run 1's request | `start` |
   | a fix, size S | run 3's request | `overdue-bad-date` |
   | a request of size L | run 4's request | `overdue-non-string` |

   `start` is the starting point: tasklist 0.1.0 adopted by plumbline, without the records. `main` has the same code plus `runs/` and this README, so an agent in a session on `main` could read the answers. Use `main` to read, not to try.

3. **Get the starting point.** For the feature, clone and check out `start`:

   ```
   git clone https://github.com/krajgh/plumbline-demo
   cd plumbline-demo
   git checkout start
   ```

   For a later point, that branch has to be the `main` of a remote of your own, because plumbline measures a change from the remote's default branch. A bare repository on your own machine will do. This is the fix; for the request of size L use `overdue-non-string` in place of `overdue-bad-date`:

   ```
   git clone --branch overdue-bad-date https://github.com/krajgh/plumbline-demo try-it
   cd try-it
   git checkout -b main
   git init --bare --initial-branch=main ../try-it-remote.git
   git remote set-url origin ../try-it-remote.git
   git push -u origin main
   ```

4. **Open a Claude Code session in that folder, in auto mode.** In the version of Claude Code used for these runs, agents could hand their reports back only in auto mode.

5. **Check the install.** Type `/plumbline:status`. It should say that plumbline is adopted and that no run exists yet.

6. **Type a line of your own, then paste a request.** For example, type `run this:` and paste a request. Claude Code asks before it acts on a message that is only pasted text, so the line of your own matters. You can also type `/plumbline:run` and paste only the request after it. The session may ask you to confirm the intent (feature or fix) and the size.

Two things to expect:

- The request of size L builds nothing. It ends with a plan, a spec review and a split, and asks what to do. Each part is then a run of its own, on its own branch, and it needs a `main` that holds the parts before it: after a part passes, fast-forward `main` to its branch and push it, then start the next part, in a fresh session if you like. The session gives you the line to start it with.
- A run may stop and ask you something: a change that measures bigger than its size, findings left open once every gate has passed (fix or ship), or a commit with no pass record. You decide, and your answers shape what a run costs.

## Licence

Apache License 2.0, the same as plumbline. See `LICENSE` and `NOTICE`.
