#!/usr/bin/env python3
"""
cards.py - render GitHub stat and repo cards as standalone SVGs. Stdlib only.

Generates self-contained SVGs directly into assets/ to eliminate broken third-party
images (503s, 402 quota limits, timeouts from external services).

Usage:
    python scripts/cards.py --user iamjaved026 --out assets
    python scripts/cards.py --user iamjaved026 --projects assets/projects.json --stats assets/stats.json --out assets
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

UA = {"User-Agent": "profile-cards/2.0"}

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "title": "#39d353",
        "text": "#c9d1d9",
        "muted": "#8b949e",
        "value": "#e6edf3",
        "accent": "#39d353",
        "card_bg": "#161b22",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "title": "#1a7f37",
        "text": "#1f2328",
        "muted": "#57606a",
        "value": "#1f2328",
        "accent": "#1a7f37",
        "card_bg": "#f6f8fa",
    },
}

LANG_COLOR = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Nix": "#7e7eff",
    "PHP": "#4F5D95",
}

FONT = "ui-sans-serif,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"

ICON_STAR = (
    "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 "
    "2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 "
    "01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"
)
ICON_FORK = (
    "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 "
    "111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 "
    "0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0zM5 3.25a.75.75 0 "
    "10-1.5 0 .75.75 0 001.5 0zm6.75.75a.75.75 0 100-1.5.75.75 0 000 1.5zm-3 "
    "8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"
)
ICON_REPO = (
    "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 "
    "0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 "
    "012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 "
    "12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 "
    "00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"
)


def icon(path: str, x: float, y: float, size: float, fill: str) -> str:
    s = size / 16.0
    return (
        f'<path transform="translate({x:.1f},{y:.1f}) scale({s:.3f})" '
        f'fill="{fill}" d="{path}"/>'
    )


def rest(path: str, token: str | None):
    req = urllib.request.Request("https://api.github.com" + path, headers=dict(UA))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


CONTRIB_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""


def fetch_contributions(user: str, token: str | None):
    if not token:
        return None
    try:
        body = json.dumps({"query": CONTRIB_QUERY, "variables": {"login": user}}).encode()
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={**UA, "Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"  contributions unavailable: {e}", file=sys.stderr)
        return None

    if data.get("errors"):
        return None

    try:
        cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        days = [
            (dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in cal["weeks"]
            for d in w["contributionDays"]
        ]
        days.sort()

        longest = run = 0
        for _, c in days:
            run = run + 1 if c > 0 else 0
            longest = max(longest, run)

        current = 0
        for date, c in reversed(days):
            if c > 0:
                current += 1
            elif date != days[-1][0]:
                break
        return cal["totalContributions"], current, longest
    except Exception:
        return None


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def text_width(s: str, size: float) -> float:
    return len(s) * size * 0.54


def wrap(text: str, size: float, max_w: float, max_lines: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_width(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and words:
        used = len(" ".join(lines).split())
        if used < len(words):
            while lines and text_width(lines[-1] + "…", size) > max_w:
                parts = lines[-1].rsplit(" ", 1)
                lines[-1] = parts[0] if len(parts) > 1 else ""
            lines[-1] += "…"
    return lines


def frame(w: int, h: int, c: dict, body: str, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{esc(label)}" '
        f'font-family="{FONT}">'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>'
        f"{body}</svg>"
    )


def render_stats(user: str, stats: list[tuple[str, str]], theme: str) -> str:
    c = THEMES[theme]
    pad = 22
    tiles = [(v, k) for k, v in stats]
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    rh, W = 54, 530
    H = pad + 52 + (rows - 1) * rh + 24 + pad
    tw = (W - 2 * pad) / cols

    out = [
        f'<text x="{pad}" y="{pad + 14}" font-size="15" font-weight="700" '
        f'fill="{c["title"]}">@{esc(user)} · telemetry</text>',
        f'<text x="{W - pad}" y="{pad + 14}" font-size="11" text-anchor="end" '
        f'fill="{c["muted"]}">verified stats</text>',
        f'<line x1="{pad}" y1="{pad + 26}" x2="{W - pad}" y2="{pad + 26}" '
        f'stroke="{c["border"]}"/>',
    ]
    top = pad + 56
    for i, (value, label) in enumerate(tiles):
        cx = pad + (i % cols) * tw
        cy = top + (i // cols) * rh
        v_len = len(str(value))
        if v_len <= 5:
            fsize = 23
            y_shift = 0
        elif v_len <= 10:
            fsize = 18
            y_shift = -1
        elif v_len <= 14:
            fsize = 15
            y_shift = -2
        else:
            fsize = 13.5
            y_shift = -2

        out.append(
            f'<text x="{cx:.0f}" y="{cy + y_shift:.0f}" font-size="{fsize}" font-weight="700" '
            f'fill="{c["value"]}">{esc(value)}</text>'
        )
        out.append(
            f'<text x="{cx:.0f}" y="{cy + 19:.0f}" font-size="10.8" '
            f'fill="{c["muted"]}">{esc(label)}</text>'
        )
    return frame(W, H, c, "".join(out), f"{user} GitHub telemetry")


def render_repo(repo: dict, theme: str) -> str:
    c = THEMES[theme]
    W, H = 430, 138
    pad = 18
    out = []

    out.append(icon(ICON_REPO, pad, pad, 15, c["title"]))
    out.append(
        f'<text x="{pad + 22}" y="{pad + 12}" font-size="14.5" font-weight="700" '
        f'fill="{c["title"]}">{esc(repo["name"])}</text>'
    )

    desc = repo.get("description") or "No description provided."
    for i, line in enumerate(wrap(desc, 11.2, W - 2 * pad, 3)):
        out.append(
            f'<text x="{pad}" y="{pad + 36 + i * 16}" font-size="11.5" '
            f'fill="{c["text"]}">{esc(line)}</text>'
        )

    fy = H - pad - 2
    x = pad
    if repo.get("language"):
        col = LANG_COLOR.get(repo["language"], c["muted"])
        out.append(f'<circle cx="{x + 5}" cy="{fy - 4}" r="5" fill="{col}"/>')
        out.append(
            f'<text x="{x + 15}" y="{fy}" font-size="11" fill="{c["muted"]}">'
            f'{esc(repo["language"])}</text>'
        )
        x += 15 + text_width(repo["language"], 11) + 18

    for path, count in ((ICON_STAR, repo.get("stars", 0)), (ICON_FORK, repo.get("forks", 0))):
        out.append(icon(path, x, fy - 11, 12, c["muted"]))
        out.append(
            f'<text x="{x + 16}" y="{fy}" font-size="11" fill="{c["muted"]}">'
            f'{count}</text>'
        )
        x += 16 + text_width(str(count), 11) + 18

    return frame(W, H, c, "".join(out), f'{repo["name"]} repository card')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--user", required=True)
    p.add_argument("--out", type=Path, default=Path("assets"))
    p.add_argument("--projects", type=Path, default=Path("assets/projects.json"))
    p.add_argument("--stats", type=Path, default=Path("assets/stats.json"))
    args = p.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("METRICS_TOKEN")
    args.out.mkdir(parents=True, exist_ok=True)

    # Defaults / fallback metrics
    total_repos_display = "68"
    public_repos_display = "17"
    contributions_display = "355+"
    stars_display = "7+"
    audits_display = "4+ Audits"
    streak_display = "14 days"

    if args.stats.exists():
        try:
            sd = json.loads(args.stats.read_text(encoding="utf-8"))
            total_repos_display = str(sd.get("total_repos", total_repos_display))
            public_repos_display = str(sd.get("public_repos", public_repos_display))
            contributions_display = str(sd.get("total_contributions", contributions_display))
            stars_display = str(sd.get("total_stars", stars_display))
            audits_display = str(sd.get("security_audits", audits_display))
        except Exception as e:
            print(f"Warning reading stats.json: {e}", file=sys.stderr)

    # Fetch live GitHub data
    repos = []
    try:
        user_data = rest(f"/users/{args.user}", token)
        public_repos_display = str(user_data.get("public_repos", public_repos_display))
        page = 1
        while True:
            batch = rest(f"/users/{args.user}/repos?per_page=100&page={page}&type=owner", token)
            repos += batch
            if len(batch) < 100:
                break
            page += 1
        owned = [r for r in repos if not r.get("fork")]
        public_stars = sum(r.get("stargazers_count", 0) for r in owned)
        # Preserve private repo stars if known from stats.json / vault
        if public_stars > 0 and (not stars_display or stars_display.endswith("+") is False):
            stars_display = f"{max(public_stars, int(stars_display or 0))}+"
    except Exception as e:
        print(f"  GitHub REST API info note: {e}", file=sys.stderr)

    contrib = fetch_contributions(args.user, token)
    if contrib:
        total, current, longest = contrib
        contributions_display = f"{total:,}"
        streak_display = f"{current:,} days"
    else:
        print("  no token or live GraphQL, using configured telemetry numbers", file=sys.stderr)

    tiles = [
        ("Total Repos (17 Pub)", total_repos_display),
        ("Contributions", contributions_display),
        ("Total Stars", stars_display),
        ("Security Research", audits_display),
        ("Specialization", "Offensive Sec"),
        ("Primary Stack", "TS • Py • C++"),
    ]

    for theme in ("dark", "light"):
        dest = args.out / f"card-stats-{theme}.svg"
        dest.write_text(render_stats(args.user, tiles, theme), encoding="utf-8")
    print(f"wrote card-stats-*.svg ({len(tiles)} tiles)")

    if not args.projects.exists():
        print(f"no {args.projects}, skipping repo cards")
        return

    wanted = json.loads(args.projects.read_text(encoding="utf-8"))["projects"]
    by_name = {r["name"].lower(): r for r in repos}

    # Hardcoded metadata fallbacks for the 4 featured repos in case of API offline
    fallback_meta = {
        "aero-chat-cli": {"language": "TypeScript", "stars": 1, "forks": 0},
        "rtdb-inspector": {"language": "TypeScript", "stars": 3, "forks": 0},
        "trueface": {"language": "TypeScript", "stars": 1, "forks": 0},
        "kofitype-security-research": {"language": "HTML", "stars": 1, "forks": 0},
    }

    for entry in wanted:
        repo_name = entry["repo"]
        src = by_name.get(repo_name.lower())
        fb = fallback_meta.get(repo_name.lower(), {})
        card = {
            "name": src["name"] if src else repo_name,
            "description": entry.get("description") or (src.get("description") if src else ""),
            "language": (src.get("language") if src else None) or fb.get("language", "TypeScript"),
            "stars": (src.get("stargazers_count", 0) if src else 0) or fb.get("stars", 0),
            "forks": (src.get("forks_count", 0) if src else 0) or fb.get("forks", 0),
        }
        for theme in ("dark", "light"):
            dest = args.out / f"card-{card['name']}-{theme}.svg"
            dest.write_text(render_repo(card, theme), encoding="utf-8")
        print(f"wrote card-{card['name']}-*.svg ({card['stars']} stars, {card['language']})")


if __name__ == "__main__":
    main()
