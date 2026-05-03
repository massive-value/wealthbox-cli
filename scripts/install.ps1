# wealthbox-cli bootstrap installer (Windows).
#
# One-line install:
#   irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex
#
# Installs uv (if missing), installs wealthbox-cli as an isolated tool,
# prompts for the API token, and offers to install the AI agent skill.

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

# 'pending', 'succeeded', 'user-action', 'errored'.
# 'user-action' = clean early-exit because the user needs to do something
# manual (e.g., declined to flip ExecutionPolicy). NOT an error.
$state = 'pending'

try {
    Write-Host "=== wealthbox-cli installer ===" -ForegroundColor Cyan

    Write-Step "Checking PowerShell execution policy..."
    # uv's installer requires Unrestricted, RemoteSigned, or Bypass. The
    # Windows-client default is Restricted, which blocks uv from running.
    # Detect this upfront and offer to fix it (CurrentUser scope, no
    # admin required) so the user doesn't have to re-run the installer.
    $policy = Get-ExecutionPolicy
    $allowed = @('Unrestricted', 'RemoteSigned', 'Bypass')
    if ($policy -notin $allowed) {
        Write-Host ""
        Write-Host "  Your execution policy is '$policy'. uv's installer needs at least"
        Write-Host "  'RemoteSigned' to run."
        Write-Host ""
        Write-Host "  'RemoteSigned' is Microsoft's recommended developer-machine default."
        Write-Host "  It allows your local scripts to run, while still requiring signatures"
        Write-Host "  on scripts downloaded from the internet."
        Write-Host ""
        $confirm = Read-Host "  Set RemoteSigned for your user account now? [Y/n]"
        if ($confirm -match '^[Nn]') {
            Write-Host ""
            Write-Host "  Skipped. To enable later, run:" -ForegroundColor Yellow
            Write-Host "      Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
            Write-Host "      irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex"
            $state = 'user-action'
            return
        }
        try {
            Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "  Policy updated to RemoteSigned (CurrentUser scope)."
        } catch {
            Write-Host ""
            Write-Host "  Couldn't update policy: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  Run manually, then re-run the installer:"
            Write-Host "      Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
            $state = 'user-action'
            return
        }
    } else {
        Write-Host "  Policy: $policy (OK)"
    }

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
        $state = 'user-action'
        return
    }
    Write-Host "  wbox found at $((Get-Command wbox).Source)"

    Write-Step "Configuring API token..."
    Write-Host "  Get your Wealthbox API token at https://dev.wealthbox.com"
    Write-Host "  (Settings -> API Access -> Access Tokens)"
    Write-Host ""
    wbox config set-token

    Write-Step "AI agent skill setup..."
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        # Claude Code is installed — use the plugin marketplace path.
        # Recommended setup: plugin auto-updates daily, firm data lives
        # at the canonical machine path (independent of plugin version),
        # and the install is a single CLI invocation.
        Write-Host "  Claude Code detected. Installing wealthbox-crm via the plugin marketplace..."
        try {
            claude plugin marketplace add massive-value/wealthbox-cli 2>&1 | Out-Host
        } catch {
            Write-Host "  (marketplace 'massive-value' may already be configured - continuing)"
        }
        try {
            claude plugin install wealthbox-crm@massive-value 2>&1 | Out-Host
            Write-Host "  Installed." -ForegroundColor Green
        } catch {
            Write-Host "  Plugin install failed. Fall back: wbox skills install --platform claude-code-user" -ForegroundColor Yellow
        }

        Write-Host ""
        $installCodex = Read-Host "  Also install for Codex (separate AI agent)? [y/N]"
        if ($installCodex -match '^[Yy]') {
            wbox skills install --platform codex
        }
    } else {
        # No `claude` CLI — fall back to the legacy wbox skills install
        # interactive picker (handles Codex / project-scope / etc.).
        $installSkill = Read-Host "  Install the AI agent skill (Claude Code / Codex)? [Y/n]"
        if ($installSkill -match '^[Nn]') {
            Write-Host "  Skipped. Run 'wbox skills install' anytime."
        } else {
            wbox skills install
        }
    }

    Write-Host ""
    Write-Host "Done." -ForegroundColor Green
    Write-Host "If 'wbox me' returns 'command not found' in a new terminal, that"
    Write-Host "shell hasn't picked up the user PATH update yet. Sign out and"
    Write-Host "back in (or restart Windows Terminal completely). Then: wbox me"
    $state = 'succeeded'
}
catch {
    $state = 'errored'
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
    if ($state -eq 'errored') {
        Write-Host "Press Enter to close this window (an error occurred)..." -ForegroundColor Yellow
    } else {
        Write-Host "Press Enter to close this window..." -ForegroundColor DarkGray
    }
    try { $null = Read-Host } catch { Start-Sleep -Seconds 30 }
}
