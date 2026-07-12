# cf_room WordPress REST API connectivity test (ASCII-only source for PS5.1)
# E2E check before real operation: auth -> media upload -> draft post -> cleanup.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\wp_connect_test.ps1                  # auth+media+post
#   powershell -ExecutionPolicy Bypass -File tools\wp_connect_test.ps1 -Step auth      # auth only
#   powershell -ExecutionPolicy Bypass -File tools\wp_connect_test.ps1 -Step cleanup   # delete test artifacts
#   -ImagePath <file>  : use your own image for the media step (default: auto-generated PNG)
#
# Safety: never publishes anything (draft only). Cleanup verifies deletion with a GET (expects 404)
# and reports leftovers explicitly. Created IDs are tracked in tools\connect_test_state.json.
# Exit code: 0 = all steps OK / 1 = any failure

param(
    [ValidateSet("all", "auth", "media", "post", "cleanup")]
    [string]$Step = "all",
    [string]$ImagePath = ""
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

$authFile = Join-Path $PSScriptRoot "wp_auth.local.json"
$stateFile = Join-Path $PSScriptRoot "connect_test_state.json"

if (-not (Test-Path $authFile)) {
    Write-Host "ERROR: auth file not found: $authFile"
    Write-Host "Create it with this JSON (gitignored, keep local):"
    Write-Host '{ "site": "https://cf-room.com", "user": "YOUR-WP-USER", "appPassword": "xxxx xxxx xxxx xxxx xxxx xxxx" }'
    Write-Host "Get the app password in WP admin: Users > Profile > Application Passwords (name: cf-article)."
    exit 1
}
$auth = Get-Content $authFile -Raw -Encoding UTF8 | ConvertFrom-Json
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("$($auth.user):$($auth.appPassword)"))
$headers = @{ Authorization = "Basic $basic" }
$api = "$($auth.site.TrimEnd('/'))/wp-json/wp/v2"

