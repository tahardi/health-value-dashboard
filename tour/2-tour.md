# Part 2: Tour

In this part she follows one real, finished card from plan to running image: HVD-17 (Publish Image on Merge), and
its two pull requests, #10 and #12. She reads and clicks; you open pages and run commands. Nothing in this part
changes the repo.

Only step 13 needs Docker. If Docker is broken, do steps 1 to 12 and 14, and record step 13 under `## Problems`.

Before step 1, say:

> Part 2 is a tour. We'll follow one finished card, HVD-17, from the plan all the way to a running app. You'll
> mostly read and click. Say "next" when you're ready for each step.

## Steps

1. **The big picture.** Show her this diagram in a code block, exactly as written:

   ```text
   requirements -> design -> plan -> cards -> branch -> pull request -> checks + review -> merge to main
                                                                                                 |
                                                                        deploy <- publish image <-+
   ```

   Then walk the stages in one sentence each:

   - Requirements: what the app must do, and for whom.
   - Design: how it will work, and why those choices were made.
   - Plan: the design broken into small tasks.
   - Cards: one task each, tracked in Jira (a website that tracks work as cards on a board).
   - Branch: a private copy of the code where one card's work happens.
   - Pull request (PR): a request to merge a branch into `main`, the shared copy everyone builds on. People
     review it there.
   - Checks: tests GitHub runs automatically on every PR.
   - Merge: the branch's changes join `main`.
   - Publish image: GitHub packages the app so any computer can run it.
   - Deploy: a server runs that package for users.

   Then say:

   > Each stage makes the next one easy and repeatable. Claude does most of the typing; you make the decisions
   > at each stage.

2. **Requirements and design.** Run
   `open https://github.com/tahardi/health-value-dashboard/blob/main/docs/design.md`. Point out, in order:

   - "Purpose" and "Success Criteria": the requirements. What the app is for, and how we know it works.
   - "Scope": what is built now, what is left as cards for a learner, and what is out of scope (a database,
     logins, real data). Saying what you will not build is as important as saying what you will.
   - The upload rule in "Success Criteria": a new data file uploaded on the Data tab updates every open
     dashboard, and a file with wrong columns is rejected with a plain message while the current data stays.
     That is a constraint (a rule every later decision must respect).
   - "Statistics and R Validation": every number the app shows is checked by a test against answers computed
     in R, a statistics language. So a Python mistake fails a test instead of reaching a doctor.

   Then say:

   > A design records why things are the way they are, so later work doesn't re-argue it.

3. **Plan.** Run `open https://github.com/tahardi/health-value-dashboard/blob/main/docs/plan.md`. Ask her to
   scroll to "Card Map". Explain:

   - Each `## Epic:` section in the plan became an epic in Jira. An epic is a group of related cards, such as
     "Delivery".
   - Each task in the table became one card. "T-R2 Publish Image on Merge" became HVD-17, the card we follow
     today.
   - "Blocked by" means a card cannot start until another card is done.

4. **Jira backlog.** Run
   `open "https://taylorantoniohardin.atlassian.net/jira/software/projects/HVD/boards/8/backlog?epics=visible"`.
   The `?epics=visible` at the end turns on the epics panel, which Jira hides by default. If Jira asks her to log
   in, she uses the email her Jira invitation went to.

   Explain what she sees:

   - The sprint at the top: a two-week box of work the team has committed to finishing.
   - The backlog below it: every other card, waiting to be picked.
   - The epics panel on the left.

   Then say:

   > Click the "Delivery" epic in the epics panel. The list now shows only that epic's cards. Find HVD-17. Click
   > the epic again to clear the filter.

5. **HVD-17 up close.** Run `open https://taylorantoniohardin.atlassian.net/browse/HVD-17`. Point out, in order:

   - The description: the files to change and numbered steps, detailed enough that Claude can build it alone.
   - The acceptance criteria at the bottom: how we know it is done. On newer cards these are named tests.
   - Story points: 2. Points estimate how much effort the reviewer spends checking the work, not hours spent
     building it. The scale is 1, 2, 3, 5, 8.
   - Labels: HVD-17 has none. Other cards use `demo` (part of this tour), `parallelizable` (can be built at the
     same time as other cards), `needs-taylor` (only Taylor can do it), and `needs-refinement` (not detailed
     yet).
   - Links: "is blocked by HVD-16" and "blocks HVD-27". Claude will not start a card while its blockers are
     unfinished.
   - Comments, under "Activity": Claude posted a link to each PR, what changed in review, and "Merged" when done.

6. **The board.** Run `open https://taylorantoniohardin.atlassian.net/jira/software/projects/HVD/boards/8`.
   Explain the columns: To Do, In Progress, In Review (a PR is waiting for review), Done. Then say:

   > You won't drag cards between these columns yourself. When you run /card in Part 3, it moves the card for
   > you as the work progresses.

7. **Branches and worktrees.** Run `git log --oneline -10` in `~/code/health-value-dashboard` and show her the
   output. Explain:

   - Each line is one change merged into `main`. Most lines start with a card number in brackets. The two
     `[HVD-17]` lines are the PRs we follow today.
   - A branch is a private copy of the code for one card. Work happens there, so `main` stays untouched until
     the work is reviewed and its checks pass.
   - A worktree is a separate folder holding one branch. Several cards can be worked on at once, each in its own
     folder, without touching each other or her main copy in `~/code/health-value-dashboard`.

   Then say:

   > Your rule, which your Claude setup now follows: every card gets its own worktree folder under ~/code/wts/,
   > named for the repo, the card, and a short description, like
   > ~/code/wts/health-value-dashboard-hvd-26-discharged-home. Nobody changes main directly. You'll see these
   > folders appear in Part 3, and run several at once in Part 4.

