@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
call "%ROOT%scripts\preparar_windows.bat"
if errorlevel 1 (echo Error de preparacio.& pause& exit /b 1)
if not exist "%ROOT%frontend\.env" copy /Y "%ROOT%frontend\.env.example" "%ROOT%frontend\.env" >nul
pushd "%ROOT%frontend"
if not exist "node_modules\expo" (
 echo Instal-lant dependencies Expo per primera vegada...
 call npm ci
 if errorlevel 1 (popd& echo Error a npm ci.& pause& exit /b 1)
)
if not exist "node_modules\react-native-web" (
  echo Instal-lant suport Expo Web la primera vegada...
  call npx expo install react-dom react-native-web @expo/metro-runtime
  if errorlevel 1 (popd& echo Error instal-lant Expo Web.& pause& exit /b 1)
)
popd
powershell -NoProfile -Command "try {$r=Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2; if($r.data.status -ne 'ok') {exit 1}} catch {exit 1}"
if errorlevel 1 start "SAFi Backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
set "EXPO_PUBLIC_API_URL=http://127.0.0.1:8000"
set "EXPO_PUBLIC_USE_MOCKS=false"
echo Obrint aplicacio SAFi en navegador (Expo Web)...
start "SAFi App" /D "%ROOT%frontend" cmd /k "npx expo start --web --clear"
echo Backend: http://127.0.0.1:8000/health
echo L'app s'obrira al navegador quan Expo estigui preparat.
echo IMPORTANT: es necessita Internet durant la primera instal-lacio.
pause
