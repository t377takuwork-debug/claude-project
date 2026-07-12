# vtuber_log draft QA script (ASCII-only source to avoid PS5.1 encoding issues)
# Usage: powershell -ExecutionPolicy Bypass -File tools\qa_draft.ps1 drafts\article.txt
# Exit code: 0 = no ERROR (WARN allowed) / 1 = ERROR found

param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

if (-not (Test-Path $Path)) {
    Write-Output "ERROR: file not found: $Path"
    exit 1
}

$content = Get-Content $Path -Raw -Encoding UTF8
$errors = 0
$warnings = 0

Write-Output "=== vtuber_log qa_draft: $Path ==="

# 1. Block comment open/close balance
#    Open pattern requires a space after the tag name ("<!-- wp:list " matches
#    "<!-- wp:list -->" and "<!-- wp:list {...} -->" but NOT "<!-- wp:list-item").
foreach ($tag in @("paragraph", "heading", "image", "table", "html", "list", "list-item", "embed", "quote", "separator")) {
    $openCount = ([regex]::Matches($content, [regex]::Escape("<!-- wp:$tag") + " ")).Count
    $closeCount = ([regex]::Matches($content, [regex]::Escape("<!-- /wp:$tag -->"))).Count
    if ($openCount -ne $closeCount) {
        Write-Output "[ERROR] wp:$tag open/close mismatch (open=$openCount close=$closeCount)"
        $errors++
    } elseif ($openCount -gt 0) {
        Write-Output "[OK] wp:$tag open=$openCount close=$closeCount"
    }
}

# 2. Total comment delimiters (detects nested-comment accidents)
$openTotal = ([regex]::Matches($content, "<!--")).Count
$closeTotal = ([regex]::Matches($content, "-->")).Count
if ($openTotal -ne $closeTotal) {
    Write-Output "[ERROR] total <!-- vs --> mismatch (open=$openTotal close=$closeTotal). Possible nested comment."
    $errors++
} else {
    Write-Output "[OK] comment totals $openTotal/$closeTotal"
}

# 3. Smart quotes U+2018/2019/201C/201D (break HTML attributes)
$sqPattern = '[' + [char]0x2018 + [char]0x2019 + [char]0x201C + [char]0x201D + ']'
$sq = [regex]::Matches($content, $sqPattern)
if ($sq.Count -gt 0) {
    Write-Output "[ERROR] smart quotes found: $($sq.Count)"
    $errors++
} else {
    Write-Output "[OK] no smart quotes"
}

# 4. JSON-LD syntax (keep first parsed JSON for check 10)
$jsonLd = $null
$scriptMatches = [regex]::Matches($content, '<script type="application/ld\+json">([\s\S]*?)</script>')
if ($scriptMatches.Count -eq 0) {
    Write-Output "[WARN] no JSON-LD block found"
    $warnings++
} else {
    foreach ($m in $scriptMatches) {
        try {
            $parsed = $m.Groups[1].Value | ConvertFrom-Json
            if ($null -eq $jsonLd) { $jsonLd = $parsed }
            Write-Output "[OK] JSON-LD syntax valid"
        } catch {
            Write-Output "[ERROR] JSON-LD syntax invalid: $($_.Exception.Message)"
            $errors++
        }
    }
}

# 5. Pre-publish placeholders (Japanese markers built from code points for ASCII-safety)
#    youShuusei = "needs-fix" marker / shouhinLink = product-link stub
$youShuusei = [string]([char]0x8981) + [char]0x4FEE + [char]0x6B63
$shouhinLink = '\[' + [char]0x5546 + [char]0x54C1 + [char]0x30EA + [char]0x30F3 + [char]0x30AF
$placeholders = @(
    @{ Pattern = 'href="#"';    Label = 'dummy link href="#"' },
    @{ Pattern = $youShuusei;   Label = "needs-fix marker" },
    @{ Pattern = $shouhinLink;  Label = "product-link stub" }
)
foreach ($p in $placeholders) {
    $hits = [regex]::Matches($content, $p.Pattern)
    if ($hits.Count -gt 0) {
        Write-Output "[WARN] $($p.Label): $($hits.Count) (replace before publish)"
        $warnings++
    }
}