8. **PR #10, then PR #12.** Run `open https://github.com/tahardi/health-value-dashboard/pull/10`. Walk her
   through the tabs:

   - "Conversation": the summary Claude wrote, then the review. Taylor asked to rename two make commands so it is
     clear which runs the local copy and which runs the published one. Claude replied with the fix and the
     commit. Taylor wrote "LGTM" ("looks good to me"), a plain comment meaning the work is ready, and it merged.
   - "Files changed": every line added in green and removed in red. Reviewers comment on single lines here.
   - "Checks": the automatic tests, all passed.

   Then run `open https://github.com/tahardi/health-value-dashboard/pull/12` and tell the story:

   - After #10 merged, the release job on `main` failed. It could not build the app for Apple Silicon Macs like
     hers.
   - PR #12 fixed that. In review, Taylor also asked to make the checks stricter and split them into one job per
     check, so a failure shows exactly what broke.
   - Ask her to read the review threads on `.github/workflows/ci.yml`, including the one where Taylor asks
     whether Apple Silicon support is needed at all and Claude explains why it is.

   Then say:

   > Feedback is a conversation, not a verdict. And when a bug reaches main, it gets fixed the same way as
   > everything else: a card, a branch, a PR, review, merge.

9. **Main is gated.** Run `gh api repos/tahardi/health-value-dashboard/rulesets` to find the ruleset's `id`,
   then `gh api repos/tahardi/health-value-dashboard/rulesets/<id>` with that number. Do not show her the raw
   output. Explain what it says in plain words. A ruleset is a set of rules GitHub enforces on a branch.

   - This ruleset, "Protect main", applies to `main`.
   - Changes reach `main` only through a PR. Nobody can push to it directly, delete it, or undo past changes.
   - A status check is a test GitHub runs that must pass. Under "required status checks" are five names:
     `lint`, `test`, `data`, `reference`, and `docker-build`. These are the checks GitHub runs on every PR.
     The merge button stays locked until all five pass.
     - `lint`: the code is formatted and free of common mistakes.
     - `test`: every test passes.
     - `data`: the sample data file is up to date.
     - `reference`: the R answers the tests compare against are up to date.
     - `docker-build`: the app still packages into an image.

   Then say:

   > Because nothing reaches main without passing every check, main always works. That matters because main is
   > the code that gets published and deployed.

10. **The CI workflow file.** Run
    `open https://github.com/tahardi/health-value-dashboard/blob/main/.github/workflows/ci.yml`. CI (continuous
    integration) means running the checks automatically on every change. Explain:

    - A workflow is a file of instructions GitHub follows automatically. `on:` says when: `pull_request` means
      on every PR, and `push` to `main` means again after every merge.
    - Each block under `jobs:` is one job: one of the five checks from step 9.
    - `runs-on: ubuntu-latest` means each job gets a fresh Linux computer, so it does not matter what is
      installed on anyone's laptop.
    - Most `run:` lines are the same `make` commands as `make pre-pr`, which Claude runs on her Mac before every
      PR. The `git diff` lines fail the job if a command changed a saved file, such as an out-of-date data file.
    - `uses:` lines borrow ready-made steps, such as copying the code onto the fresh computer.

11. **Actions tab.** Run `open https://github.com/tahardi/health-value-dashboard/actions/runs/39033867390`. This
    is the CI run on PR #12's final version. Then say:

    > If you don't see a list of jobs on the left, click "Summary" first. Click the "test" job on the left, then
    > click the "make test" step to expand it. Scroll to the bottom.

    Explain: GitHub started a fresh computer, installed everything, and ran every test. The last line shows how
    many passed. A green check means all of them did.

12. **The release workflow.** Open these one at a time. After each, wait for her to say "next" before opening
    the next one:

    1. Run `open https://github.com/tahardi/health-value-dashboard/blob/main/.github/workflows/release.yml`.
       Explain: `on: push: branches: main` means it runs on every merge to `main`. It builds the app image
       (a package holding the app and everything it needs to run) for both regular PCs (`linux/amd64`) and
       Apple Silicon Macs (`linux/arm64`), then saves it to GitHub's registry (a storage place for images).
    2. Run `open https://github.com/tahardi/health-value-dashboard/actions/runs/39032787393`. This is the
       release run after PR #10, failed with a red X: the Apple Silicon build broke.
    3. Run `open https://github.com/tahardi/health-value-dashboard/actions/runs/39034188510`. This is the
       release run after PR #12, green.
    4. Run `open https://github.com/tahardi/health-value-dashboard/pkgs/container/health-value-dashboard`. This
       is the package page: every merge to `main` adds a new image here, and `latest` always points to the
       newest one.

13. **The payoff.** Run `docker info`. If it fails, apply the Docker fix from "Known fixes" in `TOUR.md`. Then
    say:

    > Now we'll run the exact app image GitHub built, without building anything on your laptop. The first
    > download can take a few minutes.

    Run `make docker-run-registry` in the background and wait until its output shows the app is listening on
    port 8000. Then run `open http://localhost:8000` and say:

    > This is the app GitHub built and published after the last merge. A hosting service does the same thing:
    > it pulls this image and runs it. That's how code goes live without anyone building it by hand.

    When she says she has finished looking, stop the background task. If `make docker-run-registry` fails, follow
    "When something breaks" in `TOUR.md` and go on to step 14.

14. **Recap and checkpoint.** Recap Part 2 in two or three sentences: one card went from plan, to Jira, to a
    branch and PR, through review and checks, to merge, to a published image she just ran. This is the end of
    the first sitting. Say:

    > That's Part 2. This is a good place to stop. When you come back, open Terminal, run
    > cd ~/code/health-value-dashboard and then colo, and type "continue the tour". Or say "next" to start
    > Part 3, where you build two cards yourself.
