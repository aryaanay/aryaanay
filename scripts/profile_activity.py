"""Refresh the activity section using GitHub's public repository and event data."""

import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = "aryaanay"
PROFILE = f"{OWNER}/{OWNER}"
START = "<!-- activity:start -->"
END = "<!-- activity:end -->"
LANGUAGES_START = "<!-- languages:start -->"
LANGUAGES_END = "<!-- languages:end -->"
REPO = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+")
DISCUSSION = re.compile(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/discussions/[1-9][0-9]*")


# Count only the featured repositories that are public at refresh time.
FEATURED = (
    "build-review-release",
    "Quantitative-Finance-Model-Development-Portfolio",
    "ai-narrative-reality-gap",
    "commhub",
)


def render_languages(repos):
    public = {repo["full_name"].lower() for repo in repos if repo.get("private") is False}
    counts = Counter()
    for slug in FEATURED:
        name = f"{OWNER}/{slug}"
        if name.lower() not in public:
            continue
        languages = request(f"repos/{name}/languages")
        if not isinstance(languages, dict) or any(
            type(amount) is not int or amount < 0 for amount in languages.values()
        ):
            raise ValueError("Unexpected language data")
        counts.update({name: amount for name, amount in languages.items() if amount})

    total = counts.total()
    if not total:
        return "GitHub has no language data for the featured repositories.", language_matrix([], 0)
    ranked = sorted(counts.items(), key=lambda row: (-row[1], row[0].lower()))
    rows = ranked[:5]
    if len(ranked) > 5:
        rows.append(("Other", sum(amount for _, amount in ranked[5:])))

    table = ["| Language | Share |", "| :--- | ---: |"]
    for name, amount in rows:
        label = escape(" ".join(name.split())).replace("|", "&#124;").replace("[", "&#91;")
        share = f"{amount / total:.1%}" if amount / total >= 0.001 else "&lt;0.1%"
        table.append(f"| {label} | {share} |")
    return "\n".join(table), language_matrix(rows, total)


def language_matrix(rows, total):
    """Draw the same shares as the text table, quantized to twenty dots."""
    content = []
    for row, (name, amount) in enumerate(rows):
        y = 20 + row * 30
        label = escape("Jupyter" if name == "Jupyter Notebook" else " ".join(name.split()))
        share = f"{amount / total:.1%}" if amount / total >= 0.001 else "&lt;0.1%"
        content.append(f'<text x="6" y="{y + 6}">{label}</text>')
        content.append(f'<text x="492" y="{y + 6}" text-anchor="end">{share}</text>')
        for column in range(20):
            x = 164 + 12 * column
            dot = f'cx="{x}" cy="{y}" r="3.4"'
            content.append(f'<circle class="track" {dot}/>')
            portion = min(1, max(0, 20 * amount / total - column))
            if portion:
                content.append(f'<circle class="lit" {dot} opacity="{max(0.30, portion):.2f}"/>')
                if portion >= 0.5:
                    content.append(f'<circle class="sweep" {dot} style="animation-delay:{column * 0.07:.2f}s"/>')
    if not content:
        content.append('<text x="6" y="26">No detected language data</text>')
    height = max(38, len(rows) * 30 + 8)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="{height}" viewBox="0 0 500 {height}">
<title>Language shares for featured public repositories</title>
<style>
:root {{ --ink:#364451; --track:#abb6c0; --lit:#a54431; --sweep:#d96b46; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --ink:#d1dbe5; --track:#485665; --lit:#e78766; --sweep:#ffd3a9; }}
}}
text {{ fill:var(--ink); font:20px system-ui,sans-serif; }}
.track {{ fill:var(--track); }}
.lit {{ fill:var(--lit); }}
.sweep {{ fill:var(--sweep); opacity:0; }}
@media (prefers-reduced-motion:no-preference) {{
  .sweep {{ animation:scan 7s ease-in-out infinite; }}
}}
@keyframes scan {{
  0%, 12%, 100% {{ opacity:0; }}
  5% {{ opacity:1; }}
}}
</style>
{chr(10).join(content)}
</svg>
'''


def stack_display(readme):
    header, found, body = readme.partition("\n## Tech stack\n")
    if not found:
        raise ValueError("Tech stack heading missing")
    section = body.split("\n### Languages\n", 1)[0]
    rows = re.findall(r"^\*\*[^*\n]+\*\* · (.+)$", section, re.MULTILINE)
    names = list(dict.fromkeys(name.strip() for row in rows for name in row.split(",") if name.strip()))
    aliases = {"c++": "cplusplus", "c#": "csharp", ".net": "dotnet"}
    masks = []
    slides = []
    for name in names:
        normalized = name.lower()
        slug = aliases.get(normalized, re.sub(r"[^a-z0-9]", "", normalized.replace(".", "dot")))
        if not slug:
            continue
        url = f"https://raw.githubusercontent.com/simple-icons/simple-icons/16.38.1/icons/{slug}.svg"
        try:
            with urlopen(Request(url, headers={"User-Agent": "aryaanay-profile"}), timeout=6) as icon:
                raw = icon.read(32769).decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        geometry = re.fullmatch(
            r'<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
            r'<title>[^<]*</title><path d="([MmZzLlHhVvCcSsQqTtAaEe0-9.,+\-\s]+)"/></svg>',
            raw.strip(),
        )
        if geometry is None:
            raise ValueError(f"Unexpected geometry for {slug}")
        index = len(masks)
        masks.append(f'<mask id="logo-{index}"><path d="{geometry[1]}" fill="white" '
                     f'transform="translate(14 7) scale(3.5)"/></mask>')
        slides.append(f'<rect class="logo" style="--delay:{index * 3}s" width="112" height="98" '
                      f'fill="url(#dots)" mask="url(#logo-{index})"/>')
    if not slides:
        raise ValueError("No logos found for the technologies listed")
    period = len(slides) * 3
    slot = 100 / len(slides)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="112" height="98" viewBox="0 0 112 98">
<title>Rotating tech stack logos</title>
<!-- Logo silhouettes from Simple Icons 16.38.1. Trademarks belong to their respective owners. -->
<style>
:root {{ --copper:#a54431; }}
@media (prefers-color-scheme:dark) {{ :root {{ --copper:#ff936c; }} }}
.dot {{ fill:var(--copper); }}
.logo {{ opacity:0; }}
.logo:first-of-type {{ opacity:1; }}
@media (prefers-reduced-motion:no-preference) {{
  .logo {{ animation:cycle {period}s linear calc(var(--delay) - {period}s) infinite; }}
}}
@keyframes cycle {{
  0% {{ opacity:0; }}
  {slot * .10:.5f}%, {slot * .87:.5f}% {{ opacity:1; }}
  {slot:.5f}%, 100% {{ opacity:0; }}
}}
</style>
<defs>
  <pattern id="dots" width="3.3" height="3.3" patternUnits="userSpaceOnUse">
    <circle class="dot" cx="1.65" cy="1.65" r="1.2"/>
  </pattern>
  {chr(10).join(masks)}
</defs>
{chr(10).join(slides)}
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


def refresh(readme, content, start=START, end=END):
    if readme.count(start) != 1 or readme.count(end) != 1 or readme.index(start) > readme.index(end):
        raise ValueError("Expected exactly one ordered pair of profile markers")
    before, _, tail = readme.partition(start)
    _, _, after = tail.partition(end)
    return f"{before}{start}\n{content}\n{end}{after}"


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

    path = Path("README.md")
    old = path.read_text(encoding="utf-8")
    new = refresh(old, render(repos, events, posts, datetime.now(timezone.utc)))

    if LANGUAGES_START in new or LANGUAGES_END in new:
        try:
            languages, matrix = render_languages(repos)
        except (URLError, ValueError):
            print("::warning::Public language data unavailable. Keeping the previous breakdown.")
        else:
            new = refresh(new, languages, LANGUAGES_START, LANGUAGES_END)
            Path("language-matrix.svg").write_text(matrix, encoding="utf-8", newline="\n")

    try:
        stack = stack_display(new)
    except (URLError, ValueError):
        print("::warning::Tech stack logos unavailable. Keeping the previous display.")
    else:
        Path("tech-stack-matrix.svg").write_text(stack, encoding="utf-8", newline="\n")

    if new != old:
        path.write_text(new, encoding="utf-8", newline="\n")
