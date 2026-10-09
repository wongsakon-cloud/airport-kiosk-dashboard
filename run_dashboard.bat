@echo off
echo Installing required packages...
pip install -r requirements.txt
echo.
echo Starting the Kiosk Dashboard...
streamlit run dashboard.py
pause
