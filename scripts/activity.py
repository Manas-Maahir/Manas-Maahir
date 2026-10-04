"""Write a "what I'm working on" feed into the README from public GitHub events.

    python scripts/activity.py          (env: GITHUB_TOKEN optional, raises the rate limit)

Off-the-shelf activity actions only list issues/PRs, but most real work shows up as pushes,
so this groups recent pushes, new repos and newly public repos by repository.
Standard library only.
"""
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

USER = os.environ.get("GITHUB_USER", "Manas-Maahir")
SKIP = {f"{USER}/{USER}"}  # the profile repo itself is mostly bot commits
MAX_REPOS = 5
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!--START_SECTION:activity-->", "<!--END_SECTION:activity-->"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    events = get(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    repos = {}
    for e in events:
        name = e["repo"]["name"]
        if name in SKIP:
            continue
        # org repos count too (e.g. a lab's repo); an org mirror of one of my own repos does not
        short = name.split("/", 1)[1]
        if not name.startswith(f"{USER}/") and any(e2["repo"]["name"] == f"{USER}/{short}" for e2 in events):
            continue
        r = repos.setdefault(name, {"pushes": 0, "last": e["created_at"], "created": False, "public": False})
        r["last"] = max(r["last"], e["created_at"])  # the events feed is only roughly time-ordered
        if e["type"] == "PushEvent":
            r["pushes"] += 1
        elif e["type"] == "CreateEvent" and e["payload"].get("ref_type") == "repository":
            r["created"] = True
        elif e["type"] == "PublicEvent":
            r["public"] = True

    lines = []
    for name, r in sorted(repos.items(), key=lambda kv: kv[1]["last"], reverse=True)[:MAX_REPOS]:
        info = get(f"https://api.github.com/repos/{name}")
        desc = (info.get("description") or "").strip().rstrip(".")
        tags = []
        if r["created"]:
            tags.append("🆕 new repo")
        if r["public"]:
            tags.append("📢 just open-sourced")
        if r["pushes"]:
            tags.append(f"{r['pushes']} push{'es' if r['pushes'] != 1 else ''}")
        when = datetime.fromisoformat(r["last"].replace("Z", "+00:00")).strftime("%b %d").replace(" 0", " ")
        repo = name.split("/", 1)[1]
        lines.append(f"- **[{repo}](https://github.com/{name})**" + (f" — {desc}" if desc else "")
                     + f"  \n  <sub>{' · '.join(tags + ['last active ' + when])}</sub>")

    text = README.read_text(encoding="utf-8")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    body = "\n".join(lines) if lines else "_Nothing public in the last few weeks — probably deep in a private repo._"
    README.write_text(f"{head}{START}\n{body}\n{END}{tail}", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
