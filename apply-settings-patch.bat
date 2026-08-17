@echo off
setlocal
set "ROOT=%~1"
if "%ROOT%"=="" set "ROOT=%CD%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply-settings-patch.ps1" -ProjectRoot "%ROOT%"
exit /b %ERRORLEVEL%
