import json
import os
import subprocess
from pathlib import Path

KIT = Path(__file__).parent.parent / "starter-kit"


def test_settings() -> None:
    # given
    path = KIT / "settings.json"

    # when
    settings = json.loads(path.read_text())

    # then
    assert settings["model"] == "sonnet"
    deny = settings["permissions"]["deny"]
    for rule in [
        "Bash(sudo *)",
        "Bash(rm -rf *)",
        "Bash(git push --force*)",
        "Read(~/.ssh/**)",
        "Edit(~/.zshrc)",
        "Edit(~/.bash_profile)",
    ]:
        assert rule in deny
    stop_commands = [h["command"] for group in settings["hooks"]["Stop"] for h in group["hooks"]]
    assert "printf '\\a'" in stop_commands
    assert settings["statusLine"]["command"] == "~/.claude/statusline.sh"
    assert settings["enabledPlugins"] == {"superpowers@claude-plugins-official": True}
    assert "allow" not in settings["permissions"]


def test_statusline() -> None:
    # given
    path = KIT / "statusline.sh"

    # when
    result = subprocess.run(["bash", "-n", str(path)], capture_output=True)

    # then
    assert os.access(path, os.X_OK)
    assert result.returncode == 0


def test_claude_md() -> None:
    # given
    path = KIT / "CLAUDE.md"

    # when
    text = path.read_text()

    # then
    for want in ["~/code/wts/", "## Planning work", "needs-me", "jira.py"]:
        assert want in text
