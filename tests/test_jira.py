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


def paragraph(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(nodes)}


def item(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "listItem", "content": list(nodes)}


def doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": list(nodes)}


def link(value: str, href: str) -> dict[str, Any]:
    return {"type": "text", "text": value, "marks": [{"type": "link", "attrs": {"href": href}}]}


class Recorder:
    def __init__(self, responses: dict[tuple[str, str], Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, Any]] = []

    def __call__(self, method: str, path: str, body: Any = None) -> Any:
        self.calls.append((method, path, body))
        return self.responses.get((method, path))


@pytest.mark.parametrize(
    ("markdown", "want"),
    [
        (
            "## Title",
            doc({"type": "heading", "attrs": {"level": 2}, "content": [text("Title")]}),
        ),
        (
            "one\ntwo",
            doc(paragraph(text("one two"))),
        ),
        (
            "- a\n- b",
            doc(
                {
                    "type": "bulletList",
                    "content": [item(paragraph(text("a"))), item(paragraph(text("b")))],
                }
            ),
        ),
        (
            "- a\n  - b",
            doc(
                {
                    "type": "bulletList",
                    "content": [
                        item(
                            paragraph(text("a")),
                            {"type": "bulletList", "content": [item(paragraph(text("b")))]},
                        )
                    ],
                }
            ),
        ),
        (
            "1. a\n2. b",
            doc(
                {
                    "type": "orderedList",
                    "content": [item(paragraph(text("a"))), item(paragraph(text("b")))],
                }
            ),
        ),
        (
            "```sh\nmake test\n```",
            doc({"type": "codeBlock", "attrs": {"language": "sh"}, "content": [text("make test")]}),
        ),
        (
            "- [ ] **Step 1:** x",
            doc(
                {
                    "type": "bulletList",
                    "content": [
                        item(paragraph(text("[ ] "), text("Step 1:", "strong"), text(" x")))
                    ],
                }
            ),
        ),
    ],
)
def test_markdown_to_adf(markdown: str, want: dict[str, Any]) -> None:
    # given
    jira = load_jira()

    # when
    got = jira.markdown_to_adf(markdown)

    # then
    assert got == want


@pytest.mark.parametrize(
    ("value", "want"),
    [
        ("run `make`", [text("run "), text("make", "code")]),
        ("**bold** end", [text("bold", "strong"), text(" end")]),
        ("~~gone~~", [text("gone", "strike")]),
        ("[a](https://x.y)", [link("a", "https://x.y")]),
        (
            "see https://x.y/z now",
            [text("see "), link("https://x.y/z", "https://x.y/z"), text(" now")],
        ),
        ("plain text", [text("plain text")]),
    ],
)
def test_inline_nodes(value: str, want: list[dict[str, Any]]) -> None:
    # given
    jira = load_jira()

    # when
    got = jira.inline_nodes(value)

    # then
    assert got == want


def test_link(monkeypatch: pytest.MonkeyPatch) -> None:
    # given
    jira = load_jira()
    fake = Recorder({})
    monkeypatch.setattr(jira, "api", fake)

    # when
    jira.link("HVD-1", "HVD-2")

    # then
    assert fake.calls == [
        (
            "POST",
            "/rest/api/3/issueLink",
            {
                "type": {"name": "Blocks"},
                "inwardIssue": {"key": "HVD-1"},
                "outwardIssue": {"key": "HVD-2"},
            },
        )
    ]


def test_create(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # given
    jira = load_jira()
    fake = Recorder({("POST", "/rest/api/3/issue"): {"key": "HVD-99"}})
    monkeypatch.setattr(jira, "api", fake)
    monkeypatch.setattr(jira, "story_points_field", lambda: "customfield_123")
    monkeypatch.setattr(jira, "load_env", lambda: {"JIRA_SITE": "https://site"})
    description = tmp_path / "card.md"
    description.write_text("hello")

    # when
    jira.create("HVD", "A card", str(description), parent="HVD-5", points=3, labels=["a", "b"])

    # then
    method, path, body = fake.calls[0]
    assert (method, path) == ("POST", "/rest/api/3/issue")
    fields = body["fields"]
    assert fields["project"] == {"key": "HVD"}
    assert fields["summary"] == "A card"
    assert fields["issuetype"]["name"] == "Task"
    assert fields["parent"]["key"] == "HVD-5"
    assert fields["labels"] == ["a", "b"]
    assert fields["customfield_123"] == 3
    assert fields["description"] == doc(paragraph(text("hello")))


@pytest.mark.parametrize(
    ("sprints", "want_calls", "want_exit"),
    [
        (
            [{"id": 7, "name": "Sprint 1"}],
            [
                ("GET", "/rest/agile/1.0/board?projectKeyOrId=HVD", None),
                ("GET", "/rest/agile/1.0/board/3/sprint?state=active", None),
                ("POST", "/rest/agile/1.0/sprint/7/issue", {"issues": ["HVD-1", "HVD-2"]}),
            ],
            None,
        ),
        (
            [],
            [
                ("GET", "/rest/agile/1.0/board?projectKeyOrId=HVD", None),
                ("GET", "/rest/agile/1.0/board/3/sprint?state=active", None),
            ],
            "no active sprint on board HVD board",
        ),
    ],
)
def test_sprint(
    monkeypatch: pytest.MonkeyPatch,
    sprints: list[dict[str, Any]],
    want_calls: list[tuple[str, str, Any]],
    want_exit: str | None,
) -> None:
    # given
    jira = load_jira()
    fake = Recorder(
        {
            ("GET", "/rest/agile/1.0/board?projectKeyOrId=HVD"): {
                "values": [{"id": 3, "name": "HVD board"}]
            },
            ("GET", "/rest/agile/1.0/board/3/sprint?state=active"): {"values": sprints},
        }
    )
    monkeypatch.setattr(jira, "api", fake)

    # when
    exit_code = None
    try:
        jira.sprint(["HVD-1", "HVD-2"])
    except SystemExit as e:
        exit_code = e.code

    # then
    assert fake.calls == want_calls
    assert exit_code == want_exit
