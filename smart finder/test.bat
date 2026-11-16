@echo off
setlocal enabledelayedexpansion
title "Smart Lost and Found - Test Suite"

set "PYTHON_EXE="
if exist "C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=C:\Users\kdani\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    goto :run_tests
)
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :run_tests
)
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py"
    goto :run_tests
)

:run_tests
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo Running complete unit and integration test suite...
"%PYTHON_EXE%" -W error -m unittest discover -s tests -p "test_*.py" -v
pause
