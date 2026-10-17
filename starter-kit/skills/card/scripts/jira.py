import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

USAGE = """usage:
  python3 jira.py get KEY                 print card as markdown with status, parent, links
  python3 jira.py transition KEY STATUS   move card (e.g. "In Progress", "In Review")
  python3 jira.py comment KEY TEXT        add a plain-text comment (URLs become links)
"""


def load_env():
    env = {}
    with open(os.path.expanduser("~/.config/jira/env")) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


ENV = load_env()
AUTH = base64.b64encode(f"{ENV['JIRA_EMAIL']}:{ENV['JIRA_TOKEN']}".encode()).decode()


def api(method, path, body=None):
    req = urllib.request.Request(
        ENV["JIRA_SITE"] + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        sys.exit(f"jira {method} {path} failed: {e.code} {e.read().decode()[:500]}")


def text_of(node):
    if node.get("type") == "text":
        t = node.get("text", "")
        marks = {m["type"] for m in node.get("marks", [])}
        if "code" in marks:
            return f"`{t}`"
        if "strong" in marks:
            return f"**{t}**"
        return t
    if node.get("type") == "hardBreak":
        return "\n"
    return "".join(text_of(c) for c in node.get("content", []))


def render(node, indent=""):
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


def get(key):
    fields = "summary,status,description,parent,labels,issuelinks,customfield_10016"
    issue = api("GET", f"/rest/api/3/issue/{key}?fields={fields}")
    f = issue["fields"]
    print(f"# {key}: {f['summary']}")
    print(f"Status: {f['status']['name']}")
    if f.get("parent"):
        print(f"Epic: {f['parent']['key']} {f['parent']['fields']['summary']}")
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
    print(f"URL: {ENV['JIRA_SITE']}/browse/{key}")
    print()
    print(render(f["description"]) if f.get("description") else "(no description)")


def transition(key, status):
    options = api("GET", f"/rest/api/3/issue/{key}/transitions")["transitions"]
    match = [t for t in options if t["to"]["name"].lower() == status.lower()]
    if not match:
        sys.exit(f"no transition to {status!r}; available: {', '.join(t['to']['name'] for t in options)}")
    api("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": match[0]["id"]}})
    print(f"{key} -> {match[0]['to']['name']}")


def comment(key, text):
    nodes = []
    for part in re.split(r"(https?://\S+)", text):
        if not part:
            continue
        if part.startswith("http"):
            nodes.append({"type": "text", "text": part, "marks": [{"type": "link", "attrs": {"href": part}}]})
        else:
            nodes.append({"type": "text", "text": part})
    body = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": nodes}]}}
    api("POST", f"/rest/api/3/issue/{key}/comment", body)
    print(f"commented on {key}")


def main():
    args = sys.argv[1:]
    if len(args) < 2 or not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", args[1]):
        sys.exit(USAGE)
    cmd, key = args[0], args[1]
    if cmd == "get" and len(args) == 2:
        get(key)
    elif cmd == "transition" and len(args) == 3:
        transition(key, args[2])
    elif cmd == "comment" and len(args) == 3:
        comment(key, args[2])
    else:
        sys.exit(USAGE)


main()
