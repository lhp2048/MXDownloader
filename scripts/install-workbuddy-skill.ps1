# Install Family Media Center WorkBuddy Skill
# Usage:
#   .\scripts\install-workbuddy-skill.ps1
#   .\scripts\install-workbuddy-skill.ps1 -BaseUrl "http://192.168.2.11:18026"

param(
    [string]$BaseUrl = ""
)

$ErrorActionPreference = "Stop"

$SkillName = "family-mediacenter"
$Dest = Join-Path $env:USERPROFILE ".workbuddy\skills\$SkillName"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LocalSrc = Join-Path $ProjectRoot "skills\$SkillName"

function Write-Log {
    param([string]$Message)
    Write-Host "[install-workbuddy-skill] $Message"
}

function Install-FromLocal {
    $skillFile = Join-Path $LocalSrc "SKILL.md"
    if (-not (Test-Path $skillFile)) {
        throw "SKILL.md not found: $skillFile"
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $Dest "references") | Out-Null
    Copy-Item $skillFile (Join-Path $Dest "SKILL.md") -Force
    $apiRef = Join-Path $LocalSrc "references\api.md"
    if (Test-Path $apiRef) {
        Copy-Item $apiRef (Join-Path $Dest "references\api.md") -Force
    }
    Write-Log "Installed from local repository"
}

function Install-FromUrl {
    param([string]$Base)
    $base = $Base.TrimEnd("/")
    New-Item -ItemType Directory -Force -Path (Join-Path $Dest "references") | Out-Null
    Invoke-WebRequest -Uri "$base/skills/family-mediacenter/SKILL.md" -OutFile (Join-Path $Dest "SKILL.md") -UseBasicParsing
    Invoke-WebRequest -Uri "$base/skills/family-mediacenter/references/api.md" -OutFile (Join-Path $Dest "references\api.md") -UseBasicParsing
    Write-Log "Downloaded and installed from $base"
}

if ($BaseUrl) {
    Install-FromUrl -Base $BaseUrl
} else {
    Install-FromLocal
}

Write-Log "Skill installed to: $Dest"
Write-Log "Restart WorkBuddy completely, then use keywords like download in chat."
