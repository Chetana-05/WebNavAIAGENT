@echo off
echo ==============================================
echo Starting Web Navigator AI Agent Dashboard...
echo Open your browser at: http://127.0.0.1:8000
echo ==============================================
call .\.venv\Scripts\activate.bat
python -m web_agent.web
pause
