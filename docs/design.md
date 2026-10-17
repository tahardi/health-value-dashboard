# Health Value Dashboard: Design

Status: approved 2026-10-16. Plan: [plan.md](plan.md). Repo `tahardi/health-value-dashboard`, Jira project `HVD`.

## Purpose

This project is a teaching example for statisticians and analysts who build dashboards for an orthopedic practice. The
kind of app it copies is a "value dashboard": a Shiny app that lets doctors compare surgeons and procedures on outcomes
and cost. Building one by hand is often painful, less because of the code and more because there is no software
engineering workflow around it: no branches, pull requests (PRs), cards, tests, continuous integration (CI), or
automated deploys.

This project is a small, working value dashboard, built the way a real team would build one, so a learner can:

1. Run the app, locally and from a published image.
2. Go through the full loop of adding a feature with Claude: pick a card, run `/card` on it, watch the tests and CI,
   review the PR, merge it, see the new image publish, and see the card move to Done.

It is not a copy of any real app. It uses made-up data. It looks close enough to a real orthopedic practice that the
lessons carry over directly.

## Success Criteria

- On a Mac with Docker, one command (`make docker-run-registry`) runs the app, and the dashboard opens at
  `http://localhost:8000`.
- Merging a PR to `main` publishes a new Docker image with no manual steps. Once a host is chosen (HVD-1), merging also
  deploys it.
- Uploading a new data file through the Data tab updates every open dashboard without restarting the app. A file with
  missing or wrong columns is rejected with a plain message that names the problem, and the current data stays in
  place.
- Adding a new measure (for example "discharged home") takes one schema entry plus its column in the data. It appears
  in the measure dropdowns with no screen code changes.
- Every statistic the app shows is checked by a test against reference answers computed in R.
- A learner can run `/card` on the Surgeons tab card and take it from card to merged PR to published image, using only
  the starter kit tools.

## Scope

Built first:

- Repo, tooling, CI, Docker image, and image publishing on merge
- Schema, data loader with validation, and synthetic data generator
- Value tab and Data tab
- R reference script and golden tests
- The starter kit (`/card` and `jira.py`)
- Screenshots of the Value and Data tabs, captured with a headless browser by `make screenshots` and written to
  `docs/screenshots/`
- Inviting the learner to the GitHub repo (as a collaborator with write access, so they can review and merge) and to
  the HVD Jira project. Both are manual cards, since they need the learner's GitHub username and email.

Left as cards for the learner (written in full, but not built beforehand):

- **Surgeons tab with funnel plot.** The main example card.
- **Add a measure via the schema.** A smaller second example.
- **Procedures tab.** Outlined only, labeled `needs-refinement`.

Deferred or out of scope:

- Connecting to a database
- Login or user accounts
- Any real data, real schema, or real R code (a learner can swap in their own later)
- Choosing the hosting service (HVD-1)

## Stack

- **Python 3.12** with **Shiny for Python** (`shiny`). Many value dashboards start in R Shiny, so the reactive model
  carries over. Python was chosen for better Claude output and simpler tooling.
- **uv** for packages, **ruff** for formatting and linting, **pytest** for tests. These match the starter kit's
  `CLAUDE.md`.
