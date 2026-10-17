---
name: card
description: Use when the user runs /card with a Jira card key (e.g. /card VD-12) to implement that card end to end
argument-hint: <JIRA-KEY> [force]
disable-model-invocation: true
---

# Implement a Jira Card

Implement the card named in the arguments, get it green locally and in CI, and leave a PR for the user to review. On later runs, address the user's PR comments. The card is the spec. You merge only after the user approves the PR (see "Review Round").

**Arguments:** `$ARGUMENTS`. The first word is the card key (`[A-Z]+-\d+`). If the second word is `force`, skip the blocker check.

**Jira helper:** `python3 ~/.claude/skills/card/scripts/jira.py` with `get KEY`, `transition KEY STATUS`, `comment KEY TEXT`, `assign KEY`, or `strike-blockers KEY`. It reads credentials from `~/.config/jira/env`. Never print or echo that file.

## Precedence

1. The user's CLAUDE.md rules (worktrees, PR title format, no comments, test style).
2. The card: files, names, types, steps, commands, and acceptance criteria.
3. Your own defaults.

If rules 1 and 2 conflict, stop and ask the user.

## Workflow

1. **Read the card.** Run `jira.py get KEY` and read all of it. If the card is `In Review` and has an open PR, skip to "Review Round".
2. **Check blockers.** If any "Blocked by" card is not `Done` and `force` was not given, stop. Tell the user which blockers are open, and change nothing.
   Otherwise run `jira.py strike-blockers KEY` to strike through the finished blockers in the card's description.
3. **Start.** Run `jira.py assign KEY` (assigns the card to the user unless already assigned to them), then
   `jira.py transition KEY "In Progress"`.
4. **Create a worktree.** The worktree path is the location the user's CLAUDE.md names for worktrees. If it names none, use `.claude/worktrees/<branch>` and make sure `.claude/worktrees/` is in `.gitignore`. `<branch>` is `<key-lowercase>-<short-description>`. From the repo root, run `git fetch origin`, then `git worktree add <worktree path> -b <branch> origin/main`. Work only inside the worktree. Never commit to `main`.
5. **Check tools.** Run the version commands for the tools the card needs, such as `uv --version` or `R --version`. If a tool is missing or older than the card requires, stop and ask.
6. **Implement the steps in order.**
   - For each test step, write the test, run it, and see it fail for the expected reason before you implement.
   - Do only what the card asks.
   - Put throwaway files in this session's scratchpad directory, never in the repo.
