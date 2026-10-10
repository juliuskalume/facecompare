$ErrorActionPreference = "Stop"

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "janus-$stamp.log"
$latestFile = Join-Path $logDir "janus-latest.txt"
Set-Content -Path $latestFile -Value "Latest Janus log: $logFile"

$localPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$buboPython = "C:\Users\Lenovo\Downloads\facesearch\.venv\Scripts\python.exe"

if (Test-Path $localPython) {
    $python = $localPython
} elseif (Test-Path $buboPython) {
    $python = $buboPython
} else {
    $python = "python"
}

$env:PYTHONUNBUFFERED = "1"

Start-Transcript -Path $logFile -Append | Out-Null
try {
    Write-Host "Starting Janus at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "Python: $python"
    Write-Host "URL: http://127.0.0.1:8010"
    Write-Host "Log: $logFile"

    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
    $exitCode = $LASTEXITCODE
} finally {
    Stop-Transcript | Out-Null
}

if ($exitCode) {
    exit $exitCode
}