function Load-State {
    if (Test-Path $stateFile) { return Get-Content $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    return $null
}
function Save-State($obj) {
    $obj | ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8
}
function Get-HttpStatus($err) {
    if ($err.Exception.Response) { return [int]$err.Exception.Response.StatusCode }
    return -1
}

$state = Load-State
if ($null -eq $state) { $state = [pscustomobject]@{ mediaId = $null; mediaUrl = $null; postId = $null } }

# --- Step 1: auth check (read-only) ---
function Step-Auth {
    Write-Host "--- Step 1: auth check (GET /users/me) ---"
    try {
        $me = Invoke-RestMethod -Uri "$api/users/me" -Headers $headers -TimeoutSec 30
        Write-Host "[OK] authenticated as: $($me.name) (id=$($me.id))"
        return $true
    } catch {
        $code = Get-HttpStatus $_
        Write-Host "[ERROR] auth failed (HTTP $code): $($_.Exception.Message)"
        if ($code -eq 401) { Write-Host "        Check user name and application password in wp_auth.local.json." }
        return $false
    }
}

# --- Step 2: media upload test ---
function Step-Media {
    Write-Host "--- Step 2: media upload test ---"
    $file = $ImagePath
    $generated = $false
    if ($file -eq "") {
        $file = Join-Path $env:TEMP "cf-article-connect-test.png"
        Add-Type -AssemblyName System.Drawing
        $bmp = New-Object System.Drawing.Bitmap(120, 60)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.Clear([System.Drawing.Color]::SteelBlue)
        $g.Dispose()
        $bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
        $generated = $true
        Write-Host "[OK] test image generated: $file"
    }
    if (-not (Test-Path $file)) {
        Write-Host "[ERROR] image not found: $file"
        return $false
    }
    $name = [IO.Path]::GetFileName($file)
    $mime = @{ ".png" = "image/png"; ".webp" = "image/webp"; ".jpg" = "image/jpeg"; ".jpeg" = "image/jpeg"; ".gif" = "image/gif" }[[IO.Path]::GetExtension($file).ToLower()]
    if ($null -eq $mime) { Write-Host "[ERROR] unsupported image type: $name"; return $false }
    try {
        $h = $headers.Clone()
        $h["Content-Disposition"] = "attachment; filename=""$name"""
        $resp = Invoke-RestMethod -Method Post -Uri "$api/media" -Headers $h -ContentType $mime -InFile $file -TimeoutSec 120
        $script:state.mediaId = $resp.id
        $script:state.mediaUrl = $resp.source_url
        Save-State $script:state
        Write-Host "[OK] uploaded: id=$($resp.id) url=$($resp.source_url)"
    } catch {
        Write-Host "[ERROR] media upload failed (HTTP $(Get-HttpStatus $_)): $($_.Exception.Message)"
        return $false
    }
    try {
        $check = Invoke-WebRequest -Uri $state.mediaUrl -UseBasicParsing -TimeoutSec 30
        Write-Host "[OK] uploaded image is reachable (HTTP $($check.StatusCode))"
    } catch {
        Write-Host "[ERROR] uploaded image not reachable: $($_.Exception.Message)"
        return $false
    }
    if ($generated) { Remove-Item $file -Force }
    return $true
}

# --- Step 3: draft post test (never publishes) ---
function Step-Post {
    Write-Host "--- Step 3: draft post test (status=draft) ---"
    if ($null -eq $state.mediaUrl) {
        Write-Host "[ERROR] no uploaded media in state; run -Step media first"
        return $false
    }
    $blocks = "<!-- wp:paragraph --><p>cf-article connectivity test. Safe to delete.</p><!-- /wp:paragraph -->" +
              "<!-- wp:image --><figure class=""wp-block-image size-large""><img src=""$($state.mediaUrl)"" alt=""cf-article connect test image"" width=""120""/></figure><!-- /wp:image -->"
    $body = @{ title = "cf-article connect test"; status = "draft"; content = $blocks } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Method Post -Uri "$api/posts" -Headers $headers `
            -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 60
        $script:state.postId = $resp.id
        Save-State $script:state
        Write-Host "[OK] draft created: id=$($resp.id) status=$($resp.status)"
        Write-Host "     check it in WP admin: Posts > Drafts > 'cf-article connect test'"
        return $true
    } catch {
        Write-Host "[ERROR] draft post failed (HTTP $(Get-HttpStatus $_)): $($_.Exception.Message)"
        return $false
    }
}

# --- Step 4: cleanup (delete + verify with GET 404) ---
function Step-Cleanup {
    Write-Host "--- Step 4: cleanup ---"
    $leftovers = 0
    foreach ($item in @(
        @{ Kind = "post";  Id = $state.postId;  Endpoint = "$api/posts" },
        @{ Kind = "media"; Id = $state.mediaId; Endpoint = "$api/media" }
    )) {
        if ($null -eq $item.Id) {
            Write-Host "[SKIP] no test $($item.Kind) recorded in state"
            continue
        }
        try {
            $null = Invoke-RestMethod -Method Delete -Uri "$($item.Endpoint)/$($item.Id)?force=true" -Headers $headers -TimeoutSec 60
            Write-Host "[OK] delete request sent: $($item.Kind) id=$($item.Id)"
        } catch {
            $code = Get-HttpStatus $_
            if ($code -eq 404) {
                Write-Host "[OK] $($item.Kind) id=$($item.Id) was already gone (404)"
            } else {
                Write-Host "[ERROR] delete failed: $($item.Kind) id=$($item.Id) (HTTP $code)"
                $leftovers++
                continue
            }
        }
        # verify deletion: GET must return 404
        try {
            $null = Invoke-RestMethod -Uri "$($item.Endpoint)/$($item.Id)" -Headers $headers -TimeoutSec 30
            Write-Host "[ERROR] verification failed: $($item.Kind) id=$($item.Id) still exists"
            $leftovers++
        } catch {
            $code = Get-HttpStatus $_
            if ($code -eq 404) {
                Write-Host "[OK] verified deleted: $($item.Kind) id=$($item.Id) (GET returned 404)"
            } else {
                Write-Host "[WARN] verification inconclusive for $($item.Kind) id=$($item.Id) (HTTP $code); check manually"
                $leftovers++
            }
        }
    }
    if ($leftovers -eq 0) {
        if (Test-Path $stateFile) { Remove-Item $stateFile -Force }
        Write-Host "=== CLEANUP COMPLETE: all test artifacts removed and verified (state file cleared) ==="
        return $true
    } else {
        Write-Host "=== CLEANUP INCOMPLETE: $leftovers item(s) need manual check in WP admin ==="
        return $false
    }
}

# --- Runner ---
$ok = $true
switch ($Step) {
    "auth"    { $ok = Step-Auth }
    "media"   { $ok = (Step-Auth) -and (Step-Media) }
    "post"    { $ok = (Step-Auth) -and (Step-Post) }
    "cleanup" { $ok = (Step-Auth) -and (Step-Cleanup) }
    "all"     { $ok = (Step-Auth) -and (Step-Media) -and (Step-Post)
                if ($ok) { Write-Host ""; Write-Host "NEXT: check the draft in WP admin, then run: -Step cleanup" } }
}
Write-Host ""
if ($ok) { Write-Host "=== RESULT: $Step OK ==="; exit 0 } else { Write-Host "=== RESULT: $Step FAILED ==="; exit 1 }

