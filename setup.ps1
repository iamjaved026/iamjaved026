<#
.SYNOPSIS
    Setup and asset builder for Javed Hussain's (@iamjaved026) GitHub Profile v2.

.EXAMPLE
    .\setup.ps1
    # Regenerates all radar charts, dot-matrix portrait, and project cards
#>
[CmdletBinding()]
param(
    [string]$Username = "iamjaved026",
    [string]$Name = "Javed Hussain",
    [string]$Image = "assets\javed-hussain.jpg",
    [int]$Cols = 92
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "   Javed Hussain (@iamjaved026) Profile v2 Generator    " -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Cyan

# 1. Skill Radar
Write-Host "[1/4] Generating Skill Radar from assets\skills.json..." -ForegroundColor Cyan
python (Join-Path $root 'scripts\radar.py') --data (Join-Path $root 'assets\skills.json') -o (Join-Path $root 'assets\radar')

# 2. Language Radar
Write-Host "[2/4] Generating Language Radar for $Username..." -ForegroundColor Cyan
try {
    python (Join-Path $root 'scripts\radar.py') --github $Username -o (Join-Path $root 'assets\radar-langs') --values --limit 7 --curve 0.4 --exclude "html,css,batchfile,shell,makefile,dockerfile,procfile"
} catch {
    Write-Warning "Language radar skipped or rate-limited: $_"
}

# 3. Project & Stat Cards
Write-Host "[3/4] Generating Stat and Repo Cards..." -ForegroundColor Cyan
python (Join-Path $root 'scripts\cards.py') --user $Username --projects (Join-Path $root 'assets\projects.json') --stats (Join-Path $root 'assets\stats.json') --out (Join-Path $root 'assets')

# 4. Authentic Live Metrics (3D Isometric Calendar, Languages & Snake)
Write-Host "[4/5] Rendering Live 355-Commit Isocalendar, Languages & Snake Graph..." -ForegroundColor Cyan
python (Join-Path $root 'scripts\render_real_metrics.py')

# 5. Dot-matrix Portrait
if (Test-Path (Join-Path $root $Image)) {
    Write-Host "[5/5] Rendering Animated Dot-Matrix Portrait from $Image..." -ForegroundColor Cyan
    python (Join-Path $root 'scripts\dotify.py') (Join-Path $root $Image) -o (Join-Path $root 'assets\portrait') --cols $Cols --equalize --detail 0.55 --color --reveal
    python (Join-Path $root 'scripts\dotify.py') (Join-Path $root $Image) -o (Join-Path $root 'assets\portrait-mono') --cols $Cols --equalize --detail 0.55 --reveal
} else {
    Write-Host "[5/5] Image $Image not found, skipping portrait." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "[OK] Success! All local assets generated." -ForegroundColor Green
Write-Host "     Open preview.html in your browser to inspect everything!" -ForegroundColor Cyan
Write-Host "     Review SETUP.md for one-click deployment instructions to GitHub." -ForegroundColor DarkGray
Write-Host ""
