# MyDownloader 启动脚本（控制台 + 日志文件）
param(
    [switch]$NoKillExisting
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("mydownloader-{0:yyyyMMdd}.log" -f (Get-Date))

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Get-ServerPort {
    try {
        $port = python -c "from app.config import load_settings; print(load_settings().server.port)"
        return [int]($port.Trim())
    } catch {
        return 8766
    }
}

function Stop-ListenerOnPort {
    param([int]$Port)
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Log "停止占用端口 $Port 的进程: $($proc.ProcessName) (PID $($proc.Id))" "Yellow"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    }
}

Write-Log "========================================" "Cyan"
Write-Log "MyDownloader 启动" "Cyan"
Write-Log "项目目录: $ProjectRoot" "Gray"
Write-Log "日志文件: $LogFile" "Gray"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Log "未找到 python，请先安装 Python 3.10+" "Red"
    exit 1
}
Write-Log "Python: $($python.Source)" "Gray"

$port = Get-ServerPort
$hostAddr = "127.0.0.1"
try {
    $hostAddr = (python -c "from app.config import load_settings; print(load_settings().server.host)").Trim()
} catch { }

if (-not $NoKillExisting) {
    Stop-ListenerOnPort -Port $port
}

Write-Log "服务地址: http://${hostAddr}:$port" "Green"
Write-Log "按 Ctrl+C 停止服务" "Gray"
Write-Log "========================================" "Cyan"

$env:PYTHONUNBUFFERED = "1"

$prevErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"

python -u -m app.main 2>&1 | ForEach-Object {
    $line = if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_.ToString() }
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

$ErrorActionPreference = $prevErrorAction
