# wealthbox-cli bootstrap installer (Windows).
#
# One-line install:
#   irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex
#
# Downloads the prebuilt `wbox` binary from the latest GitHub Release,
# verifies its SHA-256 against the published manifest, places it on the
# user's PATH, then installs the AI agent skill, prompts for the API
# token, and offers to bootstrap the firm directory.
#
# No admin elevation is required: the binary is installed to
# %LOCALAPPDATA%\Programs\wbox\wbox.exe and PATH is mutated at user
# scope. Re-running the script is idempotent — it overwrites the binary
# in place, leaves PATH alone if already correct, and reuses any
# previously stored token / firm data.
#
# Usage:
#   .\install.ps1            # full install
#   .\install.ps1 -DryRun    # describe what would happen; no state changes

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

$script:Repo               = 'massive-value/wealthbox-cli'
$script:ReleaseApiUrl      = "https://api.github.com/repos/$script:Repo/releases/latest"
$script:BinaryAssetName    = 'wbox-windows-x64.exe'
$script:ManifestAssetName  = 'SHA256SUMS.txt'
$script:InstallDir         = Join-Path $env:LOCALAPPDATA 'Programs\wbox'
$script:InstalledBinary    = Join-Path $script:InstallDir 'wbox.exe'

# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message"
}

function Write-DryRun {
    param([string]$Message)
    Write-Host "    [dry-run] $Message" -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# Step 1 — detect-platform
# ---------------------------------------------------------------------------

function Step-DetectPlatform {
    Write-Step 'Detecting platform...'
    # Issue #33 only ships windows-x64 for Windows. The pre-built binary
    # is a 64-bit PE32+, so even on ARM64 Windows it would run under
    # x64 emulation but would fail on a 32-bit host.
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw 'wealthbox-cli requires 64-bit Windows; this host is 32-bit.'
    }
    $target = 'windows-x64'
    Write-Info "Target: $target"
    return $target
}

# ---------------------------------------------------------------------------
# Step 2 — resolve-release-via-github-api
# ---------------------------------------------------------------------------

function Step-ResolveRelease {
    Write-Step 'Resolving latest release from GitHub...'
    Write-Info "GET $script:ReleaseApiUrl"
    try {
        # Anonymous request — no token. GitHub allows ~60 unauthenticated
        # requests per IP per hour, which is plenty for an installer.
        $response = Invoke-RestMethod -Uri $script:ReleaseApiUrl `
            -UseBasicParsing `
            -Headers @{ 'User-Agent' = 'wealthbox-cli-installer'; 'Accept' = 'application/vnd.github+json' }
    } catch {
        $status = $null
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        if ($status -eq 403) {
            throw 'GitHub API returned 403 (rate-limited or forbidden). Wait an hour and re-run, or set GITHUB_TOKEN and retry.'
        }
        if ($status -eq 404) {
            throw "GitHub API returned 404 — repository '$script:Repo' has no published releases yet."
        }
        throw "GitHub API request failed: $($_.Exception.Message)"
    }

    $tag = $response.tag_name
    if (-not $tag) {
        throw 'GitHub release payload missing tag_name.'
    }

    $assets = @($response.assets)
    $binaryAsset   = $assets | Where-Object { $_.name -eq $script:BinaryAssetName }   | Select-Object -First 1
    $manifestAsset = $assets | Where-Object { $_.name -eq $script:ManifestAssetName } | Select-Object -First 1
    if (-not $binaryAsset) {
        throw "Release $tag is missing asset '$script:BinaryAssetName'."
    }
    if (-not $manifestAsset) {
        throw "Release $tag is missing asset '$script:ManifestAssetName'."
    }

    Write-Info "Tag: $tag"
    Write-Info "Binary URL:   $($binaryAsset.browser_download_url)"
    Write-Info "Manifest URL: $($manifestAsset.browser_download_url)"

    return [pscustomobject]@{
        Tag         = $tag
        BinaryUrl   = $binaryAsset.browser_download_url
        ManifestUrl = $manifestAsset.browser_download_url
    }
}

# ---------------------------------------------------------------------------
# Step 3 — download
# ---------------------------------------------------------------------------

function Step-Download {
    param(
        [Parameter(Mandatory)] [string]$BinaryUrl,
        [Parameter(Mandatory)] [string]$ManifestUrl
    )
    Write-Step 'Downloading binary and manifest...'

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("wbox-install-" + [guid]::NewGuid().ToString('N'))
    $binaryPath   = Join-Path $tempRoot $script:BinaryAssetName
    $manifestPath = Join-Path $tempRoot $script:ManifestAssetName

    if ($DryRun) {
        Write-DryRun "would create temp dir $tempRoot"
        Write-DryRun "would download $BinaryUrl  -> $binaryPath"
        Write-DryRun "would download $ManifestUrl -> $manifestPath"
        return [pscustomobject]@{
            TempRoot     = $tempRoot
            BinaryPath   = $binaryPath
            ManifestPath = $manifestPath
        }
    }

    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Write-Info "Temp dir: $tempRoot"

    Write-Info "Fetching $script:BinaryAssetName ..."
    Invoke-WebRequest -Uri $BinaryUrl -OutFile $binaryPath -UseBasicParsing `
        -Headers @{ 'User-Agent' = 'wealthbox-cli-installer' }

    Write-Info "Fetching $script:ManifestAssetName ..."
    Invoke-WebRequest -Uri $ManifestUrl -OutFile $manifestPath -UseBasicParsing `
        -Headers @{ 'User-Agent' = 'wealthbox-cli-installer' }

    return [pscustomobject]@{
        TempRoot     = $tempRoot
        BinaryPath   = $binaryPath
        ManifestPath = $manifestPath
    }
}

