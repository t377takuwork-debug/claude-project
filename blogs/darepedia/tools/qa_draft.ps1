# darepedia draft QA script (ASCII-only source to avoid PS5.1 encoding issues)
# Usage: powershell -ExecutionPolicy Bypass -File tools\qa_draft.ps1 drafts\draft_slug.txt
# Exit code: 0 = no ERROR (WARN allowed) / 1 = ERROR found
#
# 2026-08-26 rewrite: darepedia uses the same Gutenberg block-comment format as
# shira_note/cf_room ("<!-- wp:xxx -->" wrappers around real <h2>/<h3> tags),
# not plain unwrapped HTML. This script checks wp: block balance the same way
# cf_room's qa_draft.ps1 does, plus darepedia-specific structural markers.

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

Write-Output "=== darepedia qa_draft: $Path ==="

# Japanese literals built from code points (ASCII-safe source file)
$titleMarker = [string]([char]0x30BF) + [char]0x30A4 + [char]0x30C8 + [char]0x30EB + [char]0xFF1A          # "taitoru:"
$matomeWord  = [string]([char]0x307E) + [char]0x3068 + [char]0x3081                                          # "matome"
$faqWord     = [string]([char]0x3088) + [char]0x304F + [char]0x3042 + [char]0x308B + [char]0x8CEA + [char]0x554F  # "yoku aru shitsumon"
$metaMarker  = [string]([char]0x30E1) + [char]0x30BF + [char]0x30C7 + [char]0x30A3 + [char]0x30B9 + [char]0x30AF + [char]0x30EA + [char]0x30D7 + [char]0x30B7 + [char]0x30E7 + [char]0x30F3  # "meta description" (no trailing colon; actual line is "...(n-ji):")

