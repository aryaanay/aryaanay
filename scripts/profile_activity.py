"""Refresh the activity section using GitHub's public repository and event data."""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

OWNER = "aryaanay"
PROFILE = f"{OWNER}/{OWNER}"
START = "<!-- activity:start -->"
END = "<!-- activity:end -->"
REPO = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+")
DISCUSSION = re.compile(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/discussions/[1-9][0-9]*")


# Only public metadata from these featured repositories enters the timeline.
FEATURED = {
    "build-review-release": "Codex skill",
    "Quantitative-Finance-Model-Development-Portfolio": "Quant notebooks",
    "ai-narrative-reality-gap": "AI research",
    "commhub": "CommUHub",
}


def month_index(date):
    return date.year * 12 + date.month - 1


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def render_timeline(repos, now):
    public = {repo["full_name"].lower(): repo for repo in repos if repo.get("private") is False}
    months = [month_index(now) - 11 + column for column in range(12)]
    labels = []
    marks = []
    for column, month in enumerate(months):
        x = 191 + 31 * column
        year, index = divmod(month, 12)
        date = datetime(year, index + 1, 1)
        if column in (0, 3, 6, 9, 11):
            labels.append(f'<text x="{x}" y="22" text-anchor="middle">{date:%b}</text>')
    for row, (slug, label) in enumerate(FEATURED.items()):
        y = 50 + 32 * row
        labels.append(f'<text x="7" y="{y + 5}">{label}</text>')
        full_name = f"{OWNER}/{slug}"
        repo = public.get(full_name.lower())
        created = month_index(timestamp(repo["created_at"])) if repo else None
        releases = request(f"repos/{full_name}/releases?per_page=100") if repo else []
        release_months = {
            month_index(timestamp(release["published_at"]))
            for release in releases
            if not release["draft"] and not release["prerelease"] and release.get("published_at")
        }
        for column, month in enumerate(months):
            x = 191 + 31 * column
            if month in release_months:
                marks.append(f'<path class="release" d="M{x} {y-6}l6 6-6 6-6-6z"/>')
            elif month == created:
                marks.append(f'<circle class="opened" cx="{x}" cy="{y}" r="5"/>')
            else:
                marks.append(f'<circle class="quiet" cx="{x}" cy="{y}" r="2"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 552 164" width="552" height="164" role="img">
<title>Public repository milestones</title>
<style>
/* The copper accent matches the profile's Lorenz attractor. */
:root {{ --ink:#3b4b59; --quiet:#9eaab4; --copper:#a54431; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --ink:#d1dbe5; --quiet:#758696; --copper:#ff936c; }}
}}
text {{ fill:var(--ink); font:17px system-ui,sans-serif; }}
.quiet {{ fill:var(--quiet); }}
.opened {{ fill:var(--copper); }}
.release {{ fill:var(--copper); }}
</style>
{chr(10).join(labels)}
{chr(10).join(marks)}
</svg>
'''


def request(path, query=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "aryaanay-profile"}
    if query is not None:
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
        headers["Content-Type"] = "application/json"
    data = json.dumps({"query": query}).encode() if query is not None else None
    with urlopen(Request(f"https://api.github.com/{path}", data, headers), timeout=20) as response:
        return json.load(response)


def render(repos, events, discussions, now):
    public = {
        repo["full_name"]: repo["default_branch"] for repo in repos
        if repo.get("private") is False and REPO.fullmatch(repo["full_name"])
        and repo["full_name"].lower().startswith(f"{OWNER}/")
        and repo["full_name"].lower() != PROFILE
    }
    rows = [
        (repo["created_at"], "Opened repository", repo["full_name"], "")
        for repo in repos if repo["full_name"] in public and not repo["fork"]
    ]
    for event in events:
        name = event["repo"]["name"]
        if not event.get("public") or name not in public:
            continue
        payload = event["payload"]
        kind = event["type"]
        if kind == "ReleaseEvent" and payload.get("action") == "published":
            rows.append((event["created_at"], "Published release", name, "/releases"))
        elif kind == "PushEvent" and payload.get("ref") == "refs/heads/" + public[name]:
            rows.append((event["created_at"], "Updated code", name, "/commits"))
        elif kind in {"PullRequestEvent", "IssuesEvent"} and payload.get("action") == "opened":
            key, label, route = (
                ("pull_request", "Opened pull request", "pull") if kind == "PullRequestEvent"
                else ("issue", "Opened issue", "issues")
            )
            number = payload.get(key, {}).get("number")
            if type(number) is int and number > 0:
                rows.append((event["created_at"], label, name, f"/{route}/{number}"))

    for post in discussions:
        if post.get("repository", {}).get("isPrivate") is False and DISCUSSION.fullmatch(post["url"]):
            name, number = post["url"].removeprefix("https://github.com/").split("/discussions/")
            if name != PROFILE:
                rows.append((post["createdAt"], "Posted discussion", name, f"/discussions/{number}"))

    links = {}
    cutoff = now - timedelta(days=90)
    for date, label, name, suffix in sorted(rows, reverse=True):
        timestamp = datetime.fromisoformat(date.replace("Z", "+00:00"))
        if cutoff <= timestamp <= now:
            url = f"https://github.com/{name}{suffix}"
            links.setdefault(url, f"- **{timestamp:%b %d, %Y}** — {label} in [{name.split('/')[1]}]({url})")
        if len(links) == 6:
            break
    return "\n".join(links.values()) or "No public activity in the past 90 days."


def refresh(readme, activity):
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise ValueError("Expected exactly one ordered pair of activity markers")
    before, _, tail = readme.partition(START)
    _, _, after = tail.partition(END)
    return f"{before}{START}\n{activity}\n{END}{after}"


if __name__ == "__main__":
    repos = request(f"users/{OWNER}/repos?type=owner&sort=updated&per_page=100")
    events = request(f"users/{OWNER}/events/public?per_page=100")
    posts = []
    try:
        result = request("graphql", """
            { search(query: "author:aryaanay is:public sort:created-desc", type: DISCUSSION, first: 10) {
                nodes { ... on Discussion { createdAt url repository { isPrivate } } }
            } }
        """)
        if result.get("errors"):
            raise ValueError("Discussion search returned errors")
        posts = result["data"]["search"]["nodes"]
    except (URLError, KeyError, ValueError):
        print("::warning::Public discussion search unavailable. Updating repository activity only.")

    if isinstance(posts, list):
        path = Path("README.md")
        old = path.read_text(encoding="utf-8")
        new = refresh(old, render(repos, events, posts, datetime.now(timezone.utc)))
        if new != old:
            path.write_text(new, encoding="utf-8", newline="\n")

    try:
        timeline = render_timeline(repos, datetime.now(timezone.utc))
    except (URLError, KeyError, ValueError):
        print("::warning::Public release data unavailable. Keeping the last timeline.")
    else:
        Path("project-timeline.svg").write_text(timeline, encoding="utf-8", newline="\n")