# 6. Empty alt attributes
$emptyAlt = [regex]::Matches($content, 'alt=""')
if ($emptyAlt.Count -gt 0) {
    Write-Output "[WARN] images with empty alt: $($emptyAlt.Count)"
    $warnings++
} else {
    Write-Output "[OK] no empty alt"
}

# 7. Nested wp: block comments inside wp:html blocks (output rule 3-2)
$htmlBlocks = [regex]::Matches($content, '<!-- wp:html -->([\s\S]*?)<!-- /wp:html -->')
$nestedCount = 0
foreach ($b in $htmlBlocks) {
    $nestedCount += ([regex]::Matches($b.Groups[1].Value, '<!--\s*/?wp:')).Count
}
if ($nestedCount -gt 0) {
    Write-Output "[ERROR] wp: block comments nested inside wp:html blocks: $nestedCount (rule 3-2)"
    $errors++
} else {
    Write-Output "[OK] no wp: comments nested in wp:html"
}

# 8. Internal links must exist in rules\internal_links.md (link-fabrication guard)
#    Skips /wp-content/ (images). Allowlist: site root and /operator-information/ (fixed JSON-LD data).
$linksFile = Join-Path $PSScriptRoot "..\rules\internal_links.md"
if (Test-Path $linksFile) {
    $linksRaw = Get-Content $linksFile -Raw -Encoding UTF8
    $known = @([regex]::Matches($linksRaw, 'https://vtuber-verse\.com[^\s\)\|<]*') | ForEach-Object { $_.Value.TrimEnd('/') } | Sort-Object -Unique)
    $allow = @('https://vtuber-verse.com', 'https://vtuber-verse.com/operator-information', 'https://vtuber-verse.com/author/vlogyt')
    $draftUrls = @([regex]::Matches($content, 'https://vtuber-verse\.com[^"''\s<\\]*') | ForEach-Object { ($_.Value -split '#')[0].TrimEnd('/') } | Sort-Object -Unique)
    $unknown = @()
    foreach ($u in $draftUrls) {
        if ($u -match '/wp-content/') { continue }
        if ($allow -contains $u) { continue }
        if ($known -contains $u) { continue }
        $unknown += $u
    }
    if ($unknown.Count -gt 0) {
        foreach ($u in $unknown) {
            Write-Output "[ERROR] internal link not in internal_links.md: $u"
        }
        $errors += $unknown.Count
    } else {
        Write-Output "[OK] all internal links exist in internal_links.md ($($draftUrls.Count) urls checked)"
    }
} else {
    Write-Output "[WARN] rules\internal_links.md not found; internal link check skipped"
    $warnings++
}

# 9. MANUAL_JSONLD marker must precede JSON-LD (output rule 7)
if ($scriptMatches.Count -gt 0) {
    if ($content -notmatch '<!-- MANUAL_JSONLD -->') {
        Write-Output "[ERROR] JSON-LD present but <!-- MANUAL_JSONLD --> marker missing (rule 7)"
        $errors++
    } else {
        Write-Output "[OK] MANUAL_JSONLD marker present"
    }
}