# ---------------------------------------------------------------------------
# Step 4 — verify-checksum
# ---------------------------------------------------------------------------

function Step-VerifyChecksum {
    param(
        [Parameter(Mandatory)] [string]$BinaryPath,
        [Parameter(Mandatory)] [string]$ManifestPath
    )
    Write-Step 'Verifying SHA-256 checksum...'

    if ($DryRun) {
        Write-DryRun "would parse $ManifestPath and verify $BinaryPath"
        return
    }

    # Manifest format: "<hex-sha256><two-spaces><filename>", one per line,
    # ASCII-sorted by filename. See release-binaries.yml.
    $manifestLines = Get-Content -LiteralPath $ManifestPath -ErrorAction Stop
    $expected = $null
    foreach ($line in $manifestLines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $trimmed -split '\s+', 2
        if ($parts.Length -ne 2) { continue }
        $name = $parts[1].TrimStart('*').Trim()
        if ($name -eq $script:BinaryAssetName) {
            $expected = $parts[0].ToLower()
            break
        }
    }
    if (-not $expected) {
        throw "Manifest does not contain a SHA-256 entry for $script:BinaryAssetName."
    }

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $BinaryPath).Hash.ToLower()
    Write-Info "Expected: $expected"
    Write-Info "Actual:   $actual"
    if ($actual -ne $expected) {
        throw "SHA-256 mismatch for $script:BinaryAssetName (expected $expected, got $actual)."
    }
    Write-Info 'Checksum OK.'
}

# ---------------------------------------------------------------------------
# Step 5 — place-on-path
# ---------------------------------------------------------------------------

