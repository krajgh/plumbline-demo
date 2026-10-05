# plumbline-demo

Two real runs of the [plumbline](https://github.com/krajgh/plumbline) pipeline for Claude Code, on a tiny to-do list program, with every record they wrote.

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

[plumbline](https://github.com/krajgh/plumbline) is a Claude Code plugin. It sends a change through a pipeline of subagents: plan, tests, build, verify and review. Each stage writes a typed JSON record. A mechanical gate checks that record before the next stage starts.

This repository has adopted plumbline: `plumbline.toml` is committed. It also holds the records of two real runs, a feature and a fix, made in the Claude Code desktop app on 2026-09-30. Two runs on one small program are two data points, not a benchmark.

| Branch | What it holds |
| --- | --- |
| `main` | The starting point, tasklist 0.1.0 adopted by plumbline (commit `ccffe51`), plus one commit that adds this README, the licence files and the records in `runs/`. |
| `start` | The starting point alone (commit `ccffe51`), without this README or the records. Use it to try a request yourself. |
| `due-dates` | The result of the feature run (commit `109e295`). |
| `overdue-bad-date` | The result of the fix run (commit `cf98e93`). It builds on `due-dates`. |

## The two requests

Both requests were pasted into a Claude Code session as they are written here.

In a review, prosecutors look for what is wrong. Each one files findings, and each finding carries a quote of the code and a case that fails. Defenders then try to refute each finding with a quote. A detective, who runs last, lists what is missing. Every finding has a severity:

- BLOCKING: it breaks a stated acceptance criterion, loses data, exposes a secret, or breaks the main path.
- MAJOR: wrong behaviour on a realistic path, with limited reach or a workaround.
- MINOR: an edge case, or an inconsistency.

Only a BLOCKING finding stops a run.

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

- About 18 minutes of active machine time: plan 1.4 min, tests 3.4 min (plus about 2 min to remove the stubs), test review 0.8 min, build 0.6 min, verify 1.2 min, review 4.7 min. The second session ran 46 minutes. About 30 of them went on waiting for the person at the keyboard. The test command takes under a second.
- The 15 agents wrote at least 42K output tokens, took in 416K fresh input tokens and read 2.7M tokens from the cache.
- The main session, which orchestrates the run, wrote 26K output tokens, wrote 114K tokens to the cache and read 5.3M from it.

Fresh input is input the model takes in anew: plain input, or input written to the prompt cache. A cache read is input served from the cache, which costs less. The agents' output counts are lower bounds, because some messages never recorded their final count. Agents run on small models. The main session runs on a larger one, and it is the biggest spender: it holds about two thirds of all the cache reads.

**Open items.** No finding was BLOCKING, so none had to be fixed. The number of tests stayed at 38 from the first measured run to the pass. The session asked whether to fix the findings first or ship as is, and the answer was ship as is. All 8 findings (some of them the same gap, found twice) and all 3 gaps were open when the run passed. The second run fixed the one bug behind `correctness-1` and `boundaries-1`. It touched nothing else on this list.

### Run 2: a fix

The request was pasted after a line of the person's own.

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

**Open items.** The run passed with 3 findings and 4 gaps open, on purpose. plumbline 0.4.2 does not carry them forward. The pass record lists none of them, and git ignores `.plumbline/`, so they stay in this run's `review.json` and nowhere else. The session reports them once, in its chat. Here they are.

The findings, all MINOR:

- `correctness-1`: a stored due date that is not a string, such as `null` or a number, makes `list --overdue` crash with a `TypeError` traceback, not the one-line error.
- `tests-1`: the test checks the task id with a bare `"1" in line`, so a wrong id, or any message that contains a 1, would pass.
- `tests-2`: no test covers a done task with a malformed due date, or a file with several tasks.

The prosecutor rated the crash MINOR. But the finding names AC-1 as its rule, and two of the three defenders wrote that the crash fails AC-1. A broken acceptance criterion is BLOCKING by the rubric above. A defense record has no field for severity, so the gate never saw this.

The detective's gaps:

- A well-formed but impossible stored date such as `2026-02-30`, and an empty string, are not tested.
- No test shows that a done task's bad date is ignored, or that a file with several tasks names the right id.
- The non-string crash above.
- With several malformed tasks, the first one in file order is named, not the lowest id, and no test pins that. No test combines an invalid `TASKLIST_TODAY` with a malformed stored date either.

## What the records are

Every record is a JSON file in `runs/feature-due-dates/` or `runs/fix-overdue-bad-date/`. `runs/README.md` explains the folders and what was scrubbed before they were published.

**Spec** (`plan.json`). Written by the planner before any test or code exists. In the fix run it was supplied. It holds the goal, the non-goals, the acceptance criteria with how to check each, the interfaces, a test plan and the risks. Everything after it is checked against it.

**Tests record** (`tests.json`, and `test-review.json` in the feature run). Written by the test-writer. It lists each test by file and name, the criteria it covers and a one-line scenario. It also holds the stub check: did each new test fail, on an assertion, before the code existed? `test-review.json` is the review of those tests.

**Review record** (`review.json`, and one file per agent in `review/round-1/`). The prosecutors' files hold their findings. The defenders' files hold one verdict per finding: conceded, or refuted with a quote. The detective's file holds the gaps. `review.json` merges them. It lists the findings, the defenses, the findings that survived, who each goes to (the builder or the test-writer), how many are BLOCKING, and the gaps.

**Verify record** (`verify.json`, and `junit-verify.xml`). The verifier ran the test command and the mechanical checks: secrets, symlinks, absolute home paths. The record holds the test counts, whether the run is green, and a hash of the change that was checked. plumbline also runs the test command itself at each gate, and keeps pytest's report: `junit-tests.xml` and `junit-verify.xml`.

**Ledger** (`ledger.jsonl`). The run's log. It is only appended to, one line per event: the intake, each agent's stop with the hash of the record it left, each review merge, each gate with the problems it found, each measured test run, and the final pass. This is how plumbline knows who wrote what. A record that no agent's line traces to fails its gate.

**Pass record** (`reduce.json`, and a copy of it in `runs/pass/`). Written by the main session at the end. It lists every stage with its record, gate and rounds, the tokens each model used, and the verdict. plumbline's push gate lets a commit be pushed only if it has a pass record or an override.

**Intake and build** (`intake.json`, `build.json`). The intake record is the change class: file types, size, row and intent, and the commit the change is measured from. The build note is the builder's list of files changed, criteria addressed and assumptions.

## Try it yourself

You need Claude Code, `git`, `python3` 3.11 or newer, and [uv](https://docs.astral.sh/uv/), which the test command in `plumbline.toml` uses.

1. **Install ponytail and plumbline.** plumbline depends on [ponytail](https://github.com/DietrichGebert/ponytail), another Claude Code plugin. These are the commands from [plumbline's README](https://github.com/krajgh/plumbline):

   ```
   claude plugin marketplace add DietrichGebert/ponytail
   claude plugin marketplace add krajgh/plumbline
   claude plugin install plumbline@plumbline
   ```

   Do this before you open a session, because plugins load when a session starts. The first session may tell you to set `PONYTAIL_SUBAGENT_MATCHER`. plumbline's README says how.

2. **Clone this repository and check out `start`.** It is where both runs began, without the records, so an agent can't copy the answers from `runs/`.

   ```
   git clone https://github.com/krajgh/plumbline-demo
   cd plumbline-demo
   git checkout start
   ```

3. **Open a Claude Code session in that folder, in auto mode.** In the version of Claude Code used for these runs, agents could hand their reports back only in auto mode.

4. **Check the install.** Type `/plumbline:status`. It should say that plumbline is adopted and that no run exists yet.

5. **Type a line of your own, then paste a request.** For example, type `run this:` and paste a request. Claude Code asks before it acts on a message that is only pasted text, so the line of your own matters. You can also type `/plumbline:run` and paste only the request after it. The session may ask you to confirm the intent (feature or fix) and the size (S or M).

Two cautions:

- `main` holds the answers to the two requests in `runs/`, and an agent that reads them could copy them. That's why you try from `start`.
- The second request builds on the result of the first. To try it, put `due-dates` on a `main` of your own and push that to a remote of your own first. plumbline measures a change from the remote's default branch.

## Licence

Apache License 2.0, the same as plumbline. See `LICENSE` and `NOTICE`.
