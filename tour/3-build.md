# Part 3: Build Existing Cards

In this part she builds two real cards with `/card`, reviews each pull request, asks for changes, and merges.
HVD-26 comes first because it is small, so her first loop is fast. HVD-25 follows and is bigger.

Run this part in the same `colo` session as Part 2. If she is resuming in a new session, she starts it with `colo`
in `~/code/health-value-dashboard`.

Links used in this part:

- Jira backlog: https://taylorantoniohardin.atlassian.net/jira/software/projects/HVD/boards/8/backlog
- Jira board: https://taylorantoniohardin.atlassian.net/jira/software/projects/HVD/boards/8
- Pull requests: https://github.com/tahardi/health-value-dashboard/pulls
- Release runs: https://github.com/tahardi/health-value-dashboard/actions/workflows/release.yml

## Step 1: Into the sprint

Open the Jira backlog for her. She does this step herself in Jira. Do not move or assign the cards with `jira.py`;
the point is that she does it with her own hands.

Tell her:

> A sprint is the box of work the team has committed to doing now. The board only shows cards in the active
> sprint, so moving a card into the sprint is how work becomes "now".

If the backlog shows no active sprint to drag cards into, create and start one yourself, without asking her or
Taylor. Run this, which reads her Jira login from the file and never prints it:

```bash
set -a && . ~/.config/jira/env && set +a
site="https://${JIRA_SITE#https://}"
id=$(curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\": \"HVD Sprint\", \"originBoardId\": 8, \"startDate\": \"$(date -u +%FT%TZ)\",
  \"endDate\": \"$(date -u -v+14d +%FT%TZ)\"}" "$site/rest/agile/1.0/sprint" | jq .id)
curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" -H "Content-Type: application/json" \
  -d '{"state": "active"}' "$site/rest/agile/1.0/sprint/$id" | jq .state
```

It prints `"active"` when the sprint has started. Reload the backlog page for her and tell her:

> There was no active sprint, so I started a two-week one for you.

If it prints anything else, follow "When something breaks" in `TOUR.md`.

Walk her through it:

1. Above the backlog list, click the "Label" filter and pick `demo`.
2. Drag HVD-26 from the backlog up into the active sprint. Do the same for HVD-25.
3. Click HVD-26 to open it. In the "Assignee" field, click "Assign to me". Do the same for HVD-25.

Then check her work: run `python3 ~/.claude/skills/card/scripts/jira.py get HVD-26` and the same for HVD-25, and
confirm each shows her as the assignee. If not, point out which card still needs it.

## Step 2: Intro to `/card`

Tell her:

> /card is a command that builds one Jira card for you. It reads the card, moves it to In Progress in Jira, makes a
> branch in its own folder, writes the tests first, writes the code, runs the checks, and opens a pull request.
> Then it stops and waits for your review. It never merges until you say so.

Define these two terms in one sentence each: a pull request (PR) is a request to merge a branch into `main`, where
the changes can be read, discussed, and checked first; a check is an automatic test GitHub runs on every PR.

## Step 3: Read HVD-26 together

Run `python3 ~/.claude/skills/card/scripts/jira.py get HVD-26` and show her the output. Point out, briefly:

- The "Files" list: only three files change, plus new R answer files.
- The steps: step 1 writes a test and runs it to see it fail, before any code changes. Explain "test first" in one
  sentence: the failing test proves the test can catch the problem, and passing it proves the change works.
- The acceptance criteria: the tests that must pass for the card to count as done.

Tell her:

> The point of this card is how small it is. Small cards are fast to build and easy to review.

## Step 4: Run it

Open the Jira board for her and tell her to place the browser window beside Terminal so she can watch the card
move.

Run `pwd` first; if it is not `~/code/health-value-dashboard`, give her the `cd ~/code/health-value-dashboard`
command. Then tell her to type this in this Claude window:

```text
/card HVD-26
```

Tell her:

> This takes about 10 to 20 minutes. Claude will stop and ring a bell when the pull request is ready. You can watch
> the card move from To Do to In Progress to In Review on the board.

While `/card` runs, narrate only the big moments in one line each: the card moving to In Progress, the new folder
under `~/code/wts/`, the first failing test, the test passing, `make pre-pr`, the PR opening, and CI starting. If
`make reference` fails, `/card` follows "When make reference fails locally" in the repo's `CLAUDE.md`. Explain what
she is watching:

> Part of the checks runs R to make sure the Python numbers match. That part does not always work on a Mac, so
> Claude skips it here and lets GitHub run it on Linux. If GitHub's copy of R gives new answer files, Claude
> downloads them, commits them, and pushes again. You'll see the checks go green on that second push.

At the end, `/card` reads the PR's comments once and reports that the PR is waiting for review. That is expected,
not a failure: there are no comments yet.

## Step 5: Review the PR

Open the PR for her (the URL `/card` printed). Tell her to click the "Files changed" tab first and read the
changes; point out the test change and the one line added in `app/schema.py`. Then tell her to click the "Checks"
tab and confirm every check has a green tick.

