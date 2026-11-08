param([switch]$Apply)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
git fetch --prune origin
if ($LASTEXITCODE -ne 0) { throw 'No s''ha pogut sincronitzar origin.' }
$merged = @(git branch -r --merged origin/main | ForEach-Object { $_.Trim() } | Where-Object {
    $_ -like 'origin/*' -and $_ -notlike '*->*' -and $_ -ne 'origin/main'
})
Write-Host 'Branques remotes TOTALMENT fusionades a main:' -ForegroundColor Green
$merged | ForEach-Object { Write-Host (' - ' + $_) }
Write-Host 'Les branques divergents NO es tocaran.'
if (-not $Apply) {
    Write-Host 'Mode segur: cap branca eliminada. Per aplicar: powershell -ExecutionPolicy Bypass -File scripts/netejar_branques.ps1 -Apply'
    exit
}
foreach ($ref in $merged) {
  $branch = $ref.Substring(7)
  $confirmation = Read-Host "Eliminar del remot $branch ? (escriu SI)"
  if ($confirmation -eq 'SI') {
    git push origin --delete $branch
    if ($LASTEXITCODE -ne 0) { Write-Warning ('No s''ha pogut eliminar '+$branch) }
  }
}
