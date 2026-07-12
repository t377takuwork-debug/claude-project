# cf_room internal_links.md freshness checker (ASCII-only source for PS5.1)
# Compares live sitemap URLs (cf-room.com) with rules\internal_links.md and reports the diff.
# It does NOT rewrite internal_links.md (the file has hand-written descriptions/categories);
# apply the reported additions/removals manually, then re-run to confirm "IN SYNC".
# Usage: powershell -ExecutionPolicy Bypass -File tools\update_internal_links.ps1
# Exit code: 0 = in sync / 1 = diff found or fetch failed

$ErrorActionPreference = "Stop"
$linksFile = Join-Path $PSScriptRoot "..\rules\internal_links.md"
$indexUrl = "https://cf-room.com/sitemap.xml"

# URLs that resolve HTTP 200 but are intentionally absent from the sitemap
# (verified 2026-07-12: mouse/uncategorized categories excluded by sitemap plugin).
# Listed here so they do not show up as stale on every run.
$ignoreStale = @(
    'https://cf-room.com/category/mouse',
    'https://cf-room.com/category/uncategorized'
)

if (-not (Test-Path $linksFile)) {
    Write-Output "ERROR: not found: $linksFile"
    exit 1
}

function Get-LocUrls([string]$Url) {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
    return @([regex]::Matches($resp.Content, '<loc>\s*([^<]+?)\s*</loc>') | ForEach-Object { $_.Groups[1].Value })
}

Write-Output "=== cf_room internal links freshness check ==="

# 1. Collect all page URLs from the sitemap index
try {
    $subSitemaps = Get-LocUrls $indexUrl
} catch {
    Write-Output "ERROR: failed to fetch sitemap index: $($_.Exception.Message)"
    exit 1
}
$live = @()
foreach ($sm in $subSitemaps) {
    try {
        $live += Get-LocUrls $sm
        Write-Output "[OK] fetched $sm"
    } catch {
        Write-Output "[WARN] failed to fetch $sm : $($_.Exception.Message)"
    }
}
$live = @($live | ForEach-Object { $_.TrimEnd('/') } | Where-Object { $_ -ne 'https://cf-room.com' } | Sort-Object -Unique)
if ($live.Count -eq 0) {
    Write-Output "ERROR: no URLs collected from sitemaps"
    exit 1
}

# 2. Collect URLs listed in internal_links.md
$linksRaw = Get-Content $linksFile -Raw -Encoding UTF8
$known = @([regex]::Matches($linksRaw, 'https://cf-room\.com[^\s\)\|<]*') | ForEach-Object { $_.Value.TrimEnd('/') } | Where-Object { $_ -ne 'https://cf-room.com' } | Sort-Object -Unique)

# 3. Diff
$newOnSite = @($live | Where-Object { $known -notcontains $_ })
$staleInFile = @($known | Where-Object { ($live -notcontains $_) -and ($ignoreStale -notcontains $_) })

Write-Output ""
Write-Output "sitemap URLs: $($live.Count) / listed in internal_links.md: $($known.Count)"
if ($newOnSite.Count -gt 0) {
    Write-Output ""
    Write-Output "--- ADD to internal_links.md (on site, not listed): $($newOnSite.Count) ---"
    $newOnSite | ForEach-Object { Write-Output "  $_/" }
}
if ($staleInFile.Count -gt 0) {
    Write-Output ""
    Write-Output "--- NOT IN SITEMAP (verify with HTTP before removing; may be non-canonical or excluded): $($staleInFile.Count) ---"
    $staleInFile | ForEach-Object { Write-Output "  $_/" }
}
Write-Output ""
if (($newOnSite.Count + $staleInFile.Count) -eq 0) {
    Write-Output "=== RESULT: IN SYNC ==="
    exit 0
} else {
    Write-Output "=== RESULT: DIFF FOUND (add=$($newOnSite.Count) remove=$($staleInFile.Count)) ==="
    exit 1
}
