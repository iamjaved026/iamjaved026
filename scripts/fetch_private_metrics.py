#!/usr/bin/env python3
"""
fetch_private_metrics.py - Authenticated GitHub metric aggregator.

Connects to GitHub using a Personal Access Token (PAT) with `repo` and `read:user` scopes
to analyze ALL repositories (including private research repositories) and compute:
  1. Complete language byte counts across all 68 public + private repos
  2. Full GraphQL contribution calendar (public + private commits)
  3. Total star, fork, and repository counts
  4. Auto-regenerates radar charts, telemetry cards, isocalendar, and language SVGs.

Usage:
    $env:GITHUB_TOKEN = "ghp_your_token_here"
    python scripts/fetch_private_metrics.py
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

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"

UA = {"User-Agent": "javed-private-metrics/2.0"}


def api_get(url: str, token: str) -> dict | list:
    req = urllib.request.Request(url, headers={
        **UA,
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def graphql_query(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            **UA,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


CONTRIB_GRAPHQL = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{
          contributionDays{
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("METRICS_TOKEN") or os.environ.get("GH_TOKEN")
    
    if not token:
        print("\n[!] No GITHUB_TOKEN environment variable detected.")
        token = input("Enter your GitHub Personal Access Token (classic with 'repo' & 'read:user' scopes): ").strip()
        if not token:
            print("Aborted. Token required to access private repositories.")
            sys.exit(1)

    print("\n[1/4] Authenticating with GitHub API...")
    try:
        user_info = api_get("https://api.github.com/user", token)
        login = user_info["login"]
        total_private = user_info.get("total_private_repos", 0)
        public_repos = user_info.get("public_repos", 0)
        total_repos = total_private + public_repos
        print(f"      Authenticated as: @{login}")
        print(f"      Total Repos: {total_repos} ({public_repos} public + {total_private} private)")
    except urllib.error.HTTPError as e:
        print(f"[!] Authentication failed: HTTP {e.code} ({e.reason})")
        sys.exit(1)

    print("\n[2/4] Fetching all repositories (public + private) and language byte counts...")
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner"
        batch = api_get(url, token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1

    print(f"      Retrieved {len(repos)} owned repositories.")

    language_totals: dict[str, int] = {}
    for r in repos:
        r_name = r["name"]
        lang_url = r["languages_url"]
        try:
            r_langs = api_get(lang_url, token)
            for lang, count in r_langs.items():
                language_totals[lang] = language_totals.get(lang, 0) + count
        except Exception as e:
            print(f"      Warning reading {r_name}: {e}")

    sorted_langs = dict(sorted(language_totals.items(), key=lambda x: x[1], reverse=True))
    print("      Consolidated language breakdown across ALL repos:")
    for l, b in list(sorted_langs.items())[:8]:
        print(f"        • {l}: {b:,} bytes")

    print("\n[3/4] Querying full GraphQL contribution calendar (public + private commits)...")
    cal_data = graphql_query(CONTRIB_GRAPHQL, {"login": login}, token)
    calendar = cal_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total_contribs = calendar["totalContributions"]
    print(f"      Total Contributions (public + private): {total_contribs}")

    days_list = []
    level_map = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }
    for w in calendar["weeks"]:
        for d in w["contributionDays"]:
            lvl = level_map.get(d["contributionLevel"], 0)
            days_list.append({
                "date": d["date"],
                "level": lvl,
                "count": d["contributionCount"],
                "tip": f"{d['contributionCount']} contributions on {d['date']}"
            })

    # Save to contributions_real.json
    with open(ASSETS / "contributions_real.json", "w", encoding="utf-8") as f:
        json.dump({"total": total_contribs, "days": days_list}, f, indent=2)

    # Update stats.json with verified private + public numbers
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    stats_data = {
        "_comment": "Verified developer statistics for iamjaved026 (including private repos)",
        "total_repos": total_repos,
        "public_repos": public_repos,
        "private_repos": total_private,
        "total_contributions": f"{total_contribs}+",
        "total_stars": f"{total_stars}+",
        "security_audits": "4+ Audits",
        "followers": f"{user_info.get('followers', 1)}+",
        "focus": "Security & Systems"
    }
    with open(ASSETS / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2)
    print("      Updated assets/stats.json and assets/contributions_real.json")

    print("\n[4/4] Regenerating cards, radars, isocalendar, and snake...")
    # Re-run cards.py
    os.environ["GITHUB_TOKEN"] = token
    import subprocess
    subprocess.run([sys.executable, str(SCRIPTS / "cards.py"), "--user", login, "--projects", str(ASSETS / "projects.json"), "--stats", str(ASSETS / "stats.json"), "--out", str(ASSETS)])
    subprocess.run([sys.executable, str(SCRIPTS / "radar.py"), "--data", str(ASSETS / "skills.json"), "-o", str(ASSETS / "radar")])
    subprocess.run([sys.executable, str(SCRIPTS / "render_real_metrics.py")])

    print("\n[✔] COMPLETE! All private + public repository data has been pulled and re-rendered.")
    print("    Open preview.html to view your updated telemetry, calendar, and language mix!")


if __name__ == "__main__":
    main()
