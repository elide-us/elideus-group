@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

:: Go to script root
CD /D %~dp0

CALL pip install -r requirements-dev.txt
IF ERRORLEVEL 1 (
    ECHO "Failed to install requirements-dev.txt. Exiting."
    EXIT /b 1
)

:: Generate TypeScript libraries
CALL devgenerate.cmd
IF ERRORLEVEL 1 (
    ECHO "devgenerate failed. Exiting."
    EXIT /b 1
)

:: Run frontend tasks
CD frontend
ECHO Running npm ci on Frontend...
CALL npm ci
IF ERRORLEVEL 1 (
    ECHO "npm ci failed. Exiting."
    EXIT /b 1
)

ECHO Running tsc + vite on Frontend...
CALL npm run build
IF ERRORLEVEL 1 (
    ECHO "npm run build failed. Exiting."
    EXIT /b 1
)

:: Back to root
CD ..

ECHO Starting Uvicorn...
CALL python -m uvicorn main:app --reload --host localhost
