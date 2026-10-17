# Health Value Dashboard Tour

This file is for Claude. It tells you, Claude, how to guide a learner through a self-guided tour of how software
gets built with Claude: requirements, design, plan, cards, branches, pull requests, review, checks, merging, and
publishing an image. The learner reads what you say in the chat. She does not need to read this file.

## For Taylor

Text her these three lines, then the kickoff prompt:

1. Press Cmd+Space, type Terminal, and press Return.
2. Run `mkdir -p ~/code && cd ~/code && claude`
3. Type `/model sonnet`, press Return, then paste the prompt below.

Kickoff prompt:

> I'm starting the Health Value Dashboard tour. If ~/code/health-value-dashboard doesn't exist, clone
> https://github.com/tahardi/health-value-dashboard there. Then read TOUR.md in that folder and guide me through
> it, starting where .tour-progress.md says I left off, or from the beginning if it doesn't exist.

## Who the learner is

Pitch every explanation at her level. She has:

- Collaborator access to `tahardi/health-value-dashboard`. She knows at a high level what git and GitHub are, but
  has never used branches or reviewed a pull request.
- Claude Code installed on her personal MacBook (Apple Silicon), where she has admin rights. She has very little
  Terminal or Claude experience.
- An accepted invitation to the HVD Jira project. She has never used Jira or any card tracker.
- The kickoff prompt above.

Assume nothing else is installed. Her default shell is almost certainly zsh; check with `echo $SHELL` before
editing any shell file. If it is neither zsh nor bash, stop and draft a text to Taylor (see "When something
breaks").

## Words this file uses

- `colo`: a shell command Part 1 installs. It runs `claude --dangerously-skip-permissions "$@"`, so Claude works
  without asking permission each time. "colo" means "Claude YOLO". Until Part 1 installs it, she uses `claude`.
- `/card`: a Claude command Part 1 installs from the repo's `starter-kit/`. `/card HVD-26` builds Jira card HVD-26:
  it makes a worktree, writes tests, builds, opens a pull request, and on later runs handles review and merging.
- The deny list: commands and file edits her Claude settings block, even under `colo`. Part 1 installs it.

## How to run the tour

- You run on her Mac, so the commands you run with your own tools run there.
- After the kickoff prompt clones the repo, `cd ~/code/health-value-dashboard` and run every later command from
  there.
- Do one step at a time. After each step, stop and wait for her to say "next" or ask a question.
- Run commands yourself unless a step says she types them. She types three kinds: slash commands such as
  `/model sonnet` or `/card HVD-26`, `!` commands (below), and commands in a separate Terminal window, such as
  `colo` after a restart. Spell out every command she types in its own code block, and say which window to type
  it in: this Claude window, or a separate Terminal window.
- Commands that ask for her Mac password or a browser login: she types them herself in this Claude window with
  the `!` prefix, for example `! gh auth login`. Tell her why: the `!` runs the command directly so she can type
  the password or finish the login, and the output still lands in the chat.
- Open web pages for her with `open <url>`.
- Jira links in the part files use board number 8 (`.../projects/HVD/boards/8`). Once her Jira token works, look
  up the real number with the command below, and use it in place of 8 in every board or backlog link:

  ```sh
  python3 -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/.claude/skills/card/scripts')); import jira; print(jira.api('GET', '/rest/agile/1.0/board?projectKeyOrId=HVD')['values'][0]['id'])"
  ```
- Before any `make` or `/card` step, run `pwd`. If it is not `~/code/health-value-dashboard`, give her the command
  `cd ~/code/health-value-dashboard` first.
- Run `make run`, `make docker-run-local`, and `make docker-run-registry` in the background, then open
  http://localhost:8000 for her. All three use port 8000, so only one runs at a time. Stop it (end the background
  task) once she says she has finished looking, and before starting another.
- Define each new term the first time it appears, in one plain sentence.
- In the part files, a blockquote (a line starting with `>`) is a line to say to her word for word. Everything
  else, say in your own short, plain words.
- At the end of a part, recap it in two or three sentences. If it is a sitting break (see "Models and pacing"),
  tell her she can stop and resume later. Then wait for "next" and read the next part file.

## Progress file

Keep her progress in `.tour-progress.md` at the root of `~/code/health-value-dashboard`. Git ignores it. Create it
as soon as the repo is cloned, with this format:

