# vtuber_log WordPress media uploader via REST API (ASCII-only source for PS5.1)
# Uploads all images in assets\<Slug>\ to the WP media library, sets alt/title from
# manifest.md, and writes the actual URLs to assets\<Slug>\uploaded_urls.json.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\wp_upload.ps1 -Slug <article-slug> [-DryRun]
#
# Auth file (gitignored): tools\wp_auth.local.json
#   { "site": "https://vtuber-verse.com", "user": "WP-USER", "appPassword": "xxxx xxxx xxxx xxxx xxxx xxxx" }
#   Create the application password in WP admin: Users > Profile > Application Passwords.
#
# manifest.md (in assets\<Slug>\): pipe table whose first 3 columns are | file | alt | title |
# Exit code: 0 = all uploaded / 1 = any failure

param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,
    [switch]$DryRun
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

$assetsDir = Join-Path $PSScriptRoot "..\assets\$Slug"
$authFile = Join-Path $PSScriptRoot "wp_auth.local.json"
$manifestFile = Join-Path $assetsDir "manifest.md"
$outFile = Join-Path $assetsDir "uploaded_urls.json"

if (-not (Test-Path $assetsDir)) {
    Write-Output "ERROR: assets folder not found: $assetsDir"
    exit 1
}
if (-not (Test-Path $authFile)) {
    Write-Output "ERROR: auth file not found: $authFile"
    Write-Output "Create it with this JSON (gitignored, keep local):"
    Write-Output '{ "site": "https://vtuber-verse.com", "user": "YOUR-WP-USER", "appPassword": "xxxx xxxx xxxx xxxx xxxx xxxx" }'
    Write-Output "Get the app password in WP admin: Users > Profile > Application Passwords (name it e.g. vtuber-article)."
    exit 1
}

$auth = Get-Content $authFile -Raw -Encoding UTF8 | ConvertFrom-Json
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("$($auth.user):$($auth.appPassword)"))
$mediaEndpoint = "$($auth.site.TrimEnd('/'))/wp-json/wp/v2/media"

# Parse manifest.md pipe table: | file | alt | title | ...
$meta = @{}
if (Test-Path $manifestFile) {
    foreach ($line in (Get-Content $manifestFile -Encoding UTF8)) {
        if ($line -notmatch '^\s*\|') { continue }
        $cols = $line.Trim().Trim('|') -split '\|'
        if ($cols.Count -lt 3) { continue }
        $f = $cols[0].Trim()
        if ($f -eq '' -or $f -eq 'file' -or $f -match '^[-: ]+$') { continue }
        $meta[$f] = @{ alt = $cols[1].Trim(); title = $cols[2].Trim() }
    }
    Write-Output "[OK] manifest parsed: $($meta.Count) entries"
} else {
    Write-Output "[WARN] manifest.md not found; uploading without alt/title metadata"
}

$mimeMap = @{ ".webp" = "image/webp"; ".jpg" = "image/jpeg"; ".jpeg" = "image/jpeg"; ".png" = "image/png"; ".gif" = "image/gif" }
$images = @(Get-ChildItem $assetsDir -File | Where-Object { $mimeMap.ContainsKey($_.Extension.ToLower()) })
if ($images.Count -eq 0) {
    Write-Output "ERROR: no image files in $assetsDir"
    exit 1
}

# Enforce ASCII filenames (non-ASCII breaks Content-Disposition on PS5.1 and makes messy URLs)
$badNames = @($images | Where-Object { $_.Name -match '[^\x20-\x7E]' })
if ($badNames.Count -gt 0) {
    foreach ($b in $badNames) { Write-Output "ERROR: non-ASCII filename (rename first): $($b.Name)" }
    exit 1
}

Write-Output "=== wp_upload: $($images.Count) images from assets\$Slug ==="
if ($DryRun) {
    foreach ($img in $images) {
        $m = $meta[$img.Name]
        $altInfo = "(no manifest entry)"
        if ($null -ne $m) { $altInfo = "alt=$($m.alt) / title=$($m.title)" }
        Write-Output "[DRYRUN] $($img.Name) -> $mediaEndpoint  $altInfo"
    }
    Write-Output "=== DRYRUN done (nothing uploaded) ==="
    exit 0
}

$results = [ordered]@{}
$failed = 0
foreach ($img in $images) {
    try {
        $headers = @{
            Authorization = "Basic $basic"
            "Content-Disposition" = "attachment; filename=""$($img.Name)"""
        }
        $resp = Invoke-RestMethod -Method Post -Uri $mediaEndpoint -Headers $headers `
            -ContentType $mimeMap[$img.Extension.ToLower()] -InFile $img.FullName -TimeoutSec 120
        $results[$img.Name] = $resp.source_url
        Write-Output "[OK] uploaded $($img.Name) -> $($resp.source_url) (id=$($resp.id))"

        $m = $meta[$img.Name]
        if ($null -ne $m -and ($m.alt -ne '' -or $m.title -ne '')) {
            $body = @{ alt_text = $m.alt; title = $m.title } | ConvertTo-Json
            $null = Invoke-RestMethod -Method Post -Uri "$mediaEndpoint/$($resp.id)" `
                -Headers @{ Authorization = "Basic $basic" } `
                -ContentType "application/json; charset=utf-8" `
                -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 60
            Write-Output "     alt/title set on media id=$($resp.id)"
        }
    } catch {
        Write-Output "[ERROR] upload failed for $($img.Name): $($_.Exception.Message)"
        $failed++
    }
}

# Write filename -> URL mapping for the draft generator
$results | ConvertTo-Json | Set-Content -Path $outFile -Encoding UTF8
Write-Output "=== mapping written: $outFile ==="
Write-Output "=== RESULT: uploaded $($results.Count) / failed $failed ==="
if ($failed -gt 0) { exit 1 } else { exit 0 }
