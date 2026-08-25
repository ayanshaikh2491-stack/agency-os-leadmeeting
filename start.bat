@echo off
rem TAGS Agency OS - one-click local launcher (Munder office floor)
rem Kills stale servers, starts backend (FastAPI :9002) + frontend (Next.js :3000),
rem waits until the frontend is ACTUALLY ready (first compile can take ~60-90s
rem because of PixiJS), then opens the office floor.

setlocal
set ROOT=%~dp0
set BACKEND_PORT=9002
set FRONTEND_PORT=3000

echo ============================================
echo  TAGS Agency OS - starting local servers...
echo  Backend : http://localhost:%BACKEND_PORT%/api
echo  Frontend: http://localhost:%FRONTEND_PORT%/admin/office
echo ============================================

echo Killing any stale Next.js / node dev servers on port %FRONTEND_PORT%...
taskkill /F /IM next-server.exe >nul 2>nul
taskkill /F /IM node.exe >nul 2>nul
timeout /t 3 /nobreak >nul

rem Launch backend in its own window (best-effort; the office floor still
rem renders without it, just shows "connecting..." until the WS is reachable).
start "TAGS-Backend" /D "%ROOT%" cmd /k "python -m admin.main"

rem Launch frontend in its own window, forced to port %FRONTEND_PORT%.
start "TAGS-Frontend" /D "%ROOT%agency-frontend" cmd /k "set PORT=%FRONTEND_PORT% && npm run dev"

echo Waiting for the frontend to come up (first compile can take ~60-90s)...
:waitroot
curl.exe -s -o nul -w "%%{http_code}" http://localhost:%FRONTEND_PORT%/ 2>nul | findstr "200" >nul
if errorlevel 1 (
  timeout /t 3 /nobreak >nul
  goto waitroot
)

echo Warming up the Munder office route (triggers its ~80s PixiJS compile)...
:waitoffice
curl.exe -s -o nul -w "%%{http_code}" http://localhost:%FRONTEND_PORT%/admin/office 2>nul | findstr "200" >nul
if errorlevel 1 (
  timeout /t 3 /nobreak >nul
  goto waitoffice
)

echo Frontend is ready. Opening the office floor...
start "" "http://localhost:%FRONTEND_PORT%/admin/office"

echo Done. Close the two server windows to stop.
endlocal
