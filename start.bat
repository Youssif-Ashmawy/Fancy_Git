@echo off
setlocal enabledelayedexpansion
title FancyGit Windows Installer
color 0A

REM ======================================================
REM  MAIN
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

if "!PYTHON_EXE!"=="" (
    where python >nul 2>&1
    if !errorlevel! == 0 (
        for /f "delims=" %%P in ('where python') do (
            if "!PYTHON_EXE!"=="" set "PYTHON_EXE=%%P"
        )
    )
)

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
if !errorlevel! neq 0 call :fail [ERROR] Git not installed. Get it at https://git-scm.com

for /f "tokens=*" %%V in ('git --version') do call :log [OK] %%V
echo.


REM -------------------------------------------------------
REM  3. COPY fancygit.py FROM INSTALLER DIRECTORY
REM -------------------------------------------------------
if exist "%INSTALL_DIR%\fancygit.py" (
    call :log [OK] fancygit.py already present - skipping.
) else (
    SET "SCRIPT_DIR=%~dp0"
    if exist "!SCRIPT_DIR!fancygit.py" (
        copy /y "!SCRIPT_DIR!fancygit.py" "%INSTALL_DIR%\fancygit.py" >nul
        call :log [OK] Copied fancygit.py from installer directory.
    ) else (
        call :fail [ERROR] fancygit.py not found next to installer. Put both files in the same folder.
    )
)
echo.


REM -------------------------------------------------------
REM  4a. CREATE WINDOWS LAUNCHER  (fancygit.bat)
REM -------------------------------------------------------
(
    echo @echo off
    echo "!PYTHON_EXE!" "%INSTALL_DIR%\fancygit.py" %%*
) > "%INSTALL_DIR%\fancygit.bat"

if !errorlevel! neq 0 call :fail [ERROR] Could not write fancygit.bat
call :log [OK] CMD launcher:      %INSTALL_DIR%\fancygit.bat
echo.


REM -------------------------------------------------------
REM  4b. CREATE GIT BASH LAUNCHER  (fancygit — no extension)
REM  Convert Windows paths  C:\Foo\Bar  ->  /c/Foo/Bar
REM -------------------------------------------------------
for /f "delims=" %%U in ('powershell -NoProfile -Command ^
    "$p = '%INSTALL_DIR%'; $d = $p[0].ToString().ToLower(); '/' + $d + '/' + $p.Substring(3).Replace('\','/')"') do (
    set "INSTALL_UNIX=%%U"
)

for /f "delims=" %%U in ('powershell -NoProfile -Command ^
    "$p = '!PYTHON_EXE!'; $d = $p[0].ToString().ToLower(); '/' + $d + '/' + $p.Substring(3).Replace('\','/')"') do (
    set "PYTHON_UNIX=%%U"
)

(
    echo #!/bin/bash
    echo "!PYTHON_UNIX!" "!INSTALL_UNIX!/fancygit.py" "$@"
) > "%INSTALL_DIR%\fancygit"

if !errorlevel! neq 0 call :fail [ERROR] Could not write git bash launcher
call :log [OK] Git Bash launcher: %INSTALL_DIR%\fancygit
echo.


REM -------------------------------------------------------
REM  4c. ADD INSTALL DIR TO GIT BASH PATH via .bashrc
REM  Removes any old/broken FancyGit line first, then appends
REM  a clean one — so re-running the installer is always safe.
REM -------------------------------------------------------
SET "BASHRC=%USERPROFILE%\.bashrc"

REM  Strip any existing FancyGit entry (handles broken old lines)
if exist "!BASHRC!" (
    powershell -NoProfile -Command ^
        "(Get-Content '!BASHRC!') | Where-Object { $_ -notmatch 'FancyGit' } | Set-Content '!BASHRC!'"
)

REM  Append clean export line
echo export PATH="$PATH:!INSTALL_UNIX!" >> "!BASHRC!"
call :log [OK] Added !INSTALL_UNIX! to .bashrc for Git Bash.
echo.


REM -------------------------------------------------------
REM  5. ADD TO WINDOWS USER PATH  (safe registry method)
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
    call :log [OK] Added %INSTALL_DIR% to Windows user PATH.
) else (
    call :log [OK] Already in Windows PATH - skipping.
)
call :log [INFO] Restart CMD / Git Bash after install to use fancygit.
echo.


REM -------------------------------------------------------
REM  6. DONE
REM -------------------------------------------------------
call :log =========================================
call :log  Installation complete!
call :log =========================================
call :log  CMD / PowerShell:   fancygit add .
call :log  Git Bash:           fancygit add .
call :log  Both support:       fancygit commit -m "msg"
call :log                      fancygit push origin main
call :log                      fancygit pull origin main
call :log =========================================
call :log  Log saved to: %LOG_FILE%
echo.
echo  Press any key to close...
pause >nul
exit /b 0


REM ======================================================
REM  SUBROUTINES
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