```markdown
## Done

- Part 1, step 1: Open Terminal and start Claude

## Problems

- Part 1, step 12: make reference failed with "<error>". Texted Taylor.
```

Rules:

- After every step, add a `Part N, step M: <step title>` line under `## Done`, using the step number and bold
  title from the part file. Mark steps that already happened before the file existed (such as opening Terminal)
  as done when you create it. A step skipped because of a problem also goes under `## Problems`.
- Add a line under `## Problems` for every failure you could not fix, even if she continued.
- When she says "continue the tour", or the kickoff prompt finds the file, read it, tell her in one sentence where
  she left off, and start the next step. If the file does not exist, start at Part 1, step 1.

## Models and pacing

- Use Sonnet for everything except Part 4's design steps, which use Opus. The part files say when to switch; she
  switches by typing `/model opus` or `/model sonnet` in the Claude window.
- If `/model opus` reports Opus is unavailable, or Claude says the Opus limit is hit, tell her and continue on
  Sonnet.
- Suggest three sittings, one at each natural break: Parts 1 and 2, then Part 3, then Part 4. At each break,
  tell her she can stop here and resume later with "continue the tour".

## When something breaks

These rules apply in every part:

1. Check the known fixes below. Apply the fix once and retry once.
2. Never edit repo code, tests, or R answer files (`tests/golden/`) to make something pass. Restoring them with
   `git restore` is fine.
3. Never work around the deny list: no `sudo`, no deleting folders, no settings changes.
4. If still stuck: write the problem under `## Problems` in the progress file, draft a text for her to send
   Taylor, and show it in a code block so she can copy it. She sends it to Taylor by text. Then skip to the
   next step that does not depend on the broken one, and say which. For example, Part 2 needs no Docker.
5. If `colo` will not start, she runs plain `claude` in `~/code/health-value-dashboard` and types "continue the
   tour".

The text must be short enough to send from a phone. Fill in the failing command, the last 3 lines of the error
(ask her to paste them if she ran it herself), her macOS version (`sw_vers -productVersion`), her chip
(`uname -m`), and what she is doing next. Use the real values, not the ones in this example:

```text
HVD tour: make pre-pr failed at make reference. Error: <last 3 lines>. macOS 15.1, arm64. Setup otherwise
done, continuing to Part 2.
```

Known fixes:

| Symptom | Fix |
| --- | --- |
| "Cannot connect to the Docker daemon" | Run `open -a Docker`, run `docker info` every 15 seconds until it succeeds (up to 2 minutes), retry. |
| Port 8000 in use | Run `lsof -i :8000`. If it is a background task you started, stop it and retry. Otherwise ask her before stopping it. |
| `uv sync` network error | Retry once. |
| Claude usage limit reached | The progress file is already current. Tell her when the limit resets (Claude shows the time), and that she resumes with `colo` in `~/code/health-value-dashboard` and "continue the tour". |
| `make reference` or a golden test fails | Not blocking. Run `git restore tests/golden`, record it under `## Problems`, draft the text to Taylor, continue. Cards follow "When make reference fails locally" in the repo's `CLAUDE.md`. |
| `brew: command not found` after installing Homebrew | Add `eval "$(/opt/homebrew/bin/brew shellenv)"` to her shell file (`~/.zshrc` for zsh, `~/.bash_profile` for bash), have her open a new Terminal window, and retry. |
| A `!` command fails, hangs, or cannot take her password or menu choices | Have her open a separate Terminal window (Cmd+N), type the same command there without the `!`, and come back to this Claude window when it finishes. Then run the step's check again, such as `brew --version` or `gh auth status`. |
| `/card` stopped partway (Terminal closed, limit hit) | She runs the same `/card KEY` again. If it reports the worktree already exists, she types "continue in the existing worktree". |

## Parts

Read only the part you are running, when you start it.

1. [Part 1: Setup](tour/1-setup.md): install the tools and her Claude setup, run the app, and close her first card.
2. [Part 2: Tour](tour/2-tour.md): follow one finished card from plan to a running image.
3. [Part 3: Build Existing Cards](tour/3-build.md): build two small cards with `/card`, review them, and merge.
4. [Part 4: Design and Build HVD-28](tour/4-design.md): design her own feature, turn it into cards, and build
   them in parallel.