function Step-PlaceOnPath {
    param(
        [Parameter(Mandatory)] [string]$BinaryPath
    )
    Write-Step 'Installing binary and updating PATH...'
    Write-Info "Install dir: $script:InstallDir"
    Write-Info "Target:      $script:InstalledBinary"

    if ($DryRun) {
        Write-DryRun "would create $script:InstallDir"
        Write-DryRun "would copy $BinaryPath -> $script:InstalledBinary"
        Write-DryRun "would ensure $script:InstallDir is on the User PATH"
        return
    }

    if (-not (Test-Path -LiteralPath $script:InstallDir)) {
        New-Item -ItemType Directory -Path $script:InstallDir -Force | Out-Null
    }

    # Copy-Item overwrites by default; idempotent on re-runs (upgrades in
    # place). Use -Force to handle the read-only attribute that occasionally
    # gets sticky on Windows-downloaded files.
    Copy-Item -LiteralPath $BinaryPath -Destination $script:InstalledBinary -Force

    # User-scope PATH mutation (no admin / setx /M). Read the persisted
    # value (NOT $env:Path, which is the merged process view) so we don't
    # accidentally write the merged System+User PATH back into User scope.
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (-not $userPath) { $userPath = '' }
    $segments = $userPath -split ';' | Where-Object { $_ -and $_.Trim() }
    $alreadyOnPath = $false
    foreach ($segment in $segments) {
        if ($segment.TrimEnd('\') -ieq $script:InstallDir.TrimEnd('\')) {
            $alreadyOnPath = $true
            break
        }
    }

    if ($alreadyOnPath) {
        Write-Info "PATH already contains $script:InstallDir."
    } else {
        $newUserPath = if ($userPath) { "$userPath;$script:InstallDir" } else { $script:InstallDir }
        [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
        Write-Info "Added $script:InstallDir to your User PATH."
        Write-Info '(Open a new terminal to pick up the change in fresh shells.)'
    }

    # Also update this process so the rest of the installer can call wbox.
    if (($env:Path -split ';') -notcontains $script:InstallDir) {
        $env:Path = "$script:InstallDir;$env:Path"
    }
}

# ---------------------------------------------------------------------------
# Step 6 — invoke `wbox skills install`
# ---------------------------------------------------------------------------

function Step-InstallSkills {
    Write-Step 'Installing AI agent skill...'
    if ($DryRun) {
        Write-DryRun "would run $script:InstalledBinary skills install --no-bootstrap"
        return
    }
    if (-not (Test-Path -LiteralPath $script:InstalledBinary)) {
        Write-Host '    Skipped: wbox.exe is not on disk.' -ForegroundColor Yellow
        return
    }
    # --no-bootstrap so the install does not prompt to firm-bootstrap
    # before we have a token. Step 8 (Step-OfferFirmBootstrap) handles
    # the bootstrap explicitly, after the token is configured.
    & $script:InstalledBinary skills install --no-bootstrap
    if ($LASTEXITCODE -ne 0) {
        throw "wbox skills install exited with code $LASTEXITCODE."
    }
}

# ---------------------------------------------------------------------------
# Step 7 — prompt-for-token
# ---------------------------------------------------------------------------

function Step-PromptForToken {
    Write-Step 'Configuring API token...'
    if ($DryRun) {
        Write-DryRun "would run $script:InstalledBinary config set-token"
        return
    }
    if (-not (Test-Path -LiteralPath $script:InstalledBinary)) {
        Write-Host '    Skipped: wbox.exe is not on disk.' -ForegroundColor Yellow
        return
    }
    Write-Info 'Get your Wealthbox API token at https://dev.wealthbox.com'
    Write-Info '(Settings -> API Access -> Access Tokens)'
    Write-Host ''
    & $script:InstalledBinary config set-token
    if ($LASTEXITCODE -ne 0) {
        throw "wbox config set-token exited with code $LASTEXITCODE."
    }
}

# ---------------------------------------------------------------------------
# Step 8 — offer-firm-bootstrap
# ---------------------------------------------------------------------------

function Step-OfferFirmBootstrap {
    Write-Step 'Firm bootstrap...'
    if ($DryRun) {
        Write-DryRun "would prompt user; on yes, run $script:InstalledBinary skills bootstrap"
        return
    }
    if (-not (Test-Path -LiteralPath $script:InstalledBinary)) {
        Write-Host '    Skipped: wbox.exe is not on disk.' -ForegroundColor Yellow
        return
    }
    Write-Info 'Bootstrap fetches your firm directory (users, categories, workflows)'
    Write-Info 'from the Wealthbox API. Safe to re-run anytime via `wbox skills bootstrap`.'
    Write-Host ''
    $reply = Read-Host '    Bootstrap firm data now? [Y/n]'
    if ($reply -match '^[Nn]') {
        Write-Info "Skipped. Run 'wbox skills bootstrap' anytime."
        return
    }
    & $script:InstalledBinary skills bootstrap
    if ($LASTEXITCODE -ne 0) {
        throw "wbox skills bootstrap exited with code $LASTEXITCODE."
    }
}

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

# 'pending', 'succeeded', 'errored'.
$state = 'pending'

try {
    Write-Host '=== wealthbox-cli installer ===' -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host '(dry-run mode — no files or PATH will be modified)' -ForegroundColor DarkGray
    }

    $null       = Step-DetectPlatform
    $release    = Step-ResolveRelease
    $downloaded = Step-Download -BinaryUrl $release.BinaryUrl -ManifestUrl $release.ManifestUrl
    try {
        Step-VerifyChecksum -BinaryPath $downloaded.BinaryPath -ManifestPath $downloaded.ManifestPath
        Step-PlaceOnPath -BinaryPath $downloaded.BinaryPath
    }
    finally {
        if (-not $DryRun -and $downloaded.TempRoot -and (Test-Path -LiteralPath $downloaded.TempRoot)) {
            Remove-Item -LiteralPath $downloaded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Step-InstallSkills
    Step-PromptForToken
    Step-OfferFirmBootstrap

    Write-Host ''
    Write-Host 'Done.' -ForegroundColor Green
    Write-Host "Binary installed at: $script:InstalledBinary"
    Write-Host "If 'wbox me' returns 'command not found' in a new terminal,"
    Write-Host 'sign out and back in (or restart Windows Terminal completely)'
    Write-Host 'so the User PATH update propagates to fresh shells.'
    $state = 'succeeded'
}
catch {
    $state = 'errored'
    Write-Host ''
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.InvocationInfo) {
        Write-Host "  at $($_.InvocationInfo.PositionMessage)" -ForegroundColor DarkGray
    }
    Write-Host ''
    Write-Host 'Please report this at:' -ForegroundColor Yellow
    Write-Host "  https://github.com/$script:Repo/issues"
}
finally {
    # Keep the window open if this is a transient PowerShell host (e.g.
    # double-click, `Run with PowerShell`, or `powershell -Command`),
    # which would otherwise close as soon as the script returns.
    Write-Host ''
    if ($state -eq 'errored') {
        Write-Host 'Press Enter to close this window (an error occurred)...' -ForegroundColor Yellow
    } else {
        Write-Host 'Press Enter to close this window...' -ForegroundColor DarkGray
    }
    try { $null = Read-Host } catch { Start-Sleep -Seconds 30 }
    # Surface failure to callers (CI wrappers, `powershell -File ...`,
    # bootstrap scripts) so they can detect install failures via exit code.
    if ($state -eq 'errored') { exit 1 }
}
