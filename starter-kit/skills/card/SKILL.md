---
name: card
description: Use when the user runs /card with a Jira card key (e.g. /card VD-12) to implement that card end to end
argument-hint: <JIRA-KEY> [force]
disable-model-invocation: true
---

# Implement a Jira Card

Implement the card named in the arguments, get it green locally and in CI, and leave a PR for the user to review. The card is the spec. You never merge.

**Arguments:** `$ARGUMENTS`. The first word is the card key (`[A-Z]+-\d+`). If the second word is `force`, skip the blocker check.

**Jira helper:** `python3 ~/.claude/skills/card/scripts/jira.py` with `get KEY`, `transition KEY STATUS`, or `comment KEY TEXT`. It reads credentials from `~/.config/jira/env`. Never print or echo that file.

## Precedence

1. The user's CLAUDE.md rules (worktrees, PR title format, no comments, test style).
2. The card: files, names, types, steps, commands, and acceptance criteria.
3. Your own defaults.

If rules 1 and 2 conflict, stop and ask the user.

## Workflow

1. **Read the card.** Run `jira.py get KEY` and read all of it.
2. **Check blockers.** If any "Blocked by" card is not `Done` and `force` was not given, stop. Tell the user which blockers are open, and change nothing.
3. **Start.** Run `jira.py transition KEY "In Progress"`.
4. **Create a worktree.** From the repo root, run `git fetch origin`, then `git worktree add .claude/worktrees/<branch> -b <branch> origin/main`, where `<branch>` is `<key-lowercase>-<short-description>`. Make sure `.claude/worktrees/` is in `.gitignore`. Work only inside the worktree. Never commit to `main`.
5. **Check tools.** Run the version commands for the tools the card needs, such as `uv --version` or `R --version`. If a tool is missing or older than the card requires, stop and ask.
6. **Implement the steps in order.**
   - For each test step, write the test, run it, and see it fail for the expected reason before you implement.
   - Do only what the card asks.
   - Put throwaway files in this session's scratchpad directory, never in the repo.
7. **Handle card problems.** A card may name a function, flag, or version that doesn't exist. Make the smallest change that still meets the card's goal and acceptance criteria. Record each one as a deviation: what the card said, what you did, and why.
8. **Verify locally.**
   - Run `git fetch origin && git merge origin/main` to pick up anything merged since you started. Fix any conflicts.
   - Run `make pre-pr` from the repo root. It must exit 0. On failure, find the root cause, fix it, and run it again.
   - Check each acceptance criterion and note the evidence: a test name, a command and its output, or a file.
   - Criteria you cannot check (anything needing the user's accounts, real data, or eyes on the dashboard) go in a "Needs You" list. They do not block the PR.
9. **Commit and push.** Use plain-English commit messages. Then `git push -u origin <branch>`.
10. **Open the PR** with `gh pr create`:
    - Title: `[KEY] <card summary>`.
    - Body: follow `.github/pull_request_template.md` if it exists. Link the card with its URL from `jira.py get`.
    - Add a section listing each acceptance criterion with its evidence.
    - Add "Deviations from the card" and "Needs You" sections, or write "None" in each.
11. **Comment on the card:** `jira.py comment KEY "PR: <url>"`.
12. **Watch CI.**
    - Wait until `gh pr checks <number>` lists checks. They can take up to a minute to appear.
    - Run `gh pr checks <number> --watch --interval 60` in the background, and continue when it finishes.
    - If GitHub reports a merge conflict, run `git fetch origin && git merge origin/main`, fix the conflicts, run `make pre-pr`, and push.
    - If a check fails, run `gh run view <run-id> --log-failed`, fix the root cause, run `make pre-pr`, push a new commit, and watch again.
    - Stop after 3 fix rounds. Then comment on the card and tell the user what is still failing.
13. **Finish.**
    - Run `jira.py transition KEY "In Review"`.
    - Comment on the card with the CI result, deviations, and the Needs You list.
    - Report to the user in the same order: the PR URL, the CI status, deviations, and Needs You.

## Never

- Merge, approve, or enable auto-merge on the PR.
- Push to `main`, force-push, or rewrite pushed history. Fix problems with new commits.
- Move the card to `Done`.
- Turn off, skip, or weaken tests, linters, or CI checks to get green. That includes `pytest.mark.skip`, `skip()` in testthat, `# noqa` or `# nolint` comments, and loosened assertions, unless the card itself calls for it.
- Work on other cards or fix unrelated code. If you notice something, mention it in your report.

## Stop and Ask When

- A blocker is open (step 2).
- The card contradicts itself or CLAUDE.md in a way the smallest-change rule cannot settle.
- A command needs `sudo`, an interactive login, or a secret you don't have.
- CI is still failing after 3 fix rounds.
