# Demo seed za fazu 5 (kupci, servisni nalozi, port-in, karantena)
$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "..\backend"
Push-Location $backend
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}
python -m scripts.demo_seed_faza5
Pop-Location
