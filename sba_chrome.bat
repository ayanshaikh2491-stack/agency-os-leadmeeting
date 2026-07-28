@echo off
REM Start Chrome daemon for SBA agent (port 9222)
REM Usage: sba_chrome start | stop | status

set CHROME="C:\Users\TAUSHEF\AppData\Local\ms-playwright\chromium-1228\chrome-win64\chrome.exe"
set PORT=9222
set USER_DATA="%USERPROFILE%\.chrome-sba-profile"
set PID_FILE="%USERPROFILE%\.sba_chrome_pid"

if /I "%1"=="stop" goto stop
if /I "%1"=="status" goto status
if /I "%1"=="restart" goto restart

:start
REM Check if already running
netstat -ano | findstr ":%PORT% " >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [SBA] Chrome already running on port %PORT%
    goto :eof
)

REM Create user data dir
if not exist %USER_DATA% mkdir %USER_DATA%

echo [SBA] Starting Chromium on port %PORT%...
start /B "" %CHROME% ^
    --remote-debugging-port=%PORT% ^
    --headless ^
    --disable-gpu ^
    --no-sandbox ^
    --disable-dev-shm-usage ^
    --disable-extensions ^
    --disable-sync ^
    --user-data-dir=%USER_DATA% ^
    --window-size=1920,1080 ^
    --no-first-run ^
    --disable-background-networking ^
    --disable-default-apps ^
    --mute-audio ^
    about:blank

REM Wait for it
for /L %%i in (1,1,15) do (
    timeout /t 1 /nobreak >nul
    netstat -ano | findstr ":%PORT% " >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo [SBA] Chrome ready ^(%%i s^)
        goto :eof
    )
)
echo [SBA] Chrome started but not yet on port %PORT%. Check manually.
goto :eof

:stop
echo [SBA] Stopping Chrome daemon...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% "') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo [SBA] Chrome stopped.
goto :eof

:status
netstat -ano | findstr ":%PORT% " >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [SBA] Chrome daemon is RUNNING on port %PORT%
) else (
    echo [SBA] Chrome daemon is STOPPED
)
goto :eof

:restart
call :stop
timeout /t 2 /nobreak >nul
call :start