# 1. Block comment open/close balance (wp:paragraph / wp:heading / wp:html)
foreach ($tag in @("paragraph", "heading", "html")) {
    $openCount = ([regex]::Matches($content, [regex]::Escape("<!-- wp:$tag"))).Count
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

# 3. Title line present (inside the opening wp:paragraph block)
$titleMatch = [regex]::Match($content, '(?m)^\s*' + [regex]::Escape($titleMarker) + '(.+)$')
if (-not $titleMatch.Success) {
    Write-Output "[ERROR] title line (taitoru:) not found"
    $errors++
} else {
    Write-Output "[OK] title line found: $($titleMatch.Groups[1].Value.Trim())"
}

# 4. Meta description line present
if ($content -notmatch [regex]::Escape($metaMarker)) {
    Write-Output "[WARN] meta description line not found"
    $warnings++
} else {
    Write-Output "[OK] meta description line found"
}

# 5. H2 heading count (inside wp:heading blocks) and matome ending
$h2Texts = [regex]::Matches($content, '<h2[^>]*>([\s\S]*?)</h2>')
if ($h2Texts.Count -eq 0) {
    Write-Output "[ERROR] no <h2> heading found"
    $errors++
} else {
    Write-Output "[OK] h2 count=$($h2Texts.Count)"
    $lastH2 = $h2Texts[$h2Texts.Count - 1]
    if ($lastH2.Groups[1].Value -notmatch [regex]::Escape($matomeWord)) {
        Write-Output "[WARN] last <h2> does not contain 'matome' (summary heading may be missing)"
        $warnings++
    } else {
        $afterLast = $content.Substring($lastH2.Index + $lastH2.Length)
        if ($afterLast -match '<h3[\s>]') {
            Write-Output "[WARN] <h3> found after the final matome <h2> (matome should have no h3)"
            $warnings++
        } else {
            Write-Output "[OK] article ends with matome h2, no trailing h3"
        }
    }
}

# 6. H3 must carry the level:3 attribute (otherwise Gutenberg coerces it to h2 on save)
$h3Tags = ([regex]::Matches($content, '<h3[\s>]')).Count
$h3WithLevel = ([regex]::Matches($content, '<!--\s*wp:heading\s*\{"level":3\}\s*-->\s*<h3[\s>]')).Count
if ($h3Tags -gt 0 -and $h3Tags -ne $h3WithLevel) {
    Write-Output "[ERROR] some <h3> tags are missing the wp:heading {`"level`":3} attribute (open=$h3Tags with-attr=$h3WithLevel)"
    $errors++
} elseif ($h3Tags -gt 0) {
    Write-Output "[OK] all $h3Tags h3 headings carry the level:3 attribute"
}

# 7. FAQ heading present
if ($content -notmatch [regex]::Escape($faqWord)) {
    Write-Output "[WARN] no FAQ heading (yoku aru shitsumon) found"
    $warnings++
} else {
    Write-Output "[OK] FAQ heading found"
}

# 8. Smart quotes U+2018/2019/201C/201D (break HTML attributes)
$sqPattern = '[' + [char]0x2018 + [char]0x2019 + [char]0x201C + [char]0x201D + ']'
$sq = [regex]::Matches($content, $sqPattern)
if ($sq.Count -gt 0) {
    Write-Output "[ERROR] smart quotes found: $($sq.Count)"
    $errors++
} else {
    Write-Output "[OK] no smart quotes"
}

# 9. Nested wp: block comments inside wp:html blocks (rule 5 in wordpress_output_rules.md)
$htmlBlocks = [regex]::Matches($content, '<!-- wp:html -->([\s\S]*?)<!-- /wp:html -->')
$nestedCount = 0
foreach ($b in $htmlBlocks) {
    $nestedCount += ([regex]::Matches($b.Groups[1].Value, '<!--\s*/?wp:')).Count
}
if ($nestedCount -gt 0) {
    Write-Output "[ERROR] wp: block comments nested inside wp:html blocks: $nestedCount"
    $errors++
} else {
    Write-Output "[OK] no wp: comments nested in wp:html"
}

# 10. Shortcodes must be alone in their own wp:paragraph (not mixed with other text)
foreach ($sc in @("title", "mokujimae", "originalsc")) {
    $tag = "[nopc][$sc][/nopc]"
    $mixed = [regex]::Matches($content, '<p>(?!\s*' + [regex]::Escape($tag) + '\s*</p>)[^<]*' + [regex]::Escape($tag) + '|' + [regex]::Escape($tag) + '(?!\s*</p>)[^<]*<')
    if ($mixed.Count -gt 0) {
        Write-Output "[ERROR] shortcode $tag is mixed with other text in the same block (must be alone in its own wp:paragraph)"
        $errors++
    }
}

# 11. Placeholder href="#"
$dummyHref = [regex]::Matches($content, 'href="#"')
if ($dummyHref.Count -gt 0) {
    Write-Output "[WARN] dummy link href=`"#`": $($dummyHref.Count) (replace before publish)"
    $warnings++
}

# 12. Empty alt attributes
$emptyAlt = [regex]::Matches($content, 'alt=""')
if ($emptyAlt.Count -gt 0) {
    Write-Output "[WARN] images with empty alt: $($emptyAlt.Count)"
    $warnings++
}

# 13. Internal links must exist in rules\internal_links.md (link-fabrication guard)
$linksFile = Join-Path $PSScriptRoot "..\rules\internal_links.md"
if (Test-Path $linksFile) {
    $linksRaw = Get-Content $linksFile -Raw -Encoding UTF8
    $known = @([regex]::Matches($linksRaw, 'https://darepedia\.com[^\s\)\|<]*') | ForEach-Object { $_.Value.TrimEnd('/') } | Sort-Object -Unique)
    $allow = @('https://darepedia.com')
    $draftUrls = @([regex]::Matches($content, 'href="(https://darepedia\.com[^"]*)"') | ForEach-Object { ($_.Groups[1].Value -split '#')[0].TrimEnd('/') } | Sort-Object -Unique)
    $unknown = @()
    foreach ($u in $draftUrls) {
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

# 14. JSON-LD syntax (optional; darepedia does not require JSON-LD, but validate if present)
$scriptMatches = [regex]::Matches($content, '<script type="application/ld\+json">([\s\S]*?)</script>')
if ($scriptMatches.Count -gt 0) {
    foreach ($m in $scriptMatches) {
        try {
            $null = $m.Groups[1].Value | ConvertFrom-Json
            Write-Output "[OK] JSON-LD syntax valid"
        } catch {
            Write-Output "[ERROR] JSON-LD syntax invalid: $($_.Exception.Message)"
            $errors++
        }
    }
}

# Summary
Write-Output "=== RESULT: ERROR $errors / WARN $warnings ==="
if ($errors -gt 0) { exit 1 } else { exit 0 }
