param([int]$TimeoutSeconds = 35)
$ErrorActionPreference = 'Stop'
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
  try {
    $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
    if ($response.success -eq $true -and $response.data.status -eq 'ok') {
      Write-Host 'Backend SAFi disponible a http://127.0.0.1:8000' -ForegroundColor Green
      exit 0
    }
  } catch {
    # Uvicorn may still be starting; retry until the deadline.
  }
  Start-Sleep -Milliseconds 750
} while ((Get-Date) -lt $deadline)
Write-Host 'ERROR: El backend SAFi no respon al port 8000.' -ForegroundColor Red
Write-Host 'Revisa la finestra SAFi Backend per veure l''error concret.'
exit 1
