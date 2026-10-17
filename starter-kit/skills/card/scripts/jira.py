import base64
import functools
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

USAGE = """usage:
  python3 jira.py get KEY                 print card as markdown with status, parent, links
  python3 jira.py transition KEY STATUS   move card (e.g. "In Progress", "In Review")
  python3 jira.py comment KEY TEXT        add a plain-text comment (URLs become links)
  python3 jira.py assign KEY              assign to the token's user unless already theirs
  python3 jira.py strike-blockers KEY     strike Done blockers in the "Blocked by" line
"""


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


def get(key: str) -> None:
    fields = "summary,status,description,parent,labels,issuelinks,customfield_10016,assignee"
    issue = api("GET", f"/rest/api/3/issue/{key}?fields={fields}")
    f = issue["fields"]
    print(f"# {key}: {f['summary']}")
    print(f"Status: {f['status']['name']}")
    if f.get("parent"):
        print(f"Epic: {f['parent']['key']} {f['parent']['fields']['summary']}")
    print(f"Assignee: {(f.get('assignee') or {}).get('displayName', 'unassigned')}")
    print(f"Labels: {', '.join(f.get('labels') or []) or 'none'}")
    print(f"Points: {f.get('customfield_10016')}")
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


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2 or not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", args[1]):
        sys.exit(USAGE)
    cmd, key = args[0], args[1]
    if cmd == "get" and len(args) == 2:
        get(key)
    elif cmd == "transition" and len(args) == 3:
        transition(key, args[2])
    elif cmd == "assign" and len(args) == 2:
        assign(key)
    elif cmd == "strike-blockers" and len(args) == 2:
        strike_blockers(key)
    elif cmd == "comment" and len(args) == 3:
        comment(key, args[2])
    else:
        sys.exit(USAGE)


if __name__ == "__main__":
    main()
