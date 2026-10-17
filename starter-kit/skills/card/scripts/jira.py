import argparse
import base64
import functools
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

USAGE = """
  python3 jira.py get KEY                 print card as markdown with status, parent, links
  python3 jira.py transition KEY STATUS   move card (e.g. "In Progress", "In Review")
  python3 jira.py comment KEY TEXT        add a plain-text comment (URLs become links)
  python3 jira.py assign KEY              assign to the token's user unless already theirs
  python3 jira.py strike-blockers KEY     strike Done blockers in the "Blocked by" line
  python3 jira.py create PROJECT SUMMARY --description-file PATH
                  [--parent KEY] [--points N] [--labels a,b]
                                          create a Task from a markdown file
  python3 jira.py edit KEY [--summary S] [--description-file PATH] [--points N] [--labels a,b]
                                          change only the given fields; --labels replaces all
  python3 jira.py link BLOCKER BLOCKED    mark BLOCKER as blocking BLOCKED
  python3 jira.py sprint KEY [KEY...]     add cards to the active sprint of the first card's board
"""

INLINE = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\*\*(?P<strong>.+?)\*\*"
    r"|~~(?P<strike>.+?)~~"
    r"|\[(?P<label>[^\]]+)\]\((?P<href>https?://[^)\s]+)\)"
    r"|(?P<url>https?://\S+)"
)
HEADING = re.compile(r"(#{1,4}) (.*)")
LIST_ITEM = re.compile(r"( *)([-*]|\d+\.) (.*)")


@functools.cache
def load_env() -> dict[str, str]:
    env = {}
    with open(os.path.expanduser("~/.config/jira/env")) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


