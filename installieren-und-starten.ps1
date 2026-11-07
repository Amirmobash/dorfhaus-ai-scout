# Kostenloser Windows-Starter: installiert Python nur nach ausdrücklicher Bestätigung.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "DorfHaus AI Scout - kostenlose lokale Installation"
$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "Python fehlt. Installation über Windows-Paketmanager winget."
    $antwort = Read-Host "Python 3.12 kostenlos installieren? (J/N)"
    if ($antwort -notin @("J", "j")) { exit 1 }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "winget fehlt. Python bitte manuell über python.org installieren."
        exit 1
    }
    winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements
    Write-Host "Bitte dieses Skript nach der Python-Installation erneut starten."
    exit 0
}
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    if ($python.Name -eq "py.exe") { & py -3 -m venv .venv }
    else { & python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw "Virtuelle Umgebung konnte nicht erstellt werden." }
}
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Installation fehlgeschlagen." }
& ".venv\Scripts\python.exe" -m streamlit run app.py