If the `reference` check failed, `/card` already followed the repo's fallback; tell her what happened in one
sentence and show her the second push's green checks.

## Step 6: See it

This step is the one exception to the `pwd` rule in `TOUR.md`. Run `make run` in the background from the card's
worktree (the folder under `~/code/wts/` that `/card` made), not
from `~/code/health-value-dashboard`, then open http://localhost:8000 for her. Tell her:

> This is the app running from the PR's folder, so you see the change before it is merged into main.

She opens the "Rate measure" dropdown on the Value tab and finds "Discharged home". When she says she has finished
looking, stop the background `make run`.

## Step 7: Scripted feedback

Tell her she now asks for a change, the way a reviewer would. She leaves an inline comment, meaning a comment on
one line of the code.

Walk her through it:

1. On the PR, click the "Files changed" tab.
2. Find the line in `app/schema.py` that adds the "Discharged home" column.
3. Hover over the line. Click the blue + that appears at its left edge.
4. Type exactly this comment:

   > Can we label this "Discharged to home"? That's how our team says it.

5. Click "Add single comment". If she clicked "Start a review" instead, the comment stays pending and `/card`
   cannot see it; tell her to click "Finish your review", then "Submit review".

Before she reruns `/card`, tell her:

> Tip: in this Claude window, press the up arrow key to bring back a command you typed before, then press Return.
> That saves retyping /card HVD-26 each time.

Then she types this in this Claude window:

```text
/card HVD-26
```

When it finishes, open the PR and show her: Claude replied in her comment thread, pushed a fix, and marked the
thread resolved. Tell her:

> Review is a conversation. You ask, Claude answers and fixes, and the checks run again on the new code.

## Step 8: Approve and merge

Tell her to go to the PR's "Conversation" tab, scroll to the comment box at the bottom, type `LGTM`, and click
"Comment". Tell her:

> LGTM means "looks good to me". It is a normal comment, not GitHub's Approve button, because GitHub won't let you
> approve your own pull request. /card treats your LGTM as the approval.

Then she presses the up arrow and Return to run this in this Claude window:

```text
/card HVD-26
```

When it finishes, show her: the PR says "Merged", the branch and the worktree folder are gone, and HVD-26 is in the
Done column on the board. Run `git pull` in `~/code/health-value-dashboard` so her main copy has the change.

## Step 9: HVD-25, same loop, bigger

Tell her:

> HVD-25 adds a whole new Surgeons tab, so it is a bigger card. Claude may take 30 to 60 minutes. You can walk away
> until the bell rings. Keep the laptop lid open, because closing it pauses Claude.

Repeat steps 3 to 6 for HVD-25: read the card with her, she types `/card HVD-25`, she reviews the PR, and you run
the app from its worktree so she can see the Surgeons tab and its funnel plot. Explain the funnel plot in one
sentence: each dot is a surgeon, and dots outside the curved lines have a rate unusually far from the average for
how many cases they did.

Then she leaves two comments.

First, an inline question. On "Files changed", she hovers the line in `app/stats.py` that sets the funnel limits,
clicks the blue +, types exactly this, and clicks "Add single comment":

> How do we know these limits match what R would give?

Second, a top-level comment, meaning a comment on the whole PR instead of one line. On the "Conversation" tab, in
the comment box at the bottom, she types exactly this and clicks "Comment":

> Please label the dashed and dotted lines as 95% and 99.8% limits in the legend.

She presses the up arrow, edits the command to `/card HVD-25` if needed, and presses Return. When it finishes:

- Show her Claude's reply to her question. It points to the golden test, which checks the Python limits against
  R's answer files. Tell her:

> Questions are feedback too. A good answer points to proof, like a test, not just "trust me".

- Run the app from the worktree again and show her the legend now labels the 95% and 99.8% limits. Stop it when
  she has finished looking.

Then she comments `LGTM` on the "Conversation" tab and reruns `/card HVD-25`. When it merges, run `git pull` in
`~/code/health-value-dashboard`, run `make run` there in the background, and open http://localhost:8000. Show her
"Discharged to home" in the Surgeons tab's Rate measure dropdown. Tell her:

> HVD-26 added that measure before the Surgeons tab existed, and the new tab picked it up with no extra work.
> That's what building on a clean main looks like.

Stop the background `make run` when she has finished looking.

## Step 10: Published

Open the Release runs page for her. Tell her:

> Every merge to main starts a Release run that builds the app image and saves it to GitHub. It can take up to
> about 30 minutes, mostly building the Apple Silicon version. The HVD-26 release already ran while Claude built
> HVD-25, so we only wait for the HVD-25 one.

Run `gh run list --workflow release.yml --branch main --limit 2` and check the newest run every few minutes with
`gh run watch <run-id>` in the background. When it succeeds, run `make docker-run-registry` in the background and
open http://localhost:8000. Show her both features: "Discharged to home" in the dropdowns and the Surgeons tab with
its labeled legend. Stop it when she has finished looking.

If the Release run fails, follow "When something breaks" in `TOUR.md`.

Recap the part, then tell her this is a natural place to stop, and she can resume later with "continue the tour".