def api(method: str, path: str, body: Any = None) -> Any:
    env = load_env()
    auth = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_TOKEN']}".encode()).decode()
    req = urllib.request.Request(
        env["JIRA_SITE"] + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        sys.exit(f"jira {method} {path} failed: {e.code} {e.read().decode()[:500]}")


def inline_nodes(text: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            nodes.append({"type": "text", "text": text[pos : m.start()]})
        if m["code"]:
            nodes.append({"type": "text", "text": m["code"], "marks": [{"type": "code"}]})
        elif m["strong"]:
            nodes.append({"type": "text", "text": m["strong"], "marks": [{"type": "strong"}]})
        elif m["strike"]:
            nodes.append({"type": "text", "text": m["strike"], "marks": [{"type": "strike"}]})
        else:
            href = m["href"] or m["url"]
            link = {"type": "link", "attrs": {"href": href}}
            nodes.append({"type": "text", "text": m["label"] or href, "marks": [link]})
        pos = m.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    return nodes


def list_node(items: list[tuple[int, bool, str]], start: int) -> tuple[dict[str, Any], int]:
    indent, ordered, _ = items[start]
    entries: list[dict[str, Any]] = []
    i = start
    while i < len(items) and items[i][0] >= indent:
        depth, kind, text = items[i]
        if depth > indent:
            nested, i = list_node(items, i)
            entries[-1]["content"].append(nested)
            continue
        if kind != ordered:
            break
        paragraph = {"type": "paragraph", "content": inline_nodes(text)}
        entries.append({"type": "listItem", "content": [paragraph]})
        i += 1
    return {"type": "orderedList" if ordered else "bulletList", "content": entries}, i


def markdown_to_adf(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    content: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.lstrip().startswith("```"):
            language = line.lstrip()[3:].strip()
            i += 1
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            block: dict[str, Any] = {"type": "codeBlock"}
            if language:
                block["attrs"] = {"language": language}
            if code:
                block["content"] = [{"type": "text", "text": "\n".join(code)}]
            content.append(block)
        elif m := HEADING.fullmatch(line):
            level = len(m[1])
            heading = {"type": "heading", "attrs": {"level": level}, "content": inline_nodes(m[2])}
            content.append(heading)
            i += 1
        elif LIST_ITEM.fullmatch(line):
            items: list[tuple[int, bool, str]] = []
            while i < len(lines) and lines[i].strip():
                m = LIST_ITEM.fullmatch(lines[i])
                if m:
                    items.append((len(m[1]), m[2][0].isdigit(), m[3]))
                elif lines[i].startswith(" ") and items:
                    depth, kind, prior = items[-1]
                    items[-1] = (depth, kind, prior + " " + lines[i].strip())
                else:
                    break
                i += 1
            start = 0
            while start < len(items):
                node, start = list_node(items, start)
                content.append(node)
        else:
            words = []
            while i < len(lines) and lines[i].strip():
                if words and (
                    HEADING.fullmatch(lines[i])
                    or LIST_ITEM.fullmatch(lines[i])
                    or lines[i].lstrip().startswith("```")
                ):
                    break
                words.append(lines[i].strip())
                i += 1
            content.append({"type": "paragraph", "content": inline_nodes(" ".join(words))})
    return {"type": "doc", "version": 1, "content": content}


def text_of(node: dict[str, Any]) -> str:
    if node.get("type") == "text":
        t = node.get("text", "")
        marks = {m["type"] for m in node.get("marks", [])}
        if "code" in marks:
            return f"`{t}`"
        if "strong" in marks:
            return f"**{t}**"
        if "strike" in marks:
            return f"~~{t}~~"
        return t
    if node.get("type") == "hardBreak":
        return "\n"
    return "".join(text_of(c) for c in node.get("content", []))


def render(node: dict[str, Any], indent: str = "") -> str:
    kind = node.get("type")
    content = node.get("content", [])
    if kind == "doc":
        return "\n\n".join(render(c) for c in content)
    if kind == "heading":
        return "#" * node["attrs"]["level"] + " " + text_of(node)
    if kind == "paragraph":
        return indent + text_of(node)
    if kind == "codeBlock":
        lang = (node.get("attrs") or {}).get("language") or ""
        return f"{indent}```{lang}\n{text_of(node)}\n{indent}```"
    if kind in ("bulletList", "orderedList"):
        lines = []
        for i, item in enumerate(content, 1):
            bullet = f"{i}. " if kind == "orderedList" else "- "
            parts = [render(c, indent + "   ") for c in item.get("content", [])]
            first = parts[0].lstrip() if parts else ""
            lines.append(indent + bullet + first + "".join("\n" + p for p in parts[1:]))
        return "\n".join(lines)
    return indent + text_of(node)


@functools.cache
def story_points_field() -> str:
    fields = {f["name"]: f["id"] for f in api("GET", "/rest/api/3/field")}
    for name in ("Story point estimate", "Story Points"):
        if name in fields:
            return fields[name]
    sys.exit("no story points field on this Jira site")


def get(key: str) -> None:
    points = story_points_field()
    fields = f"summary,status,description,parent,labels,issuelinks,{points},assignee"
    issue = api("GET", f"/rest/api/3/issue/{key}?fields={fields}")
    f = issue["fields"]
    print(f"# {key}: {f['summary']}")
    print(f"Status: {f['status']['name']}")
    if f.get("parent"):
        print(f"Epic: {f['parent']['key']} {f['parent']['fields']['summary']}")
    print(f"Assignee: {(f.get('assignee') or {}).get('displayName', 'unassigned')}")
    print(f"Labels: {', '.join(f.get('labels') or []) or 'none'}")
    print(f"Points: {f.get(points)}")
    blocked_by, blocks = [], []
    for link in f.get("issuelinks") or []:
        if link["type"]["name"] != "Blocks":
            continue
        if "inwardIssue" in link:
            other = link["inwardIssue"]
            blocked_by.append(f"{other['key']} ({other['fields']['status']['name']})")
        if "outwardIssue" in link:
            other = link["outwardIssue"]
            blocks.append(f"{other['key']} ({other['fields']['status']['name']})")
    print(f"Blocked by: {', '.join(blocked_by) or 'none'}")
    print(f"Blocks: {', '.join(blocks) or 'none'}")
    print(f"URL: {load_env()['JIRA_SITE']}/browse/{key}")
    print()
    print(render(f["description"]) if f.get("description") else "(no description)")


def transition(key: str, status: str) -> None:
    options = api("GET", f"/rest/api/3/issue/{key}/transitions")["transitions"]
    match = [t for t in options if t["to"]["name"].lower() == status.lower()]
    if not match:
        available = ", ".join(t["to"]["name"] for t in options)
        sys.exit(f"no transition to {status!r}; available: {available}")
    api("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": match[0]["id"]}})
    print(f"{key} -> {match[0]['to']['name']}")


def comment(key: str, text: str) -> None:
    nodes = []
    for part in re.split(r"(https?://\S+)", text):
        if not part:
            continue
        if part.startswith("http"):
            link = {"type": "link", "attrs": {"href": part}}
            nodes.append({"type": "text", "text": part, "marks": [link]})
        else:
            nodes.append({"type": "text", "text": part})
    paragraph = {"type": "paragraph", "content": nodes}
    body = {"body": {"type": "doc", "version": 1, "content": [paragraph]}}
    api("POST", f"/rest/api/3/issue/{key}/comment", body)
    print(f"commented on {key}")


def assign(key: str) -> None:
    me = api("GET", "/rest/api/3/myself")
    current = api("GET", f"/rest/api/3/issue/{key}?fields=assignee")["fields"].get("assignee")
    if current and current["accountId"] == me["accountId"]:
        print(f"{key} already assigned to {me['displayName']}")
        return
    api("PUT", f"/rest/api/3/issue/{key}/assignee", {"accountId": me["accountId"]})
    print(f"{key} assigned to {me['displayName']}")


def strike_text(node: dict[str, Any], keys: list[str]) -> None:
    out = []
    pattern = re.compile("(" + "|".join(re.escape(k) for k in keys) + ")(?![0-9])")
    for child in node.get("content", []):
        if child.get("type") != "text":
            strike_text(child, keys)
            out.append(child)
            continue
        marks = child.get("marks", [])
        if any(m["type"] == "strike" for m in marks):
            out.append(child)
            continue
        for i, part in enumerate(pattern.split(child["text"])):
            if not part:
                continue
            extra = [{"type": "strike"}] if i % 2 else []
            piece = {"type": "text", "text": part}
            if marks or extra:
                piece["marks"] = marks + extra
            out.append(piece)
    node["content"] = out


def strike_blockers(key: str) -> None:
    issue = api("GET", f"/rest/api/3/issue/{key}?fields=description,issuelinks")
    done = [
        link["inwardIssue"]["key"]
        for link in issue["fields"].get("issuelinks") or []
        if link["type"]["name"] == "Blocks"
        and "inwardIssue" in link
        and link["inwardIssue"]["fields"]["status"]["statusCategory"]["key"] == "done"
    ]
    description = issue["fields"].get("description")
    if not done or not description:
        print("nothing to strike")
        return
    for paragraph in description.get("content", []):
        if paragraph.get("type") != "paragraph":
            continue
        if text_of(paragraph).lstrip("*~").startswith("Blocked by"):
            strike_text(paragraph, done)
    api("PUT", f"/rest/api/3/issue/{key}", {"fields": {"description": description}})
    print(f"struck through {', '.join(done)} in {key}")


def card_fields(
    summary: str | None,
    description_file: str | None,
    points: float | None,
    labels: list[str] | None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if summary is not None:
        fields["summary"] = summary
    if description_file is not None:
        with open(description_file) as f:
            fields["description"] = markdown_to_adf(f.read())
    if points is not None:
        fields[story_points_field()] = points
    if labels is not None:
        fields["labels"] = labels
    return fields


def create(
    project: str,
    summary: str,
    description_file: str,
    parent: str | None = None,
    points: float | None = None,
    labels: list[str] | None = None,
) -> None:
    fields = card_fields(summary, description_file, points, labels)
    fields["project"] = {"key": project}
    fields["issuetype"] = {"name": "Task"}
    if parent is not None:
        fields["parent"] = {"key": parent}
    key = api("POST", "/rest/api/3/issue", {"fields": fields})["key"]
    print(f"created {key}")
    print(f"{load_env()['JIRA_SITE']}/browse/{key}")


def edit(
    key: str,
    summary: str | None = None,
    description_file: str | None = None,
    points: float | None = None,
    labels: list[str] | None = None,
) -> None:
    fields = card_fields(summary, description_file, points, labels)
    if not fields:
        sys.exit(
            "nothing to edit; pass at least one of --summary, --description-file, "
            "--points, --labels"
        )
    api("PUT", f"/rest/api/3/issue/{key}", {"fields": fields})
    print(f"edited {key}: {', '.join(fields)}")


def link(blocker: str, blocked: str) -> None:
    body = {
        "type": {"name": "Blocks"},
        "inwardIssue": {"key": blocker},
        "outwardIssue": {"key": blocked},
    }
    api("POST", "/rest/api/3/issueLink", body)
    print(f"{blocker} blocks {blocked}")


def sprint(keys: list[str]) -> None:
    project = keys[0].split("-")[0]
    boards = api("GET", f"/rest/agile/1.0/board?projectKeyOrId={project}")["values"]
    if not boards:
        sys.exit(f"no board for project {project}")
    board = boards[0]
    active = api("GET", f"/rest/agile/1.0/board/{board['id']}/sprint?state=active")["values"]
    if not active:
        sys.exit(f"no active sprint on board {board['name']}")
    api("POST", f"/rest/agile/1.0/sprint/{active[0]['id']}/issue", {"issues": keys})
    print(f"added {', '.join(keys)} to {active[0]['name']}")


def issue_key(text: str) -> str:
    if not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", text):
        raise argparse.ArgumentTypeError(f"not a card key: {text}")
    return text


def label_list(text: str) -> list[str]:
    return [label for label in text.split(",") if label]


def main() -> None:
    parser = argparse.ArgumentParser(prog="jira.py", usage=USAGE)
    commands = parser.add_subparsers(dest="command", required=True, prog="jira.py")

    for name in ("get", "assign", "strike-blockers"):
        commands.add_parser(name).add_argument("key", type=issue_key)

    p = commands.add_parser("transition")
    p.add_argument("key", type=issue_key)
    p.add_argument("status")

    p = commands.add_parser("comment")
    p.add_argument("key", type=issue_key)
    p.add_argument("text")

    p = commands.add_parser("create")
    p.add_argument("project")
    p.add_argument("summary")
    p.add_argument("--description-file", required=True)
    p.add_argument("--parent", type=issue_key)
    p.add_argument("--points", type=float)
    p.add_argument("--labels", type=label_list)

    p = commands.add_parser("edit")
    p.add_argument("key", type=issue_key)
    p.add_argument("--summary")
    p.add_argument("--description-file")
    p.add_argument("--points", type=float)
    p.add_argument("--labels", type=label_list)

    p = commands.add_parser("link")
    p.add_argument("blocker", type=issue_key)
    p.add_argument("blocked", type=issue_key)

    p = commands.add_parser("sprint")
    p.add_argument("keys", type=issue_key, nargs="+")

    args = parser.parse_args()
    if args.command == "get":
        get(args.key)
    elif args.command == "transition":
        transition(args.key, args.status)
    elif args.command == "comment":
        comment(args.key, args.text)
    elif args.command == "assign":
        assign(args.key)
    elif args.command == "strike-blockers":
        strike_blockers(args.key)
    elif args.command == "create":
        create(
            args.project,
            args.summary,
            args.description_file,
            parent=args.parent,
            points=args.points,
            labels=args.labels,
        )
    elif args.command == "edit":
        edit(
            args.key,
            summary=args.summary,
            description_file=args.description_file,
            points=args.points,
            labels=args.labels,
        )
    elif args.command == "link":
        link(args.blocker, args.blocked)
    elif args.command == "sprint":
        sprint(args.keys)


if __name__ == "__main__":
    main()
