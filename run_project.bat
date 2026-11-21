@echo off
title CreditLens - Setup and Run
cd /d "%~dp0"
echo ==========================================
echo         CREDITLENS PROJECT
echo ==========================================
if not exist .venv (
  echo Creating Python environment...
  py -m venv .venv
  if errorlevel 1 python -m venv .venv
)
call .venv\Scripts\activate
echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Running data pipeline...
python src\pipeline.py
if errorlevel 1 (
  echo.
  echo Pipeline failed. Read the error above.
  pause
  exit /b 1
)
echo.
echo Launching CreditLens dashboard...
python -m streamlit run app.py --browser.gatherUsageStats false
pause
