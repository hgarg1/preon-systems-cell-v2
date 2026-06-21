@echo off
setlocal
cd /d "%~dp0"
python -m pip show preon-systems-cell >nul 2>nul
if errorlevel 1 (
  echo Installing local package dependencies...
  python -m pip install -e ".[dev,postgres]"
)

python main.py web %*
if errorlevel 1 (
  echo.
  echo Preon Systems organism runtime exited with an error.
  echo If port 8000 is already in use, run: run-web.bat --port 8001
  echo.
  pause
)
