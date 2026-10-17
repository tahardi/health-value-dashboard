import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "starter-kit" / "skills" / "card" / "scripts" / "jira.py"


def load_jira() -> ModuleType:
    spec = importlib.util.spec_from_file_location("jira", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text(value: str, *marks: str) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": value}
    if marks:
        node["marks"] = [{"type": m} for m in marks]
    return node


@pytest.mark.parametrize(
    ("node", "want"),
    [
        (text("x"), "x"),
        (text("x", "strike"), "~~x~~"),
        (text("x", "code"), "`x`"),
        (text("x", "strong"), "**x**"),
        ({"type": "hardBreak"}, "\n"),
        ({"type": "paragraph", "content": [text("a "), text("b", "strike")]}, "a ~~b~~"),
    ],
)
def test_text_of(node: dict[str, Any], want: str) -> None:
    # given
    jira = load_jira()

    # when
    got = jira.text_of(node)

    # then
    assert got == want


@pytest.mark.parametrize(
    ("content", "want"),
    [
        (
            [text("Blocked by: HVD-3.")],
            [text("Blocked by: "), text("HVD-3", "strike"), text(".")],
        ),
        (
            [text("Blocked by: HVD-30.")],
            [text("Blocked by: HVD-30.")],
        ),
        (
            [text("Blocked by: HVD-3", "strong")],
            [text("Blocked by: ", "strong"), text("HVD-3", "strong", "strike")],
        ),
        (
            [text("HVD-3", "strike")],
            [text("HVD-3", "strike")],
        ),
    ],
)
def test_strike_text(content: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    # given
    jira = load_jira()
    node = {"type": "paragraph", "content": content}

    # when
    jira.strike_text(node, ["HVD-3"])

    # then
    assert node["content"] == want
