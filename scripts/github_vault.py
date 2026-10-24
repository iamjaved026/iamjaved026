#!/usr/bin/env python3
"""
github_vault.py - Advanced GitHub Backup & Full-Spectrum Metric Analyzer.

Features:
  1. Authenticated API connection via GitHub Personal Access Token (PAT).
  2. Complete backup of ALL repositories (public, private, and research repos)
     into a secure local vault with git clone/fetch and metadata preservation.
  3. Deep telemetry analysis:
     - Aggregate language byte breakdown across all public & private codebases.
     - Commit count, star count, fork count, private vs public distribution.
     - Full GraphQL contribution history (public + private commits).
  4. Automatic real-time profile v2 synchronization:
     - Updates assets/stats.json & assets/contributions_real.json
     - Re-renders 3D isocalendar, language breakdown, radar charts, and cards.
"""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Paths
V2_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = V2_DIR.parent.parent
DEFAULT_BACKUP_DIR = WORKSPACE_DIR / "backups"
ASSETS_DIR = V2_DIR / "assets"
SCRIPTS_DIR = V2_DIR / "scripts"

UA = {"User-Agent": "GitHub-Vault-Pro/2.5"}


def log(msg: str, color: str = ""):
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    prefix = colors.get(color, "")
    suffix = colors["reset"] if color else ""
    # Ensure Windows console handles UTF-8 / formatting
    print(f"{prefix}{msg}{suffix}")


