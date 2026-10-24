# Deployment & Setup Guide · Profile v2

Everything in this `v2` directory represents your special repository:
**`github.com/iamjaved026/iamjaved026`** (matching your GitHub username).
The `README.md` at the root of that repository renders directly on your public GitHub profile!

---

## 🚀 1. Local Testing & Asset Preview

All SVG assets have already been generated and calibrated for you!
To preview everything locally before pushing:

1. Double-click or open `preview.html` in your browser.
2. Click **"↺ Replay Scanline Reveal"** to watch the animated scanline sweep across your dot-matrix portrait.
3. Check the Skill Radar, Language Radar, 6-Tile Telemetry card, and Selected Work cards.

To regenerate or customize assets locally at any time:
```powershell
.\setup.ps1
```

---

## 🔒 Including Private Repositories & Private Code Metrics

By default, GitHub's unauthenticated API can **only view public repositories** (17 repos). Private repositories and private commit code are strictly protected.

You have two simple ways to connect and include all **68 repositories** (including private security research & projects):

### Option A: The Full Vault Engine (Backup All 68 Repos + Extract Deep Metrics)
We created a comprehensive tool: **`github_vault.py`**.
1. Generate a classic token at **[https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)** with:
   - ✅ **`repo`** (Full control of private repositories - reads language bytes & private code volume)
   - ✅ **`read:user`** (Reads contribution history and profile)
2. Run from your workspace root:
   ```powershell
   python github_vault.py
   ```
   This will:
   - Securely back up **all 68 repositories** (private + public) into `backups/repositories/`.
   - Calculate exact lines and bytes of code across your entire private codebase.
   - Aggregate all private and public commits.
   - Automatically update your Profile v2 cards, 3D calendar, language bars, and radar charts!

### Option B: Cloud Automation (Runs automatically every 6 hours)
When you add the `METRICS_TOKEN` secret to your GitHub repository (explained in Step 4 below), GitHub Actions handles all of this automatically in the cloud on a schedule without needing to run anything locally.

---

## 📦 2. Push to GitHub

Navigate into your `v2` folder (or initialize Git in this directory) and push to your profile repository:

```bash
cd d:\Projects\portofilio\github\my\v2

git init
git branch -M main
git remote add origin https://github.com/iamjaved026/iamjaved026.git
git add -A
git commit -m "feat(profile): upgrade to v2 with radar, telemetry, and animated dot matrix"
git push -u origin main --force
```

> [!IMPORTANT]
> The repository **must be public** so that GitHub's Camo CDN can serve the SVG files.

---

## ⚙️ 3. Configure Workflow Permissions

To allow the automated GitHub Actions (Radar updates, Snake animation, and Metrics) to commit refreshed SVGs:

1. Go to your repo: **`https://github.com/iamjaved026/iamjaved026`**
2. Click **Settings** → **Actions** → **General**
3. Scroll down to **Workflow permissions**
4. Select **"Read and write permissions"**
5. Check **"Allow GitHub Actions to create and approve pull requests"**
6. Click **Save**.

---

## 🔑 4. Add the `METRICS_TOKEN` Secret

`lowlighter/metrics` needs a GitHub Personal Access Token (PAT) to generate your 3D isometric calendar and streak graphs:

1. Visit: **[https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)** (Personal access tokens classic)
2. Note: `Profile v2 Metrics Token`
3. Expiration: Choose `90 days`, `1 year`, or `No expiration`
4. Select Scopes:
   - ✅ **`read:user`** (Reads your user profile data and contributions)
   - ✅ **`repo`** (Allows private repos to count towards your 355+ contributions and 68 repo count!)
5. Click **Generate token** and copy the string (e.g., `ghp_...`).
6. In your profile repo: **Settings** → **Secrets and variables** → **Actions**
7. Click **New repository secret**:
   - Name: **`METRICS_TOKEN`**
   - Value: *[Paste your token]*
8. Click **Add secret**.

---

## ⚡ 5. Trigger Initial Workflows

Once pushed, go to the **Actions** tab on your repository:

| Workflow | Frequency | Purpose |
|---|---|---|
| **Metrics** | Every 6 hours | Updates 3D isometric calendar, languages, and achievements into `assets/metrics.*.svg` |
| **Snake** | Every 12 hours | Generates animated snake eating your contribution graph to the `output` branch |
| **Charts and cards** | Daily at 03:30 UTC | Fetches latest language bytes & star counts to update radar and repo cards |

Click each workflow and press **"Run workflow"** to trigger the initial run immediately!

---

## 🎨 Fine-Tuning Customizations

### Skill Radar (`assets/skills.json`)
Edit the values (0–100) or labels in `assets/skills.json` and commit. The **Charts and cards** workflow will automatically redraw `assets/radar-dark.svg` and `assets/radar-light.svg`!

### Dot-Matrix Portrait (`scripts/dotify.py`)
To tweak the visual styling of your portrait:
```powershell
# Cyber green monochrome with animated shimmer
python scripts\dotify.py assets\javed-hussain.jpg -o assets\portrait-mono --cols 88 --equalize --detail 0.55 --animate

# Circular vignette with color halftone
python scripts\dotify.py assets\javed-hussain.jpg -o assets\portrait --cols 90 --circle --color --reveal
```
