@echo off
echo ==============================================
echo   UK Port Shipping Analytics Dashboard
echo ==============================================
echo.
echo Installing requirements (if not already installed)...
py -3 -m pip install -r requirements.txt
echo.
echo Starting Flask server...
echo Dashboard will be available at: http://127.0.0.1:5000
echo.
py -3 run.py
pause
