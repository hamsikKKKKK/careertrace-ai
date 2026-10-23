$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 or newer, then retry.' }
    }
    & ./.venv/Scripts/python.exe -m pip install -r backend/requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    Push-Location frontend
    try {
        $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
        $bundledPnpm = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs'
        if ($npmCommand) {
            & $npmCommand.Source install
            if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
            & $npmCommand.Source run build
        } elseif (Test-Path -LiteralPath $bundledPnpm) {
            node $bundledPnpm install --frozen-lockfile
            if ($LASTEXITCODE -ne 0) { throw 'pnpm install failed.' }
            node $bundledPnpm run build
        } else { throw 'Install Node.js LTS with npm, then retry.' }
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
} finally { Pop-Location }
Write-Host 'Ready. Run ./run.ps1 and open http://127.0.0.1:8000'