# 10. JSON-LD vs body sync (headline = draft title line / FAQ count = body Q&A count)
if ($null -ne $jsonLd) {
    if ($null -ne $jsonLd.'@graph') { $nodes = @($jsonLd.'@graph') } else { $nodes = @($jsonLd) }

    # 10a. headline vs title line ("titleMarker" = Japanese "taitoru:" built from code points)
    $titleMarker = [string]([char]0x30BF) + [char]0x30A4 + [char]0x30C8 + [char]0x30EB + [char]0xFF1A
    $titleMatch = [regex]::Match($content, '(?m)^\s*' + [regex]::Escape($titleMarker) + '(.+)$')
    $blogPost = $nodes | Where-Object { $_.'@type' -eq 'BlogPosting' } | Select-Object -First 1
    if (-not $titleMatch.Success) {
        Write-Output "[WARN] draft title line (taitoru:) not found; headline sync check skipped"
        $warnings++
    } elseif ($null -eq $blogPost) {
        Write-Output "[WARN] no BlogPosting node in JSON-LD; headline sync check skipped"
        $warnings++
    } else {
        $draftTitle = $titleMatch.Groups[1].Value.Trim()
        $headline = [string]$blogPost.headline
        if ($headline.Trim() -ne $draftTitle) {
            Write-Output "[ERROR] JSON-LD headline differs from draft title line"
            Write-Output "        draft   : $draftTitle"
            Write-Output "        headline: $headline"
            $errors++
        } else {
            Write-Output "[OK] JSON-LD headline matches draft title line"
        }
    }

    # 10b. FAQPage question count vs body Q&A markers (>Q1</span> style)
    $faqNode = $nodes | Where-Object { $_.'@type' -eq 'FAQPage' } | Select-Object -First 1
    $bodyQ = ([regex]::Matches($content, '>Q\d+</span>')).Count
    if ($null -ne $faqNode) {
        $faqCount = @($faqNode.mainEntity).Count
        if ($bodyQ -eq 0) {
            Write-Output "[WARN] FAQPage in JSON-LD but no Q-number markers found in body (check manually)"
            $warnings++
        } elseif ($faqCount -ne $bodyQ) {
            Write-Output "[WARN] FAQPage question count ($faqCount) differs from body Q&A markers ($bodyQ)"
            $warnings++
        } else {
            Write-Output "[OK] FAQPage count matches body Q&A ($faqCount)"
        }
    } elseif ($bodyQ -gt 0) {
        Write-Output "[WARN] body has $bodyQ Q&A markers but JSON-LD has no FAQPage node"
        $warnings++
    }
}

# 11. Body internal link count (rule: 2-6 links, no duplicates; see rules\internal_links.md)
#     Counts href= links to vtuber-verse.com pages (JSON-LD @id/url values have no href=, images excluded).
$bodyLinkUrls = @([regex]::Matches($content, 'href="(https://vtuber-verse\.com/[^"]*)"') | ForEach-Object { ($_.Groups[1].Value -split '#')[0].TrimEnd('/') } | Where-Object { $_ -notmatch '/wp-content/' })
$uniqueLinks = @($bodyLinkUrls | Sort-Object -Unique)
$dupCount = $bodyLinkUrls.Count - $uniqueLinks.Count
if ($uniqueLinks.Count -eq 0) {
    Write-Output "[WARN] no internal links in body (guideline: 2-6; add related-article links)"
    $warnings++
} elseif ($uniqueLinks.Count -gt 6) {
    Write-Output "[WARN] too many internal links in body: $($uniqueLinks.Count) unique (guideline: 2-6)"
    $warnings++
} else {
    Write-Output "[OK] body internal links: $($uniqueLinks.Count) unique (guideline 2-6)"
}
if ($dupCount -gt 0) {
    Write-Output "[WARN] duplicate internal links to same URL: $dupCount extra (1 link per URL per article)"
    $warnings++
}

# 12. Image src must be an absolute or protocol-relative web URL
#     (catches local paths / placeholders; "//host/..." is valid, used by affiliate pixels)
$imgSrcs = @([regex]::Matches($content, '<img[^>]*\ssrc="([^"]*)"') | ForEach-Object { $_.Groups[1].Value })
$badSrcs = @($imgSrcs | Where-Object { $_ -notmatch '^(https?:)?//' })
if ($badSrcs.Count -gt 0) {
    foreach ($s in $badSrcs) {
        Write-Output "[ERROR] img src is not an uploaded URL (local path or placeholder): $s"
    }
    $errors += $badSrcs.Count
} elseif ($imgSrcs.Count -gt 0) {
    Write-Output "[OK] all $($imgSrcs.Count) img src are absolute URLs"
}

# Summary
Write-Output "=== RESULT: ERROR $errors / WARN $warnings ==="
if ($errors -gt 0) { exit 1 } else { exit 0 }
