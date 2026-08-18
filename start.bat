@echo off
rem TAGS Agency OS - one-click local launcher (CEO Control Room)
rem Kills any squatting dev servers, starts backend (FastAPI :9002)
rem + frontend (Next.js :3000), then opens http://localhost:3000/ceo

setlocal
set ROOT=%~dp0
set BACKEND_PORT=9002
set FRONTEND_PORT=3000

echo ============================================
echo  TAGS Agency OS - starting local servers...
echo  Backend : http://localhost:%BACKEND_PORT%/api
echo  Frontend: http://localhost:%FRONTEND_PORT%/ceo
echo ============================================

echo Killing any stale Next.js / node dev servers on 3000...
taskkill /F /IM next-server.exe >nul 2>nul
taskkill /F /IM node.exe >nul 2>nul
timeout /t 3 /nobreak >nul

rem Launch backend in its own window
start "TAGS-Backend" /D "%ROOT%" cmd /k "python -m admin.main"

rem Launch frontend in its own window (force port 3000)
start "TAGS-Frontend" /D "%ROOT%agency-frontend" cmd /k "set PORT=3000 && npm run dev"

rem Wait for the dev server, then open the Control Room
timeout /t 12 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%/ceo"

echo Done. Close the two server windows to stop.
endlocal
