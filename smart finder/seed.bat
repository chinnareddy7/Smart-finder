@echo off
setlocal enabledelayedexpansion
title "Smart Lost and Found - Database Seeder"

set "PYTHON_EXE="
if exist "C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    goto :run_seed
)
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :run_seed
)
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py"
    goto :run_seed
)

:run_seed
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo Resetting and populating database with realistic campus test data...
"%PYTHON_EXE%" seed_data.py
pause
