@echo off
setlocal enabledelayedexpansion
title "Smart Lost and Found - Campus AI System"

echo ======================================================================
echo SMART LOST & FOUND - AI POWERED CAMPUS SYSTEM
echo B.Sc. Computer Science (AI & ML) College Mini Project
echo ======================================================================
echo.

:: Detect Python executable
set "PYTHON_EXE="

:: 1. Check if configured codex runtime exists
if exist "C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    goto :found_python
)

:: 2. Check standard python command
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python -c "import sys" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_EXE=python"
        goto :found_python
    )
)

:: 3. Check py launcher
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -c "import sys" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_EXE=py"
        goto :found_python
    )
)

:found_python
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python was not found on your system.
    echo Please install Python 3.10+ or check your PATH.
    pause
    exit /b 1
)

echo [OK] Using Python: %PYTHON_EXE%
echo [INFO] Starting Smart Lost & Found Web Server on http://127.0.0.1:5000 ...
echo [INFO] Press Ctrl+C in this window to stop the server.
echo.

"%PYTHON_EXE%" run.py

pause
