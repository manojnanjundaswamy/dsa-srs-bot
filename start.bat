@echo off
echo Starting Task Engine backend on port 8080...
start "Task Engine Backend" cmd /k "cd /d "%~dp0" && uvicorn task_engine.api:app --host 127.0.0.1 --port 8080"

echo Starting React frontend on port 5173...
start "React Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Services starting...
echo   Backend API : http://127.0.0.1:8080
echo   API Docs    : http://127.0.0.1:8080/docs
echo   Frontend    : http://localhost:5173
echo.
echo Close the two terminal windows to stop both services.
