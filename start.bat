@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt -q
py main.py
if errorlevel 1 (
  echo.
  echo Kunde inte starta. Installera Python fran https://www.python.org/downloads/
  echo och kryssa i "Add python.exe to PATH" samt "tcl/tk and IDLE".
  pause
)
