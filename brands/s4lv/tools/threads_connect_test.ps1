# s4lv Threads API connectivity test (ASCII-only source for PS5.1)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\threads_connect_test.ps1                # auth check only (safe, read-only)
#   powershell -ExecutionPolicy Bypass -File tools\threads_connect_test.ps1 -Step refresh   # refresh long-lived token (safe)
#   powershell -ExecutionPolicy Bypass -File tools\threads_connect_test.ps1 -Step post -Confirm2Publish
#
# IMPORTANT: Threads API has no draft state. -Step post creates a container AND
# publishes it live and public immediately. It is NOT reversible via this script
# (no delete endpoint is wired up here). Never run -Step post without explicit,
# in-the-moment user confirmation. -Confirm2Publish must be passed deliberately;
# omitting it stops the script after container creation (no publish call is made).
#
# Exit code: 0 = requested step OK / 1 = any failure

param(
    [ValidateSet("auth", "refresh", "post")]
    [string]$Step = "auth",
    [string]$Text = "",
    [switch]$Confirm2Publish
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

$authFile = Join-Path $PSScriptRoot "threads_auth.local.json"
$base = "https://graph.threads.net/v1.0"

if (-not (Test-Path $authFile)) {
    Write-Host "ERROR: auth file not found: $authFile"
    Write-Host "Create it with this JSON (gitignored, keep local):"
    Write-Host '{ "access_token": "YOUR-LONG-LIVED-TOKEN", "threads_user_id": "YOUR-THREADS-USER-ID", "app_secret": "YOUR-APP-SECRET" }'
    Write-Host "app_secret is only needed for -Step refresh."
    exit 1
}
try {
    $auth = Get-Content $authFile -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
} catch {
    # Deliberately do not print $_.Exception.Message here: PowerShell's JSON parser
    # echoes the invalid content (which may contain the raw token) into that message.
    Write-Host "ERROR: threads_auth.local.json is not valid JSON. Fix the syntax and retry."
    Write-Host "Expected shape:"
    Write-Host '{ "access_token": "YOUR-LONG-LIVED-TOKEN", "threads_user_id": "YOUR-THREADS-USER-ID" }'
    exit 1
}
if (-not $auth.access_token -or -not $auth.threads_user_id) {
    Write-Host "ERROR: threads_auth.local.json is missing access_token or threads_user_id."
    exit 1
}

function Get-HttpStatus($err) {
    if ($err.Exception.Response) { return [int]$err.Exception.Response.StatusCode }
    return -1
}

# --- Step: auth check (read-only, safe to rerun anytime) ---
function Step-Auth {
    Write-Host "--- Step: auth check (GET /me) ---"
    try {
        $uri = "$base/me?fields=id,username&access_token=$($auth.access_token)"
        $me = Invoke-RestMethod -Uri $uri -TimeoutSec 30
        Write-Host "[OK] authenticated as: $($me.username) (id=$($me.id))"
        return $true
    } catch {
        $code = Get-HttpStatus $_
        Write-Host "[ERROR] auth failed (HTTP $code): $($_.Exception.Message)"
        if ($code -eq 400 -or $code -eq 401) { Write-Host "        Token may be expired or invalid. Check threads_auth.local.json." }
        return $false
    }
}

# --- Step: refresh long-lived token (safe; writes the new token straight to
#     threads_auth.local.json, never to the console/output) ---
function Step-Refresh {
    Write-Host "--- Step: refresh long-lived token ---"
    try {
        $uri = "$base/refresh_access_token?grant_type=th_refresh_token&access_token=$($auth.access_token)"
        $resp = Invoke-RestMethod -Uri $uri -TimeoutSec 30
        $auth.access_token = $resp.access_token
        $auth | ConvertTo-Json | Set-Content -Path $authFile -Encoding UTF8
        $expiresDays = [math]::Round($resp.expires_in / 86400, 1)
        Write-Host "[OK] refreshed and saved to threads_auth.local.json. New token valid for about $expiresDays days."
        return $true
    } catch {
        Write-Host "[ERROR] refresh failed (HTTP $(Get-HttpStatus $_)): $($_.Exception.Message)"
        return $false
    }
}

# --- Step: post (LIVE / PUBLIC - two-stage container create + publish) ---
function Step-Post {
    if ($Text -eq "") {
        Write-Host "[ERROR] -Text is required for -Step post"
        return $false
    }
    Write-Host "--- Step: create container (POST /$($auth.threads_user_id)/threads) ---"
    $creationId = $null
    try {
        $uri = "$base/$($auth.threads_user_id)/threads"
        $body = @{ media_type = "TEXT"; text = $Text; access_token = $auth.access_token }
        $resp = Invoke-RestMethod -Method Post -Uri $uri -Body $body -TimeoutSec 30
        $creationId = $resp.id
        Write-Host "[OK] container created: creation_id=$creationId (NOT public yet)"
    } catch {
        Write-Host "[ERROR] container creation failed (HTTP $(Get-HttpStatus $_)): $($_.Exception.Message)"
        return $false
    }

    if (-not $Confirm2Publish) {
        Write-Host ""
        Write-Host "[STOPPED] Container created but NOT published (this is intentional)."
        Write-Host "          Re-run with -Confirm2Publish only after explicit user go-ahead to publish this exact text live."
        return $true
    }

    Write-Host "--- Step: publish (POST /$($auth.threads_user_id)/threads_publish) — THIS GOES LIVE NOW ---"
    try {
        $uri = "$base/$($auth.threads_user_id)/threads_publish"
        $body = @{ creation_id = $creationId; access_token = $auth.access_token }
        $resp = Invoke-RestMethod -Method Post -Uri $uri -Body $body -TimeoutSec 30
        Write-Host "[OK] published: id=$($resp.id)"
        Write-Host "     This post is now public. Delete manually in the Threads app if it was only a test."
        return $true
    } catch {
        Write-Host "[ERROR] publish failed (HTTP $(Get-HttpStatus $_)): $($_.Exception.Message)"
        return $false
    }
}

# --- Runner ---
$ok = $true
switch ($Step) {
    "auth"    { $ok = Step-Auth }
    "refresh" { $ok = Step-Refresh }
    "post"    { $ok = Step-Post }
}
Write-Host ""
if ($ok) { Write-Host "=== RESULT: $Step OK ==="; exit 0 } else { Write-Host "=== RESULT: $Step FAILED ==="; exit 1 }