- **pandas** for data, **scipy** for statistics, **plotly** through `shinywidgets` for interactive charts (hover to
  see a surgeon's numbers).
- **Docker** image as the unit of deployment. The same image runs locally and on any host.

## Repo Layout

```
app/
  app.py            Shiny app: tabs, shared data reactive
  schema.py         the one place that knows the data's columns
  data.py           load + validate a CSV against the schema
  stats.py          all statistics (pure functions on DataFrames)
  value_tab.py      Value tab UI and server
  data_tab.py       Data tab UI and server
data/sample.csv     generated synthetic data, committed
scripts/generate_data.py
reference/
  compute.R         computes reference answers from data/sample.csv
tests/
  golden/*.csv      reference answers written by compute.R, committed
  test_*.py
docs/               this design, the plan, and screenshots
TOUR.md             the self-guided tour of this project
Dockerfile
Makefile
.github/workflows/ci.yml
.github/workflows/release.yml
.github/pull_request_template.md
CLAUDE.md           short project notes for Claude: layout, make targets, project rules
starter-kit/        the /card command and jira.py, reviewed by PR; the tour installs them
```

## Data

**Schema (`app/schema.py`).** A list of column definitions. Each has the column name in the CSV, a display label, a
type (`category`, `number`, `boolean`, `date`), and a role:

- `id`: the case identifier
- `dimension`: something you group by. A `filter` flag marks the dimensions that get a filter control (`procedure` and
  `facility` in the first version)
- `measure`: something you measure; also says whether higher is better
- `date`: the surgery date, used for the date range filter

Screens never name a column directly. Filter controls are built from `dimension` columns with the `filter` flag, and
measure dropdowns from `measure` columns. The value view needs four named roles, set in the schema: which dimension is
the surgeon, which measure is cost, which pair of measures is the function score before and after, and which date is
the surgery date. Changing the schema later means editing this file and nothing else, except where a chart truly
depends on a specific measure.

**Columns (made up, realistic for orthopedics):**

| Column | Type | Role |
|---|---|---|
| `case_id` | category | id |
| `surgeon` | category | dimension |
| `procedure` | category | dimension: Total Knee Replacement, Total Hip Replacement, ACL Reconstruction, Rotator Cuff Repair, Lumbar Spinal Fusion |
| `facility` | category | dimension: 3 facilities |
| `payer` | category | dimension: Medicare, Commercial, Medicaid |
| `age_group` | category | dimension: <50, 50-64, 65-74, 75+ |
| `sex` | category | dimension |
| `asa_class` | category | dimension: ASA risk class 1 to 4 |
| `surgery_date` | date | date |
| `length_of_stay_days` | number | measure, lower is better |
| `total_cost` | number | measure, lower is better |
| `implant_cost` | number | measure, lower is better |
| `complication` | boolean | measure, lower is better |
| `readmit_30d` | boolean | measure, lower is better |
| `discharged_home` | boolean | **not in the first version**; the "add a measure" card adds it |
| `function_pre` | number | measure (patient-reported function score 0 to 100 before surgery) |
| `function_post` | number | measure (same score 6 months after) |

`function_gain` (post minus pre) is derived in `data.py` after loading, not stored.

**Blank cells.** `id`, `dimension`, and `date` columns must not be blank. `measure` columns may be blank, as in real
data where a patient misses follow-up. Each statistic drops blanks for its own measure and reports its own case count.
The R script does the same with `na.rm = TRUE` and `complete.cases`. The generator leaves about 5% of `function_post`
blank, so the tests cover it.

**Synthetic data (`scripts/generate_data.py`).** Fixed seed, about 2,000 cases over two years, 12 surgeons. Surgeon
volumes vary widely, including two with fewer than 20 cases, so the funnel plot has something to teach. The data has a
planted story: one surgeon with clearly higher readmissions, one with high cost and average outcomes, and one with low
cost and good outcomes. Values depend sensibly on procedure (spinal fusion costs more and stays longer than rotator
cuff repair) and on ASA class. `make data` regenerates `data/sample.csv`, and the same seed always gives the same file.
The generator also writes a `discharged_home` column. The schema leaves it out until the "add a measure" card, so the
loader ignores it until then.

**Loading and validation (`app/data.py`).** `load(path) -> DataFrame` checks the file against the schema: required
columns are present, types parse, booleans are 0/1 or true/false, and numbers are not negative. Every error found is
reported together in one message, such as "missing column `total_cost`; column `surgery_date` has 3 values that are
not dates (rows 14, 92, 310)". Extra columns are allowed and ignored.

**Where the data lives.** The app reads one file at `DATA_PATH` (an environment variable). Run locally without Docker,
it defaults to `data/sample.csv`. In the image, `DATA_PATH=/data/current.csv`, and `/data` is a mounted volume. On
startup, if `/data/current.csv` does not exist, the app copies the bundled sample there, so uploads survive restarts
and new image versions. The Docker run targets mount `./.hvd-data` (ignored by git) at `/data`. The hosting card must
give `/data` a persistent disk. A shared `reactive.file_reader` watches the file, so every session reloads when it
changes, whether the change came from an upload or from someone copying a file onto the server.

## Screens

Tabs, overview first. Filters across the top: procedure, facility, and date range. All filter options come from the
schema.

**Value tab (landing view).**

- A "Rate measure" dropdown built from the schema's yes/no measures (default 30-day readmission). This is where a new
  measure shows up with no screen changes.
- Headline numbers for the filtered cases: case count, average cost, average function gain, and the selected rate.
- Value map: a scatter plot with one dot per surgeon. X is average cost, Y is average function gain, and dot size is
  case count. Dashed lines at the overall averages split it into four quadrants (better and cheaper, and so on). Hover
  shows the surgeon's numbers.
- Table, one row per surgeon: cases, average cost with 95% confidence interval (CI), average function gain with 95% CI,
  value (gain points per $1,000), and the selected rate. Sortable.
- Surgeons with fewer than 10 cases in the current filter are shown faded and marked "low volume", not hidden.

**Data tab.**

- Shows the current file: row count, date range, last updated time.
- Upload a CSV. It is validated before it replaces anything. On success, the file at `DATA_PATH` is replaced (write to
  a temp file, then rename) and all sessions reload. On failure, the errors are listed and nothing changes.
- A "download sample file" button that shows the expected format.
- The schema shown as a table (column, type, role) that shows what the app expects.

**Surgeons tab (a card for the learner, not built beforehand).**

- Pick a rate measure (complication, 30-day readmission).
- Funnel plot: each surgeon's rate (Y) against case count (X). The center line is the overall rate. Control limits are
  95% and 99.8%, computed with the normal approximation: `p ± z * sqrt(p * (1 - p) / n)` with z = 1.96 and 3.09,
  clipped to [0, 1]. Surgeons outside the 99.8% limit are highlighted.
- Trend over time (by quarter) for a selected surgeon against everyone else.

## Statistics and R Validation

All statistics live in `app/stats.py` as pure functions that take a DataFrame and return a DataFrame, with no Shiny
code. This keeps them easy to test.

- Means with 95% CI use the t-distribution (`mean ± t(0.975, n-1) * sd / sqrt(n)`), matching R's `t.test`.
- Rates are simple proportions. Funnel limits are as above.
- Value is `mean(function_gain) / (mean(total_cost) / 1000)`. No CI in the first version.

**Reference answers.** `reference/compute.R` reads `data/sample.csv` and writes one CSV per statistic to
`tests/golden/` (for example `surgeon_summary_readmit_30d.csv`). It uses base R only. `make reference` runs it inside
the `rocker/r-ver:4.4.1` Docker image, so nobody needs R installed. The golden files are committed, and CI does not
run R.

**Golden tests.** For each golden file, a pytest test computes the same statistic in Python and compares every value
with `numpy.testing.assert_allclose` at a relative tolerance of `1e-9`. Funnel limits and summaries must match exactly
up to floating point error.

The funnel card adds its own R reference code and golden file as part of the card. This is the pattern to follow when
porting any statistic: write or reuse R code you trust, and the Python must match it.

## Workflow and CI

- `main` is protected by a GitHub ruleset: changes only through PRs, and the CI checks must pass.
- **Makefile targets:** `install`, `format`, `lint`, `test`, `pre-pr` (everything below, run before every PR), `run`
  (local dev server with reload), `data`, `reference`, `screenshots`, `docker-build`, `docker-run-local`,
  `docker-run-registry`, `docker-clean`, `docker-prune`.
- **`ci.yml`**, on every PR: `uv sync`, `ruff format --check`, `ruff check`, `pytest`, and `docker build`, so a broken
  Dockerfile fails the PR, not the release.
- **`release.yml`**, on push to `main`: build the image for `linux/amd64` and `linux/arm64` (so it runs natively on
  Apple Silicon Macs) and push it to GitHub Container Registry as `ghcr.io/tahardi/health-value-dashboard:latest` and
  `:<short sha>`. The hosting card adds a deploy job once HVD-1 is answered.
- **Public repo and image.** The data is synthetic, so the repo and the container package are public. Pulling the
  image needs no login, which keeps `make docker-run-registry` to one command.
- **Local runs:** `make docker-run-registry` pulls and runs the `:latest` image on port 8000. `make docker-build` then
  `make docker-run-local` builds and runs local changes.
- PR template with sections: summary, card link, acceptance criteria evidence, deviations, Needs You.

## Starter Kit

The kit lives in `starter-kit/` and the tour installs it into `~/.claude/`. It holds a global `CLAUDE.md`,
`settings.json`, and `statusline.sh`, plus the `/card` command (`skills/card/SKILL.md`) and its Jira helper
(`skills/card/scripts/jira.py`), kept general and Python/R flavored:

- `/card KEY` reads the card, checks its blockers, assigns it, moves it to In Progress, works in its own worktree at
  the location the global `CLAUDE.md` names, writes tests first, runs `make pre-pr`, opens the PR, and watches CI.
- Steps that depend on a CI run happen after CI passes.
- The Review Round reads the PR comments, fixes them, replies with `**Claude:**`, resolves threads, and merges after
  the user's approval comment. It then cleans up the worktree and branches and moves the card to Done.
- If the PR was already merged by clicking Merge on GitHub, the next `/card` run does the same cleanup and moves the
  card to Done.
- Sync with Main merges `main` into the PR branch when it falls behind.
- `jira.py` has `get` (with the assignee and struck-through text), `transition`, `comment`, `assign`, and
  `strike-blockers`.

## How to Explore

The project is explored through `TOUR.md`, a self-guided tour run with Claude Code. It walks through the board, the
repo, running the app, and taking a card from start to merge.

## Left to the Builder

- Exact chart styling and colors
- Internal function signatures beyond what is named here
- How the generator models the relationships between columns, as long as the planted story shows up
- Dockerfile details, beyond a slim Python base, uv, port 8000, and `DATA_PATH`
