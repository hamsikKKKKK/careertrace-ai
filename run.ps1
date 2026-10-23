param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Run setup.ps1 first: Python environment is missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/dist/index.html'))) { throw 'Run setup.ps1 first: frontend build is missing.' }
Write-Host "CareerTrace: http://127.0.0.1:$Port (Ctrl+C to stop)"
& $pythonExe -m uvicorn app.main:create_app --factory --app-dir (Join-Path $projectRoot 'backend') --host 127.0.0.1 --port $Port
if ($LASTEXITCODE -ne 0) { throw 'CareerTrace server stopped with an error.' }
