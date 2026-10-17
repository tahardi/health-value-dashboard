# Part 1: Setup

In this part she installs her tools and her Claude setup, runs the app, and closes her first Jira card. Steps 1 to 3
happened before you read this file. Each later step starts with a bold title; use it in the progress file.

Until step 10 she runs plain `claude`, so you ask before every command and file change. Steps 4 to 9 run in
`~/code/health-value-dashboard`. Several commands below use `$SHELL_FILE` and `$PROFILE_FILE`. Work them out once
with `echo $SHELL`: for zsh, `$SHELL_FILE` is `~/.zshrc` and `$PROFILE_FILE` is `~/.zprofile`; for bash, both are
`~/.bash_profile`. Write the real path into each command you run.

**Step 1: Open Terminal and start Claude**

She opened Terminal and started Claude in `~/code`. Nothing to do.

**Step 2: Pick the model**

She typed `/model sonnet`. Nothing to do.

**Step 3: Paste the kickoff prompt**

She pasted the kickoff prompt and you cloned the repo. Nothing to do.

**Step 4: Welcome**

Create the progress file if it does not exist, with steps 1 to 3 under `## Done`. Then say:

> Welcome to the Health Value Dashboard tour! You've opened Terminal, started Claude, picked Sonnet, and I've
> downloaded the project, so those first three steps are done.

Then explain, in a few short lines:

- The tour has four parts: Setup (this part), a tour of how one feature was built, building two small features
  yourself, and designing and building your own feature.
- You go one step at a time and stop after each. She says "next" to go on, or asks anything at any point.
- For now, Claude asks before every command and file change. She reads the one-line reason and picks "Yes". In
  step 10 she switches to a mode where Claude stops asking.

**Step 5: Accept the invites**

Ask her:

> Taylor sent you two email invitations: one from GitHub for the health-value-dashboard project, and one from
> Atlassian for Jira. Have you accepted both?

If she has not accepted the GitHub one, run `open https://github.com/tahardi/health-value-dashboard/invitations`
and ask her to click "Accept invitation". If she has not accepted the Jira one, ask her to open the Atlassian email
and click its button, then create her Atlassian account if it asks. If she cannot find an email, draft a text to
Taylor asking for it to be sent again, and continue.

**Step 6: Install tools**

Define Homebrew: a tool that installs other tools on a Mac.

1. Run `brew --version`. If it works, skip to item 4. If it says "command not found", try
   `/opt/homebrew/bin/brew --version`. If that works, Homebrew is installed but not on her path: skip to item 3.
