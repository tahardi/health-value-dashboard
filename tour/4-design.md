# Part 4: Design and Build HVD-28

In this part she designs a feature, turns it into cards, and builds them in parallel. The feature is fixed: Jira
card HVD-28, the Procedures tab. It is not her choice, so these steps can be specific.

Steps 2 to 7 run on Opus. Step 8 switches back to Sonnet. If she resumes in a new session and the next step is
2 to 7, have her type `/model opus` in the Claude window first. In every `jira.py` command below, `jira.py` means
`python3 ~/.claude/skills/card/scripts/jira.py`.

Steps 8 to 11 repeat once per card. Mark them done together once every new card is Done. Until then, keep a
`Part 4 cards in flight: <keys>` line under `## Problems`, so a resumed session knows which cards are left.

## Steps

1. **New session.** This step runs in the Part 3 session. Mark it done in the progress file first, so the new
   session starts at step 2. Then say:

   > Part 4 starts in a fresh Claude session, so it begins with a clean slate. Press Cmd+T to open a new Terminal
   > tab, and type these two commands there, one at a time:

   ```sh
   cd ~/code/health-value-dashboard
   colo
   ```

   > Once Claude starts in the new tab, type this in that Claude window:

   ```text
   /model opus
   ```

   > Then type "Read TOUR.md and continue the tour." in the new tab. Opus thinks more carefully than Sonnet, so
   > we use it to design the feature and plan the work. Sonnet builds it later. You can close this old tab by
   > typing /exit here.

2. **Requirements.** Run `jira.py get HVD-28` and show her the stub: a short note saying what the tab should do,
   labeled `needs-refinement`, meaning it is not detailed enough to build yet. Say:

   > Before anyone designs anything, we pin down what the feature is for. I'll ask you questions one at a time.
   > There are no wrong answers. Your answers become the requirements.

   Use the superpowers brainstorming skill to interview her, one question at a time. Cover at least: who uses the
   tab, what decision it helps them make, and what is out of scope. Keep the questions plain; she is not expected
   to know the code.

3. **Design.** Write the design to `docs/designs/procedures-tab.md` in `~/code/health-value-dashboard`. Use that
   path, not the brainstorming skill's default folder. Never run `git add` or `git commit` on it here, even if
   the skill says to: this folder is on `main`, and step 6 moves the file to its own branch before committing.
   Open it for her on screen with `open -e docs/designs/procedures-tab.md`. Say:

   > This is the design: what we're building and why. Read it and tell me anything that's wrong or missing. I'll
   > revise it until you say it's right.

   Revise until she approves it.

4. **Plan.** Write the plan to `docs/designs/procedures-tab-plan.md`. Use that path, not the planning skill's
   default folder. Never run `git add` or `git commit` on it here, and stop once the plan is written: the next
   step turns it into cards, not code. The plan breaks the work into tasks, each with test-first steps. Any new
   or changed statistic gets an R check, as the repo's `CLAUDE.md` requires. Open it with
   `open -e docs/designs/procedures-tab-plan.md` and say:

   > The plan breaks the design into small tasks, each one a future card. Each task says which tests to write
   > first. Tell me if anything looks off.

5. **Cards.** Read "Planning work" in her `~/.claude/CLAUDE.md` and turn the plan into cards following it. Split
   the work so at least two cards can run at once.

   - Write each card's description to a markdown file in a temporary folder outside the repo (make one with
     `mktemp -d`).
   - Run `jira.py edit HVD-28` with `--summary`, `--description-file`, `--points`, and `--labels` to turn the stub
     into the first card. Pass the new labels in full, since `--labels` replaces the old ones, so
     `needs-refinement` goes away.
   - Run `jira.py create HVD <summary> --description-file <file> --parent HVD-7` with `--points` and `--labels` for
     each other card. HVD-7 is the Demo epic.
   - Run `jira.py link <blocker> <blocked>` for every card that must wait on another.

   Open the board with `open https://taylorantoniohardin.atlassian.net/jira/software/projects/HVD/boards` and
   say:

   > These are your new cards. Open each one and check it against this list:
   >
   > - Can I tell what done looks like?
   > - Are the acceptance criteria tests?
   > - Do the points match how much review I would do?
   > - Do the blockers make sense?
   >
   > Then pick one card and ask me this, word for word: "Is this the complete set of cases worth testing, or are
   > there other useful properties to check?"

   When she asks, answer it, add any new cases to that card with `jira.py edit <key> --description-file <file>`,
   and tell her to refresh the card in Jira to see them appear. Fix anything else she finds the same way.

