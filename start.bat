@echo off
setlocal enabledelayedexpansion
title FancyGit Windows Installer
color 0A

REM ======================================================
REM  MAIN starts here immediately — no goto needed
REM ======================================================

SET "INSTALL_DIR=%USERPROFILE%\FancyGit"
IF NOT EXIST "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
SET "LOG_FILE=%INSTALL_DIR%\install_log.txt"

(
    echo =========================================
    echo  FancyGit Windows Installer Log
    echo  %DATE%  %TIME%
    echo =========================================
    echo.
) > "%LOG_FILE%"

call :log [INFO] Starting FancyGit installation...
echo.


REM -------------------------------------------------------
REM  1. FIND PYTHON
REM -------------------------------------------------------
SET "PYTHON_EXE="

for /d %%D in (
    "%LocalAppData%\Programs\Python\Python3*"
    "%LocalAppData%\Programs\Python\Python*"
    "C:\Python3*"
    "C:\Python*"
) do (
    if exist "%%D\python.exe" (
        if "!PYTHON_EXE!"=="" set "PYTHON_EXE=%%D\python.exe"
    )
)

REM --- Also check whatever python is already on PATH ------
if "!PYTHON_EXE!"=="" (
    where python >nul 2>&1
    if !errorlevel! == 0 (
        for /f "delims=" %%P in ('where python') do (
            if "!PYTHON_EXE!"=="" set "PYTHON_EXE=%%P"
        )
    )
)

REM --- Still nothing — ask the user ----------------------
if "!PYTHON_EXE!"=="" (
    call :log [INFO] Python not found automatically.
    echo.
    set /p "PYTHON_EXE=Enter full path to python.exe: "
)

if "!PYTHON_EXE!"=="" call :fail [ERROR] No Python path given.

"!PYTHON_EXE!" --version >nul 2>&1
if !errorlevel! neq 0 call :fail [ERROR] Python not runnable at: !PYTHON_EXE!

call :log [OK] Python found: !PYTHON_EXE!
echo.


REM -------------------------------------------------------
REM  2. CHECK GIT
REM -------------------------------------------------------
git --version >nul 2>&1
if !errorlevel! neq 0 (
    call :fail [ERROR] Git not installed. Get it at https://git-scm.com
)
for /f "tokens=*" %%V in ('git --version') do call :log [OK] %%V
echo.


REM -------------------------------------------------------
REM  3. GET fancygit.py  (copy from local dir, no download)
REM -------------------------------------------------------
if exist "%INSTALL_DIR%\fancygit.py" (
    call :log [OK] fancygit.py already present - skipping.
) else (
    REM  Grab it from the same folder as this installer
    SET "SCRIPT_DIR=%~dp0"
    if exist "!SCRIPT_DIR!fancygit.py" (
        copy /y "!SCRIPT_DIR!fancygit.py" "%INSTALL_DIR%\fancygit.py" >nul
        call :log [OK] Copied fancygit.py from installer directory.
    ) else (
        call :fail [ERROR] fancygit.py not found next to installer. Put both files in the same folder.
    )
)


REM -------------------------------------------------------
REM  4. CREATE LAUNCHER
REM -------------------------------------------------------
(
    echo @echo off
    echo "!PYTHON_EXE!" "%INSTALL_DIR%\fancygit.py" %%*
) > "%INSTALL_DIR%\fancygit.bat"

call :log [OK] Launcher: %INSTALL_DIR%\fancygit.bat
echo.


REM -------------------------------------------------------
REM  5. ADD TO USER PATH  (safe registry method)
REM -------------------------------------------------------
for /f "tokens=2*" %%A in (
    'reg query "HKCU\Environment" /v PATH 2^>nul'
) do set "CURRENT_USER_PATH=%%B"

echo !CURRENT_USER_PATH! | findstr /i /c:"%INSTALL_DIR%" >nul 2>&1
if !errorlevel! neq 0 (
    if "!CURRENT_USER_PATH!"=="" (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%INSTALL_DIR%" /f >nul
    ) else (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!CURRENT_USER_PATH!;%INSTALL_DIR%" /f >nul
    )
    call :log [OK] Added to PATH. Restart terminals to apply.
) else (
    call :log [OK] Already in PATH - skipping.
)
echo.


REM -------------------------------------------------------
REM  6. DONE
REM -------------------------------------------------------
call :log =========================================
call :log  Installation complete!
call :log =========================================
call :log  fancygit add .
call :log  fancygit commit -m "Your message"
call :log  fancygit push origin main
call :log =========================================
echo.
echo  Press any key to close...
pause >nul
exit /b 0


REM ======================================================
REM  SUBROUTINES  (must be after exit /b so they aren't
REM  executed by fall-through)
REM ======================================================

:log
    echo %*
    echo %* >> "%LOG_FILE%"
    goto :eof

:fail
    echo.
    echo %* >> "%LOG_FILE%"
    echo %*
    echo.
    echo Installation failed. See log: %LOG_FILE%
    pause
    exit /b 1