2. Say:

   > Next you'll install Homebrew. It asks for your Mac password. When you type it, nothing appears on the screen,
   > not even dots. That's normal: type it and press Return. It may also ask you to press Return to continue, and it
   > may install Apple's developer tools first. It can take 10 minutes or more.

   Then have her type this in this Claude window:

   ```text
   ! /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   Wait for it to finish, then run `/opt/homebrew/bin/brew --version` to check it worked.
3. Add Homebrew to her path, only if the line is missing:

   ```bash
   grep -qF 'brew shellenv' $PROFILE_FILE 2>/dev/null \
     || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $PROFILE_FILE
   ```

4. This Claude session started before Homebrew was on her path, so it may not find the new tools until step 10.
   Start every command that uses `brew`, `gh`, `uv`, `jq`, `docker`, or `python3` with
   `eval "$(/opt/homebrew/bin/brew shellenv)" && ` until then. Commands she types with `!` need it too. After step 8,
   Claude may show errors about `jq` from the new settings; ignore them until step 10.
5. Install the tools that are missing. Check each with `command -v gh`, `command -v uv`, and `command -v jq`, and
   check Python with `python3 -c 'import sys; print(sys.version_info >= (3, 10))'`, which must print `True`. Run
   `brew install` with only the missing ones, using `python` for Python. Explain each in one line: `gh` talks to
   GitHub, `uv` installs the app's packages, `jq` reads data for the status line she gets in step 8, and `python`
   is a newer Python than the one built into macOS, which the `/card` command needs.
6. Define Docker: a tool that runs apps in sealed boxes, so they work the same on every computer. If
   `/Applications/Docker.app` exists, skip to item 7. Otherwise the installer may ask for her Mac password, so she
   types it in this Claude window:

   ```text
   ! eval "$(/opt/homebrew/bin/brew shellenv)" && brew install --cask docker
   ```

7. Run `open -a Docker`. Say:

   > Docker Desktop is opening. Accept its terms. If it asks you to sign in, you can skip that. Tell me when you
   > see its main window.

**Step 7: GitHub login**

1. Run `gh auth status`. If it shows she is logged in to github.com, skip to item 3.
2. Have her type this in this Claude window:

   ```text
   ! eval "$(/opt/homebrew/bin/brew shellenv)" && gh auth login -h github.com -p https -w
   ```

   That picks GitHub.com, HTTPS, and logging in with a browser. If it asks whether to authenticate Git with her
   GitHub credentials, she picks "Yes". It shows a one-time code; she presses Return, a browser opens, and she
   pastes the code there.
3. Run `gh auth setup-git`. Explain: this lets git use her GitHub login when it sends work to GitHub.
4. Run `gh api repos/tahardi/health-value-dashboard --jq .permissions.push`. If it prints `false` or an error
   such as "Not Found", her GitHub invite is not accepted yet: go back to step 5's GitHub link, then run it again.
5. Run `git config --global user.name` and `git config --global user.email`. If both print a value, skip this
   item. Otherwise ask her for her full name and the email address on her GitHub account, then set them with
   `git config --global user.name "<her name>"` and `git config --global user.email "<her email>"`. Her name and email
   are not secrets, so asking for them in the chat is fine. Explain: git stamps every saved change with them.

**Step 8: Install her global Claude setup**

Define "global Claude setup": files in `~/.claude/` that shape how Claude works in every project on her Mac. Do
these in this order. The new settings block edits to her shell files, so the shell file comes first.

1. Back up anything already there. A file already in the backup folder is never overwritten, so a second run
   keeps the first backup:

   ```bash
   mkdir -p ~/.claude/backups
   for f in CLAUDE.md settings.json statusline.sh skills/card; do
     if [ -e ~/.claude/$f ] && [ ! -e ~/.claude/backups/$(basename $f) ]; then
       cp -R ~/.claude/$f ~/.claude/backups/ && echo "backed up $f"
     fi
   done
   ```

   If it printed any "backed up" lines, tell her which files and that they are in `~/.claude/backups/`.
2. Add `colo` to her shell file, only if it is not already there:

   ```bash
   grep -q 'colo()' $SHELL_FILE 2>/dev/null \
     || echo 'colo() { claude --dangerously-skip-permissions "$@"; }' >> $SHELL_FILE
   ```

   Say:

   > I've added a command called `colo`, short for "Claude YOLO". It starts Claude in a mode where it doesn't stop
   > to ask permission before each command. A short list of dangerous commands stays blocked even then.

3. Copy the starter kit. These are copies, not links, so deleting the repo later breaks nothing:

   ```bash
   mkdir -p ~/.claude/skills/card
   cp -R starter-kit/skills/card/. ~/.claude/skills/card/
   cp starter-kit/CLAUDE.md starter-kit/statusline.sh starter-kit/settings.json ~/.claude/
   ```

   Explain each in one line: `CLAUDE.md` holds the coding rules Claude follows in every project; `settings.json`
   sets Sonnet as the default model, the list of blocked commands, the status line, and a bell sound;
   `statusline.sh` draws the status line; `skills/card` is the `/card` command.
4. Run `claude plugin list`. If it lists `superpowers`, skip this item. Otherwise run
   `claude plugin install superpowers@claude-plugins-official`. If it says the marketplace is not found, run
   `claude plugin marketplace add anthropics/claude-plugins-official` and try again. Say:

   > I've installed a plugin called superpowers. It gives Claude good habits: ask questions before building,
   > write a plan, and test as it goes. It's the toolkit Taylor uses.

**Step 9: Jira token**

Define an API token: a password just for programs, so Claude can read and update Jira cards for her. It is a
secret. Never ask her to paste it into the chat. Her Jira email goes in the same file, so she types it there too.

1. If `~/.config/jira/env` exists, run `python3 ~/.claude/skills/card/scripts/jira.py get HVD-24`. If it prints
   the card, skip the rest of this step.
2. Run `open https://id.atlassian.com/manage-profile/security/api-tokens`. Say:

   > A web page opened. Click "Create API token", name it "Claude", and pick the longest expiry it allows. Click
   > "Create", then "Copy". Don't paste it here in the chat. I'll open a file for you to paste it into.

3. If `~/.config/jira/env` does not exist, create it:

   ```bash
   mkdir -p ~/.config/jira
   printf 'JIRA_SITE=https://taylorantoniohardin.atlassian.net\nJIRA_EMAIL=\nJIRA_TOKEN=\n' > ~/.config/jira/env
   ```

   Then run `chmod 600 ~/.config/jira/env` (only she can read it) and `open -e ~/.config/jira/env`. Say:

   > A file opened in TextEdit. Click right after `JIRA_EMAIL=` and type the email you use for Jira. Click right
   > after `JIRA_TOKEN=` and paste the token. No spaces anywhere. Press Cmd+S to save, close TextEdit, and tell me
   > when you're done.

