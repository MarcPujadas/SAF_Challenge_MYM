@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\"
if not exist "%ROOT%backend\requirements.txt" (echo ERROR: carpeta backend no trobada.& exit /b 1)
where node >nul 2>&1
if errorlevel 1 (echo ERROR: cal instal-lar Node.js 22 o superior: https://nodejs.org/& exit /b 1)
where npm >nul 2>&1
if errorlevel 1 (echo ERROR: npm no disponible.& exit /b 1)
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
 echo Creant entorn Python...
 where py >nul 2>&1
 if not errorlevel 1 (
   py -3 -m venv "%ROOT%backend\.venv"
 ) else (
   where python >nul 2>&1
   if errorlevel 1 (echo ERROR: cal instal-lar Python 3.12+: https://python.org/& exit /b 1)
   python -m venv "%ROOT%backend\.venv"
 )
 if errorlevel 1 exit /b 1
)
set "VENV_PY=%ROOT%backend\.venv\Scripts\python.exe"
echo Instal-lant o verificant dependències Python...
"%VENV_PY%" -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (echo ERROR instal-lant dependencies Python.& exit /b 1)
if not exist "%ROOT%backend\.env" (
  echo UTH_KEY=>"%ROOT%backend\.env"
  echo Creat backend\.env sense cap clau privada.
)
pushd "%ROOT%backend"
"%VENV_PY%" -m scripts.seed_demo
if errorlevel 1 (popd& echo ERROR inicialitzant dades de demo.& exit /b 1)
popd
exit /b 0
