@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
call "%ROOT%scripts\preparar_windows.bat"
if errorlevel 1 (echo ERROR preparant backend.& pause& exit /b 1)
pushd "%ROOT%frontend"
if not exist "node_modules\expo" (
 call npm ci
 if errorlevel 1 (popd& echo ERROR instal-lant Expo.& pause& exit /b 1)
)
popd
powershell -NoProfile -Command "try {$r=Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2; if($r.data.status -ne 'ok') {exit 1}} catch {exit 1}"
if errorlevel 1 start "SAFi Backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\wait_for_backend.ps1" -TimeoutSeconds 35
if errorlevel 1 (echo ERROR backend.& pause& exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\verificar_api.ps1"
if errorlevel 1 (echo ERROR API.& pause& exit /b 1)
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$c=Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notmatch '^(127\\.|169\\.)' -and $_.InterfaceAlias -notmatch 'Virtual|vEthernet|WSL|Docker' } | Sort-Object InterfaceMetric; $c | Select-Object -First 1 -ExpandProperty IPAddress"`) do set "SAFI_PC_IP=%%I"
if not defined SAFI_PC_IP (
 echo No es pot detectar IP de Windows.
 set /p "SAFI_PC_IP=Escriu la IP IPv4 local del PC (ipconfig): "
)
if not defined SAFI_PC_IP (echo ERROR: no s'ha indicat IP.& pause& exit /b 1)
set "EXPO_PUBLIC_API_URL=http://%SAFI_PC_IP%:8000"
set "EXPO_PUBLIC_USE_MOCKS=false"
echo.
echo Expo Go: posa el telefon a la mateixa Wi-Fi que Windows.
echo API LAN: %EXPO_PUBLIC_API_URL%
echo Prova aquesta URL al navegador del telefon: %EXPO_PUBLIC_API_URL%/health
echo Pot caldre permetre Python al Firewall de Windows (port 8000).
echo.
start "SAFi App Mobil" /D "%ROOT%frontend" cmd /k "npx expo start --lan --clear"
pause