4. Run `chmod 600 ~/.config/jira/env` again, since saving in TextEdit can reset it. Then run
   `python3 ~/.claude/skills/card/scripts/jira.py get HVD-24`. If it prints the card, tell her Jira is connected.
   If it fails, run `open -e ~/.config/jira/env` again and ask her to check for spaces, a missing character, or the
   wrong email. An error with 401 or 403 can also mean her Jira invite is not accepted yet: go back to step 5.
   Never read or print the file yourself.

**Step 10: Restart**

Add this step under `## Done` in the progress file now, before she exits, so the new session starts at step 11.
Then say:

> Now you'll restart Claude so the new setup takes effect. Follow these steps exactly:
>
> 1. Type `/exit` and press Return. Claude closes.
> 2. Press Cmd+W to close this Terminal window. If it asks, click "Terminate".
> 3. With Terminal still selected, press Cmd+N to open a new window.
> 4. In the new window, type `cd ~/code/health-value-dashboard` and press Return.
> 5. Type `colo` and press Return.
> 6. Claude shows a warning that says it's running in Bypass Permissions mode, with two choices: "No, exit" and
>    "Yes, I accept". Press the down arrow to pick "Yes, I accept", then press Return. You only see this once.
> 7. If Claude asks whether you trust the files in this folder, pick "Yes, proceed".
> 8. Type `continue the tour` and press Return.

Show the commands she types in the new Terminal window in one code block:

```text
cd ~/code/health-value-dashboard
colo
```

**Step 11: Show what changed**

You now run under `colo`. Point out:

- The status line at the bottom of the window: the folder, the git branch, the model, how much of Claude's memory
  this chat has used, and the cost.
- The bell: her Mac plays a sound when Claude finishes or needs her, so she can look away while it works.
- No more permission prompts. Claude only stops to ask when a card is unclear. The blocked-command list still
  holds.
- `/card`: have her type `/` in this Claude window and look for `card` in the list, then press Escape. She uses it
  in Part 3.

**Step 12: Smoke test**

Define a smoke test: a quick run of everything to check the setup works before real work. Run `pwd` first; if it
is not `~/code/health-value-dashboard`, give her `cd ~/code/health-value-dashboard`.

1. Run `make install`, then `make test`. Explain: `make install` downloads Python and the app's packages;
   `make test` runs the tests, which check the app's numbers against answers from the R language already saved in the
   repo.
2. Run `make run` in the background, then `open http://localhost:8000`. Ask her to click around: change the
   filters, look at the value map, and open the Data tab. Say:

   > Every piece of this app was built through Jira cards like the ones you'll run in Part 3.

   Stop `make run` once she says she has finished looking.
3. Run `docker info`. If it fails, use the Docker known fix in `TOUR.md`. Then say:

   > Next is `make pre-pr`, the full check every change runs before a pull request. The first run downloads R and
   > Python and builds the app, so it can take 10 to 30 minutes and may look stuck. That's normal. Later runs take
   > about a minute.

   Run `make pre-pr` in the background and check on it every few minutes until it finishes. If it passes, run
   `git status --porcelain`. It should print nothing. If it lists files, show her the list, record it under
   `## Problems`, run `git restore` with only those files, and draft a text to Taylor.
4. If `make reference` or a golden test fails, it is not blocking: run `git restore tests/golden`, record it under
   `## Problems`, draft the text to Taylor, and continue.

**Step 13: Close her first card**

Run `python3 ~/.claude/skills/card/scripts/jira.py get HVD-24`. If its status is already "Done", skip to the
explanation below. Otherwise run `python3 ~/.claude/skills/card/scripts/jira.py assign HVD-24`, then
`python3 ~/.claude/skills/card/scripts/jira.py transition HVD-24 "Done"`, then
`open https://taylorantoniohardin.atlassian.net/browse/HVD-24` either way. Say:

> HVD-24 is the Jira card for this setup. A card is one piece of work. I just put your name on it, which means
> it's yours, and moved it to "Done". Cards move from "To Do" to "In Progress" to "In Review" to "Done" as work
> happens. In Part 3, `/card` moves cards for you as it builds them.

**Step 14: Checkpoint**

Recap Part 1 in two or three sentences: her tools and Claude setup are installed, the app runs on her Mac, and her
first card is closed. Part 1 is not a sitting break, so do not suggest stopping. Wait for "next", then read
`tour/2-tour.md`.
