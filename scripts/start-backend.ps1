# Pokreni HT Eronet backend (zadano 8004 – port 8003 može imati zastarjele LISTEN zapise na Windowsu)
param([int]$Port = 8004)

function Stop-PortListeners([int]$p) {
    $pids = netstat -ano |
        Select-String ":$p\s" |
        ForEach-Object {
            if ($_ -match '\s+LISTENING\s+(\d+)\s*$') { [int]$Matches[1] }
        } |
        Sort-Object -Unique

    foreach ($procId in $pids) {
        $alive = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($alive) {
            Write-Host "Zaustavljam PID $procId ($($alive.ProcessName))"
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "PID $procId na portu $p nije aktivan (zastarjeli netstat zapis – ignoriraj)"
        }
    }
    Start-Sleep -Seconds 2
}

# Zaustavi sve poznate uvicorn instance (izbjegava stari kod na duplim procesima)
Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'uvicorn' } |
    ForEach-Object {
        Write-Host "Zaustavljam uvicorn PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Stop-PortListeners -p $Port
Stop-PortListeners -p 8003
Stop-PortListeners -p 8000

$BackendDir = (Resolve-Path "$PSScriptRoot\..\backend").Path
Set-Location $BackendDir

$fontFile = Join-Path $BackendDir "assets\fonts\DejaVuSans.ttf"
if (-not (Test-Path $fontFile)) {
    Write-Host "GRESKA: Nedostaje $fontFile" -ForegroundColor Red
    Write-Host "Vidi backend/assets/fonts/README.md za preuzimanje DejaVu fontova."
    exit 1
}
$fontSize = (Get-Item $fontFile).Length
if ($fontSize -lt 100000) {
    Write-Host "GRESKA: DejaVuSans.ttf je oštećen ($fontSize B). Ponovno preuzmite font." -ForegroundColor Red
    exit 1
}

Write-Host "Backend dir: $BackendDir"
Write-Host "PDF font: DejaVu OK ($fontSize B)"
Write-Host "Pokrecem backend na http://127.0.0.1:$Port"
Write-Host "Provjera: http://127.0.0.1:$Port/health (pdf_font treba biti dejavu)"
Write-Host "API docs: http://127.0.0.1:$Port/docs"
Write-Host "Frontend proxy (vite): mora biti isti port $Port u frontend/vite.config.ts"
& .\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port $Port --reload
