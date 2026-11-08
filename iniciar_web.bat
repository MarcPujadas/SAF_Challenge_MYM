@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
call "%ROOT%scripts\preparar_windows.bat"
if errorlevel 1 (echo Error de preparacio.& pause& exit /b 1)
if not exist "%ROOT%web\package.json" (echo ERROR: falta web/package.json.& pause& exit /b 1)
pushd "%ROOT%web"
if not exist "node_modules\vite" (
 echo Instal-lant dependencies de la web per primera vegada...
 call npm ci
 if errorlevel 1 (popd& echo Error a npm ci.& pause& exit /b 1)
)
popd
powershell -NoProfile -Command "try {$r=Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2; if($r.data.status -ne 'ok') {exit 1}} catch {exit 1}"
if errorlevel 1 start "SAFi Backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
set "VITE_API_URL=http://127.0.0.1:8000"
start "SAFi Web" /D "%ROOT%web" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"
echo Web: http://127.0.0.1:5173
echo Backend: http://127.0.0.1:8000/health
start "" "http://127.0.0.1:5173"
pause