7. **Handle card problems.** A card may name a function, flag, or version that doesn't exist. Make the smallest change that still meets the card's goal and acceptance criteria. Record each one as a deviation: what the card said, what you did, and why.
8. **Verify locally.**
   - Run `make pre-pr` from the worktree root. It must exit 0. On failure, find the root cause, fix it, and run it again.
   - Check each acceptance criterion and note the evidence: a test name, a command and its output, or a file.
   - Criteria you cannot check (anything needing the user's accounts, real data, or eyes on the dashboard) go in a "Needs You" list. They do not block the PR.
9. **Commit and push.** Use plain-English commit messages. Then `git push -u origin <branch>`.
10. **Open the PR** with `gh pr create`:
    - Title: `[KEY] <card summary>`.
    - Body: follow `.github/pull_request_template.md` if it exists, and fill in every section. Link the card with its URL from `jira.py get`.
    - Add a section listing each acceptance criterion with its evidence.
    - Add "Deviations from the card" and "Needs You" sections, or write "None" in each.
11. **Comment on the card:** `jira.py comment KEY "PR: <url>"`.
12. **Watch CI.**
    - Wait until `gh pr checks <number>` lists checks. They can take up to a minute to appear.
    - Run `gh pr checks <number> --watch --interval 60` in the background, and continue when it finishes.
    - If a check fails, run `gh run view <run-id> --log-failed`, fix the root cause, run `make pre-pr`, push a new commit, and watch again.
    - Stop after 3 fix rounds. Then comment on the card and tell the user what is still failing.
13. **After CI passes,** do any card steps that depend on a CI run, such as adding required status checks to the ruleset. If a step needs permissions you don't have, add it to "Needs You".
14. **Finish.**
    - Run `jira.py transition KEY "In Review"`.
    - Comment on the card with the CI result, deviations, and the Needs You list.
    - Report to the user in the same order: the PR URL, the CI status, deviations, and Needs You.
    - Then run "Review Round" once.

## Review Round

Run this when `/card KEY` is run on a card that is `In Review`, and once at the end of step 14. Work in the card's
existing worktree, at the worktree path from step 4. If it is gone, recreate it from the PR branch with
`git worktree add <worktree path> <branch>`.

1. **Check for a merge on GitHub.** If `gh pr view <number> --json state` is `MERGED`, the user clicked Merge on
   GitHub. Skip to cleanup:
   - Remove the worktree: run `git worktree remove <worktree path>` from the main repo checkout. If it has
     uncommitted changes, stop and tell the user. Never pass `--force`.
   - Delete the local and remote branch if they still exist: `git branch -D <branch>` and
     `git push origin --delete <branch>`.
   - Run `jira.py transition KEY "Done"`, then `jira.py comment KEY "Merged: <PR url>"`.
   - Report the merge, the cleanup, and the card status to the user, and stop.
2. **Gather the PR's comments.** Run `gh api user --jq .login` to get the user's login. Only comments by that login
   count; ignore everyone else, including bots. Collect:
   - top-level comments and review bodies: `gh pr view <number> --json comments,reviews,commits,mergeable`;
   - inline review threads:
     `gh api graphql -f query='{repository(owner:"<owner>",name:"<repo>"){pullRequest(number:<number>){reviewThreads(first:100){nodes{id isResolved comments(first:50){nodes{author{login} body path line}}}}}}}'`.
3. **Sort them.** Every reply you post starts with `**Claude:**`. That marks what is already handled.
   - An **approval** is a top-level comment or review body posted after the last commit's `committedDate` that plainly
     approves, such as "LGTM", "Looks good to me", "merge", or "ship it", with no conditions. "LGTM once X is fixed" is feedback.
   - **Open feedback** is any other top-level comment or review body with no later `**Claude:**` comment, and any
     unresolved inline thread whose last comment is not a `**Claude:**` reply.
4. **If there is open feedback,** first run "Sync with Main", then address the feedback, even if there is also an
   approval:
   - Treat each comment as an amendment to the card. Where it contradicts the card, follow the comment. Where it
     contradicts CLAUDE.md, or is unclear, stop and ask.
   - Make the changes, following the Workflow rules: tests first where behavior changes, `make pre-pr` exits 0, plain
     new commits, `git push`.
   - Update the PR body if the acceptance evidence, deviations, or Needs You list changed.
   - Reply to each comment. Inline threads: reply in the thread with `**Claude:** <what changed> in <short sha>`, then
     resolve it with the `resolveReviewThread` GraphQL mutation. Top-level comments and review bodies: one top-level
     comment starting with `**Claude:**` that lists each point and what changed.
   - Watch CI as in step 12, then comment on the card with a short summary of the changes.
   - Report the changes and the CI result to the user, and stop. The user approves on a later `/card KEY`.
5. **If there is an approval and no open feedback,** merge:
   - Run `gh pr view <number> --json mergeable,mergeStateStatus`. If `mergeable` is `CONFLICTING` or
     `mergeStateStatus` is `BEHIND`, run "Sync with Main". If it merged cleanly and CI passes, keep going. If you had to
     resolve conflicts, the code changed after approval: report it to the user and stop.
   - Every check in `gh pr checks <number>` must pass, and `mergeable` must be `MERGEABLE`. If not, tell the user what
     blocks the merge, and stop.
   - Remove the worktree: run `git worktree remove <worktree path>` from the main repo checkout. If it has
     uncommitted changes, stop and tell the user. Never pass `--force`.
   - Run `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`. From the main repo checkout,
     run `gh pr merge <number> --delete-branch` with `--squash` if allowed, else `--merge`, else `--rebase`. This
     deletes the remote and local branch. Never use `--admin` or `--auto`.
   - Confirm both branches are gone: `git branch --list <branch>` and `git ls-remote --heads origin <branch>` print
     nothing. Delete any leftover with `git branch -D <branch>` or `git push origin --delete <branch>`.
   - Run `jira.py transition KEY "Done"`, then `jira.py comment KEY "Merged: <PR url>"`.
   - Report the merge, the cleanup, and the card status to the user.
6. **If there is neither,** run "Sync with Main". If the branch was already up to date, tell the user the PR is
   waiting for review, and stop. Otherwise report the sync and the CI result, and stop.

### Sync with Main

1. In the worktree, run `git fetch origin`, then `git merge-base --is-ancestor origin/main HEAD`. Exit 0 means the
   branch already has everything in main: skip the rest.
2. Run `git merge origin/main`. Never rebase or force-push.
3. On conflicts, read both sides and the commits on main that caused them (`git log HEAD..origin/main`). Keep both
   intents: the card's changes and main's changes. If you cannot tell how to combine them, run `git merge --abort`,
   then stop and ask.
4. Run `make pre-pr`. It must exit 0. Fix anything main broke, such as renamed functions or changed fixtures, in a
   separate commit.
5. `git push`, then watch CI as in step 12.
6. Comment on the card: `Merged main into the PR` plus the conflicts you resolved, if any. Do not comment on the PR:
   a `**Claude:**` comment there would mark open feedback as handled.

## Never

- Merge without an approval comment from the user, approve the PR, enable auto-merge, or bypass rules with `--admin`.
- Push to `main`, force-push, or rewrite pushed history. Fix problems with new commits.
- Move the card to `Done` before its PR is merged.
- Turn off, skip, or weaken tests, linters, or CI checks to get green. That includes `pytest.mark.skip`, `skip()` in testthat, `# noqa` or `# nolint` comments, and loosened assertions, unless the card itself calls for it.
- Work on other cards or fix unrelated code. If you notice something, mention it in your report.

## Stop and Ask When

- A blocker is open (step 2).
- The card contradicts itself or CLAUDE.md in a way the smallest-change rule cannot settle.
- A command needs `sudo`, an interactive login, or a secret you don't have.
- CI is still failing after 3 fix rounds.
- A PR comment contradicts CLAUDE.md or is unclear.
- The worktree has uncommitted changes when it is time to merge.
