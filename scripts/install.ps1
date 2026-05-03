# wealthbox-cli bootstrap installer (Windows).
#
# One-line install:
#   irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex
#
# Installs uv (if missing), installs wealthbox-cli as an isolated tool,
# prompts for the API token, and offers to install the AI agent skill.
$ErrorActionPreference = "Stop"

Write-Host "=== wealthbox-cli installer ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv (Python tool manager)..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

$installed = $false
try {
    $toolList = (uv tool list 2>$null) -join "`n"
    if ($toolList -match '(?m)^wealthbox-cli\s') {
        $installed = $true
    }
} catch {
    $installed = $false
}

if ($installed) {
    Write-Host "Upgrading wealthbox-cli to latest..."
    uv tool upgrade wealthbox-cli
} else {
    Write-Host "Installing wealthbox-cli..."
    uv tool install wealthbox-cli
}

# uv installs tool entry points to %USERPROFILE%\.local\bin; ensure it's
# on PATH for the rest of this session.
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

if (-not (Get-Command wbox -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "wbox installed but not on PATH in this shell." -ForegroundColor Yellow
    Write-Host "Open a new terminal and run:"
    Write-Host "    wbox config set-token"
    Write-Host "    wbox skills install"
    return
}

Write-Host ""
Write-Host "Get your Wealthbox API token at https://dev.wealthbox.com"
Write-Host "(Settings -> API Access -> Access Tokens)"
Write-Host ""
wbox config set-token

Write-Host ""
$installSkill = Read-Host "Install the AI agent skill (Claude Code / Codex)? [Y/n]"
if ($installSkill -match '^[Nn]') {
    Write-Host "Skipped. Run 'wbox skills install' anytime."
} else {
    wbox skills install
}

Write-Host ""
Write-Host "Done. Try: wbox me" -ForegroundColor Green
