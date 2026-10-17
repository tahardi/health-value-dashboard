# The tour files are instructions Claude follows, so a stale reference sends the learner to a
# command or file that no longer exists. These tests do not judge the writing. They pull the
# references out of the markdown and check each one against the repo:
# - test_make_targets: every `make <target>` in the tour names a target defined in the Makefile.
# - test_links: every relative markdown link points to a file that exists.
# - test_parts: TOUR.md links all four part files.
# A renamed make target or a moved file fails here instead of mid-tour.
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PARTS = ["tour/1-setup.md", "tour/2-tour.md", "tour/3-build.md", "tour/4-design.md"]
FILES = ["TOUR.md", *PARTS]


def make_targets(text: str) -> list[str]:
    commands = re.findall(r"`make ([^`]+)`", text)
    commands += re.findall(r"^\s*make ([^\n]+)$", text, re.MULTILINE)
    return [
        word for command in commands for word in command.split() if re.fullmatch(r"[\w-]+", word)
    ]


def relative_links(text: str) -> list[str]:
    links = re.findall(r"\]\(([^)\s]+)\)", text)
    return [link.split("#")[0] for link in links if not re.match(r"[a-z]+:|#", link)]


@pytest.mark.parametrize("name", FILES)
def test_make_targets(name: str) -> None:
    # given
    defined = set(re.findall(r"^([\w-]+):", (ROOT / "Makefile").read_text(), re.MULTILINE))

    # when
    used = make_targets((ROOT / name).read_text())

    # then
    assert set(used) <= defined


@pytest.mark.parametrize("name", FILES)
def test_links(name: str) -> None:
    # given
    path = ROOT / name

    # when
    links = relative_links(path.read_text())

    # then
    for link in links:
        assert (path.parent / link).exists(), link


def test_parts() -> None:
    # given
    path = ROOT / "TOUR.md"

    # when
    links = relative_links(path.read_text())

    # then
    assert set(PARTS) <= set(links)