6. **Design PR.** Designs get reviewed too. Run this as one command from `~/code/health-value-dashboard`:

   ```sh
   wt=~/code/wts/health-value-dashboard-procedures-tab-design
   git fetch origin
   git worktree add $wt -b procedures-tab-design origin/main
   mkdir -p $wt/docs/designs
   mv docs/designs/procedures-tab.md docs/designs/procedures-tab-plan.md $wt/docs/designs/
   ```

   The branch has no card key, because HVD-28 is now a build card that `/card` gives its own branch. In the
   worktree, commit both files, push the branch, and open a PR titled `Procedures Tab Design` with `gh pr create`.
   Fill in the PR template. Open the PR with `gh pr view <number> --web` and say:

   > This pull request holds the design and the plan. Read them in "Files changed". If they look right, go to the
   > "Conversation" tab and leave a comment that says LGTM, which means "looks good to me". Tell me here when
   > you're done.

   When she says she is done, check her comment with `gh pr view <number> --json comments`. Wait for every check
   in `gh pr checks <number>` to pass. Then, from `~/code/health-value-dashboard`, run
   `git worktree remove ~/code/wts/health-value-dashboard-procedures-tab-design`, then
   `gh pr merge <number> --squash --delete-branch`, then `git pull`.

7. **Sprint planning.** Say:

   > Next, we pick which cards go into this sprint. Type this in this Claude window:

   ```text
   Plan my sprint.
   ```

   Explain in one sentence that points measure how much reviewing a card needs. Ask her how many points she can
   review this sprint. Then propose the new cards whose blockers will be done, ordered by blockers, within that
   number, and explain the choice with their points and blockers. Once she agrees, run
   `jira.py sprint <key> <key>...` with the cards she agreed to, then `jira.py assign <key>` for each one. Open the
   board so she sees them. If `jira.py sprint` reports `no active sprint`, record it under `## Problems`, draft the
   text to Taylor, and go on to step 8 without the sprint.

8. **Build in parallel.** Say:

   > Building runs on Sonnet. Type this in this Claude window:

   ```text
   /model sonnet
   ```

   Then pick the cards that can start now, with no open blockers, at most two. For each one, say:

   > Press Cmd+T to open a new Terminal tab, and type these two commands there, one at a time:

   ```sh
   cd ~/code/health-value-dashboard
   colo --model sonnet
   ```

   > Wait until Claude starts in that tab, then type this in that Claude window:

   ```text
   /card HVD-X
   ```

   Fill in the real card key for `HVD-X`. Say:

   > Each card works in its own folder, called a worktree, so the two Claudes never touch each other's files. You
   > can watch both cards move on the board. Each tab rings a bell when it finishes or needs you. When a card's
   > pull request is open, come back to this tab and tell me, for example "HVD-X is ready".

   If one of the new cards is blocked by another, have her type `/card` with that card's key in this Claude
   window. It refuses and lists the open blockers. Say:

   > The card refused because it depends on work that isn't merged yet. Building it now would mean building on
   > code that might still change.

   If no card is blocked, skip that part and say so.

9. **Review on her own.** No scripted comments this time. When she says a card is ready, find its PR with
   `gh pr list`, open it with `open <url>`, and say:

   > This time you review on your own. Go through this list:
   >
   > - Does it match the card?
   > - Are the tests meaningful?
   > - Is this the complete set of cases worth testing, or are there other useful properties to check?
   > - Does it look right in the app?
   >
   > Leave any feedback as comments on the pull request. Then go to that card's tab, press the up arrow, and
   > press Return to run the same /card command again. Claude will answer your comments and push fixes.

   To check the app, find the card's worktree with `git worktree list`, run `make run` in the background from
   there, as Part 3 did, and open http://localhost:8000.

10. **Merge one at a time.** Say:

    > Merge one pull request at a time. Pick one, comment LGTM on it, and rerun its /card command in its tab.
    > Don't comment LGTM on the second one yet.

    Once the first is merged, say:

    > Now rerun /card in the second tab. The second branch was made before the first one merged, so it doesn't
    > have that work yet. Claude merges main into it and the checks run again on the combined code. That way main
    > only ever gets code that was tested together. When the checks pass, comment LGTM and rerun /card to merge it.

11. **Remaining cards.** Any card that was blocked can start once all its blockers are Done. Have her type `/exit`
    in a finished build tab and close it, then start the card in a new tab with the same commands as step 8. At
    most two build tabs run at once. Repeat steps 9 and 10 for it. Continue until every new card is Done.

12. **Published.** After the last merge, open the Actions page with
    `open https://github.com/tahardi/health-value-dashboard/actions`. Find the newest Release run with
    `gh run list --workflow release.yml --branch main --limit 1`, and run `gh run watch <id>` in the background
    until it finishes (up to about 30 minutes). Then run `make docker-run-registry` in the background from
    `~/code/health-value-dashboard` and open http://localhost:8000. Say:

    > This is your feature running from the image GitHub built. Nobody built it by hand.

    Stop it once she has finished looking.

13. **Wrap-up.** Recap the lifecycle against what she did: requirements, design, and plan in steps 2 to 4, cards
    in step 5, branches and pull requests in step 8, review and checks in steps 9 and 10, publishing in step 12.
    Then say:

    > The same loop works on your own app. Your Claude setup lives in your home folder, not in this repo, so in
    > any project you can ask Claude to design a feature with you, turn it into cards, and run /card on each one.

    Ask her what was confusing during the tour. Then draft the text to Taylor with her answer filled in, in a code
    block she can copy:

    ```text
    HVD tour done! What was confusing: <her answer>.
    ```

    Mark the tour finished in the progress file.
