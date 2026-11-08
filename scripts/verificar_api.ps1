param([string]$ApiBase = 'http://127.0.0.1:8000')
$ErrorActionPreference = 'Stop'
$tests = @(
  @{ Name='Salut'; Path='/health'; DataCheck={ param($x) $x.data.status -eq 'ok' } },
  @{ Name='Cataleg de serveis'; Path='/api/v1/services'; DataCheck={ param($x) $x.data -is [array] -and $x.data.Count -ge 8 } },
  @{ Name='Disponibilitat setmanal Fitness'; Path='/api/v1/services/fitness/availability/week?from=2026-11-09&to=2026-11-09'; DataCheck={ param($x) $x.data.days.Count -gt 0 } },
  @{ Name='Reserves de demo'; Path='/api/v1/reservations?user_id=demo-user'; DataCheck={ param($x) $null -ne $x.data } }
)
$failed = 0
foreach ($test in $tests) {
  $url = $ApiBase + $test.Path
  try {
    $response = Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 12
    if ($response.success -ne $true -or -not (& $test.DataCheck $response)) {
      Write-Host ('ERROR: ' + $test.Name + ' - resposta inesperada a ' + $url) -ForegroundColor Red
      $failed++
    } else {
      Write-Host ('OK: ' + $test.Name) -ForegroundColor Green
    }
  } catch {
    Write-Host ('ERROR: ' + $test.Name + ' - ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('URL: ' + $url)
    $failed++
  }
}
if ($failed -gt 0) {
  Write-Host ('ERRORS de l''API: ' + $failed + '. Revisa els logs de FastAPI i la configuracio.') -ForegroundColor Red
  exit 1
}
Write-Host 'Tots els endpoints essencials del backend responen.' -ForegroundColor Green
exit 0