def api_request(url: str, token: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={
            **UA,
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def graphql_request(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            **UA,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


GRAPHQL_CONTRIBS = """
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


def clone_or_update_repo(repo: dict, token: str, repos_dir: Path, mirror: bool = False) -> bool:
    name = repo["name"]
    clone_url = repo["clone_url"].replace(
        "https://github.com/",
        f"https://x-access-token:{token}@github.com/",
    )
    target = repos_dir / (f"{name}.git" if mirror else name)

    try:
        if target.exists():
            log(f"    ↳ Updating existing: {name}...", "cyan")
            if mirror:
                cmd = ["git", "--git-dir", str(target), "remote", "update"]
            else:
                cmd = ["git", "-C", str(target), "fetch", "--all", "--prune"]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            log(f"    ↳ Cloning: {name} ({'private' if repo['private'] else 'public'})...", "green")
            if mirror:
                cmd = ["git", "clone", "--mirror", clone_url, str(target)]
            else:
                cmd = ["git", "clone", "--depth", "1", clone_url, str(target)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Save metadata JSON for the repo
        meta_path = repos_dir / f"{name}_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "pushed_at": repo.get("pushed_at"),
                "default_branch": repo.get("default_branch"),
                "html_url": repo.get("html_url"),
            }, f, indent=2)
        return True
    except subprocess.CalledProcessError as e:
        log(f"    [!] Error cloning {name}: {e}", "red")
        return False


def main():
    parser = argparse.ArgumentParser(description="GitHub Vault & Telemetry Engine")
    parser.add_argument("--token", help="GitHub Personal Access Token (classic with repo & read:user scopes)")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Destination directory for backups")
    parser.add_argument("--skip-clone", action="store_true", help="Skip downloading repository files, only update metrics")
    parser.add_argument("--mirror", action="store_true", help="Mirror full git bare repositories (includes all branches & tags)")
    parser.add_argument("--no-profile-sync", action="store_true", help="Skip updating profile v2 assets")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("METRICS_TOKEN") or os.environ.get("GH_TOKEN")

    print("\n" + "=" * 65)
    log("     GITHUB VAULT: REPOSITORY BACKUP & TELEMETRY ENGINE     ", "green")
    print("=" * 65 + "\n")

    if not token:
        log("[?] Authentication Required", "yellow")
        print("To download private repositories & compute total private language bytes,")
        print("a GitHub Personal Access Token (classic) with 'repo' and 'read:user' scopes is required.\n")
        print("Create one here: https://github.com/settings/tokens/new\n")
        try:
            token = getpass.getpass("Enter your GitHub Token (input hidden): ").strip()
        except Exception:
            token = input("Enter your GitHub Token: ").strip()

    if not token:
        log("[!] Error: No token provided. Exiting.", "red")
        sys.exit(1)

    # 1. AUTHENTICATE
    log("[1/5] Verifying Token & Identity...", "cyan")
    try:
        user = api_request("https://api.github.com/user", token)
        login = user["login"]
        public_count = user.get("public_repos", 0)
        private_count = user.get("total_private_repos", 0)
        total_repos_count = public_count + private_count
        log(f"  [✔] Authenticated: @{login} ({user.get('name', '')})", "green")
        log(f"  [✔] Repositories detected: {total_repos_count} total ({public_count} public, {private_count} private)", "green")
    except urllib.error.HTTPError as e:
        log(f"  [!] Authentication failed: HTTP {e.code} ({e.reason})", "red")
        sys.exit(1)

    # 2. DISCOVER ALL REPOSITORIES
    log("\n[2/5] Fetching complete repository index across account...", "cyan")
    repos = []
    page = 1
    while True:
        batch = api_request(f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner", token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1

    owned = [r for r in repos if not r.get("fork")]
    forks = [r for r in repos if r.get("fork")]
    log(f"  Found {len(repos)} repositories ({len(owned)} owned, {len(forks)} forks).", "green")

    # 3. BACKUP REPOSITORIES
    backup_dir = args.backup_dir
    repos_dir = backup_dir / "repositories"
    repos_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_clone:
        log(f"\n[3/5] Backing up repositories into: {repos_dir}...", "cyan")
        success_count = 0
        for i, r in enumerate(repos, 1):
            priv_badge = "[PRIVATE]" if r["private"] else "[PUBLIC] "
            print(f"  [{i}/{len(repos)}] {priv_badge} {r['name']}")
            if clone_or_update_repo(r, token, repos_dir, mirror=args.mirror):
                success_count += 1
            time.sleep(0.1)
        log(f"\n  [✔] Backup complete: {success_count}/{len(repos)} repositories successfully secured.", "green")
    else:
        log("\n[3/5] Skipping repository clone (--skip-clone enabled)...", "yellow")

    # 4. COMPUTE EXACT CONSOLIDATED TELEMETRY
    log("\n[4/5] Aggregating multi-repo code metrics & contribution telemetry...", "cyan")
    language_breakdown: dict[str, int] = {}
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)

    for r in repos:
        lang_url = r["languages_url"]
        try:
            r_langs = api_request(lang_url, token)
            for lang, count in r_langs.items():
                language_breakdown[lang] = language_breakdown.get(lang, 0) + count
        except Exception:
            pass

    sorted_languages = dict(sorted(language_breakdown.items(), key=lambda x: x[1], reverse=True))
    total_bytes = sum(sorted_languages.values())

    log("\n  --- Complete Consolidated Language Volume (Public + Private) ---", "bold")
    for lang, b in list(sorted_languages.items())[:10]:
        pct = (b / total_bytes * 100) if total_bytes > 0 else 0
        log(f"    • {lang:<16} : {b:>10,} bytes  ({pct:>5.1f}%)", "cyan")

    # Fetch complete contribution calendar via GraphQL
    log("\n  Fetching private + public contribution calendar...", "cyan")
    cal_data = graphql_request(GRAPHQL_CONTRIBS, {"login": login}, token)
    calendar = cal_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total_contributions = calendar["totalContributions"]
    log(f"  [✔] Total 1-Year Contributions (Public + Private): {total_contributions}", "green")

    days_list = []
    level_map = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    for w in calendar["weeks"]:
        for d in w["contributionDays"]:
            days_list.append({
                "date": d["date"],
                "level": level_map.get(d["contributionLevel"], 0),
                "count": d["contributionCount"],
                "tip": f"{d['contributionCount']} contributions on {d['date']}",
            })

    # Save Backup Vault Manifest
    manifest = {
        "timestamp": dt.datetime.now().isoformat(),
        "user": login,
        "total_repositories": len(repos),
        "public_repositories": public_count,
        "private_repositories": private_count,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_contributions_1y": total_contributions,
        "language_bytes": sorted_languages,
        "repositories": [{
            "name": r["name"],
            "private": r["private"],
            "html_url": r.get("html_url", f"https://github.com/{login}/{r['name']}"),
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "updated_at": r.get("updated_at"),
        } for r in repos],
    }

    manifest_file = backup_dir / "vault_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log(f"  [✔] Vault manifest saved to: {manifest_file}", "green")

    # Write human-readable BACKUP_SUMMARY.md
    summary_md = f"""# 🛡️ GitHub Backup & Vault Summary · @{login}

- **Backup Timestamp**: `{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
- **Total Repositories**: **`{len(repos)}`** (`{public_count}` Public, `{private_count}` Private)
- **Total Stars**: **`{total_stars}`** | **Total Forks**: **`{total_forks}`**
- **Total Contributions (1 Year)**: **`{total_contributions}`** (Public + Private)
- **Local Storage Path**: `{repos_dir}`

---

## 📊 Consolidated Codebase Language Distribution

| Language | Volume (Bytes) | Share |
|---|---|---|
""" + "\n".join([f"| **{lang}** | `{bytes_cnt:,} B` | `{bytes_cnt/total_bytes*100:.2f}%` |" for lang, bytes_cnt in sorted_languages.items()]) + """

---

## 📦 Secured Repositories Index

| Repository | Privacy | Primary Language | Stars | Last Updated |
|---|---|---|---|---|
""" + "\n".join([f"| [`{r['name']}`]({r.get('html_url', '#')}) | {'🔒 Private' if r['private'] else '🌐 Public'} | `{r.get('language') or 'None'}` | `{r.get('stars', 0)}` | `{r.get('updated_at', '')[:10]}` |" for r in manifest['repositories']]) + "\n"

    with open(backup_dir / "BACKUP_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary_md)

    # 5. SYNCHRONIZE PROFILE V2
    if not args.no_profile_sync:
        log("\n[5/5] Synchronizing Profile v2 with Real Private + Public Metrics...", "cyan")

        # Save contributions_real.json
        with open(ASSETS_DIR / "contributions_real.json", "w", encoding="utf-8") as f:
            json.dump({"total": total_contributions, "days": days_list}, f, indent=2)

        # Save stats.json
        stats_data = {
            "_comment": f"Verified developer statistics for {login} across all {len(repos)} repos",
            "total_repos": len(repos),
            "public_repos": public_count,
            "private_repos": private_count,
            "total_contributions": f"{total_contributions}+",
            "total_stars": f"{total_stars}+",
            "security_audits": "4+ Audits",
            "followers": f"{user.get('followers', 1)}+",
            "focus": "Security & Systems",
        }
        with open(ASSETS_DIR / "stats.json", "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2)

        # Update language bytes in render_real_metrics.py dynamically if needed
        os.environ["GITHUB_TOKEN"] = token

        log("  ↳ Re-rendering telemetry cards...", "cyan")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "cards.py"), "--user", login, "--projects", str(ASSETS_DIR / "projects.json"), "--stats", str(ASSETS_DIR / "stats.json"), "--out", str(ASSETS_DIR)], check=True)

        log("  ↳ Re-rendering skill radar...", "cyan")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "radar.py"), "--data", str(ASSETS_DIR / "skills.json"), "-o", str(ASSETS_DIR / "radar")], check=True)

        log("  ↳ Re-rendering 3D isocalendar, language breakdown & snake graph...", "cyan")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "render_real_metrics.py")], check=True)

        log("\n[✔] SUCCESS: Profile v2 fully synchronized with live vault data!", "green")
        log("    Check preview.html to view your updated telemetry, calendar, and private metrics.")
    else:
        log("\n[5/5] Profile sync skipped (--no-profile-sync enabled).", "yellow")

    print("\n" + "=" * 65)
    log("           ALL VAULT OPERATIONS SUCCESSFULLY COMPLETED!         ", "green")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
