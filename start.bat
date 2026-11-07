@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installieren-und-starten.ps1"
if errorlevel 1 (
  echo Installation oder Start fehlgeschlagen.
  pause
)
