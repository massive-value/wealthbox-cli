# wealthbox-cli bootstrap installer (Windows).
#
# One-line install:
#   irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex
#
# Installs uv (if missing), installs wealthbox-cli as an isolated tool,
# prompts for the API token, and offers to install the AI agent skill.
#
# Wrapped in a try/finally so the window stays open long enough to read
# the result even if the parent shell would otherwise auto-close on exit.

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

$installerSucceeded = $false

try {
    Write-Host "=== wealthbox-cli installer ===" -ForegroundColor Cyan

    Write-Step "Checking for uv (Python tool manager)..."
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "  uv not found. Installing from astral.sh..."
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    } else {
        Write-Host "  uv found at $((Get-Command uv).Source)"
    }

    Write-Step "Installing or upgrading wealthbox-cli..."
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
        Write-Host "  Upgrading existing wealthbox-cli install..."
        uv tool upgrade wealthbox-cli
    } else {
        Write-Host "  Installing wealthbox-cli..."
        uv tool install wealthbox-cli
    }

    # uv installs tool entry points to %USERPROFILE%\.local\bin; ensure
    # it's on PATH for the rest of this session.
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

    Write-Step "Verifying wbox is on PATH..."
    if (-not (Get-Command wbox -ErrorAction SilentlyContinue)) {
        Write-Host "  wbox installed but not on PATH in this shell." -ForegroundColor Yellow
        Write-Host "  Open a new terminal and run:"
        Write-Host "    wbox config set-token"
        Write-Host "    wbox skills install"
        $installerSucceeded = $true
        return
    }
    Write-Host "  wbox found at $((Get-Command wbox).Source)"

    Write-Step "Configuring API token..."
    Write-Host "  Get your Wealthbox API token at https://dev.wealthbox.com"
    Write-Host "  (Settings -> API Access -> Access Tokens)"
    Write-Host ""
    wbox config set-token

    Write-Step "Skill install..."
    $installSkill = Read-Host "Install the AI agent skill (Claude Code / Codex)? [Y/n]"
    if ($installSkill -match '^[Nn]') {
        Write-Host "  Skipped. Run 'wbox skills install' anytime."
    } else {
        wbox skills install
    }

    Write-Host ""
    Write-Host "Done." -ForegroundColor Green
    Write-Host "If 'wbox me' returns 'command not found' in a new terminal, that"
    Write-Host "shell hasn't picked up the user PATH update yet. Sign out and"
    Write-Host "back in (or restart Windows Terminal completely). Then: wbox me"
    $installerSucceeded = $true
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.InvocationInfo) {
        Write-Host "  at $($_.InvocationInfo.PositionMessage)" -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "Please report this at:" -ForegroundColor Yellow
    Write-Host "  https://github.com/massive-value/wealthbox-cli/issues"
}
finally {
    # Keep the window open if this is a transient PowerShell host (e.g.
    # double-click, `Run with PowerShell`, or `powershell -Command`),
    # which would otherwise close as soon as the script returns.
    Write-Host ""
    if ($installerSucceeded) {
        Write-Host "Press Enter to close this window..." -ForegroundColor DarkGray
    } else {
        Write-Host "Press Enter to close this window (an error occurred)..." -ForegroundColor Yellow
    }
    try { $null = Read-Host } catch { Start-Sleep -Seconds 30 }
}
