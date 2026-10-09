$ErrorActionPreference = "Stop"

$localPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$buboPython = "C:\Users\Lenovo\Downloads\facesearch\.venv\Scripts\python.exe"

if (Test-Path $localPython) {
    $python = $localPython
} elseif (Test-Path $buboPython) {
    $python = $buboPython
} else {
    $python = "python"
}

& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
