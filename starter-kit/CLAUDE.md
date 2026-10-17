## Coding

Every card gets its own git worktree at `~/code/wts/<repo>-<card-lowercase>-<description>`. For example, card HVD-26
in the `health-value-dashboard` repo, about patients discharged home, gets
`~/code/wts/health-value-dashboard-hvd-26-discharged-home`. Never change `main` directly.

Title a PR `[KEY] Card Title`, such as `[HVD-26] Discharged Home`. When there is no card, use a short plain title.

## Style

- Never add code comments unless I ask. The `# given`, `# when`, `# then` markers in tests are fine.
- Keep lines under 120 characters, unless the project's formatter sets another limit. When a call or signature is too
  long, put one argument per line.
- Keep each file about one subject.

## Python

- Put type hints on every function signature.
- Use `uv` for dependencies (`uv add`). Never run `pip install`.
- Test with pytest. Write one `test_<function>` per function, with all of its cases inside, as a table of cases with
  `@pytest.mark.parametrize`. Split each test into `# given`, `# when`, and `# then` sections.

## Writing

Be clear and concise. Use plain English. No filler.

## Planning work

1. Design new work with the superpowers brainstorming skill.
2. Save designs and plans to `docs/designs/` in the repo.
3. Turn the plan into Jira cards with `python3 ~/.claude/skills/card/scripts/jira.py` (`create`, `edit`, `link`,
   `sprint`).

Card rules:

- Write every card so Sonnet could build it without the planning conversation: the files to create or change, exact
  commands, interfaces and data shapes, and edge cases. Acceptance criteria name the tests that pass or the properties
  that hold.
- Lay out each card as: Files, Interfaces, numbered test-first steps, Acceptance criteria, Global Constraints.
- Mark dependencies with Blocks links. Label a card `parallelizable` when it can run alongside others without editing
  the same files.
- Points estimate my review effort: 1, 2, 3, 5, or 8, rising with diff size and risk. Epics get no points.
- At sprint planning, propose cards whose blockers will be done, ordered by dependency, and sized to my review
  capacity. Once I agree, add them with `jira.py sprint` and assign them to me.
- Manual steps and decisions only I can make become cards labeled `needs-me`. Cards we know we need but have not
  detailed yet get `needs-refinement`.
