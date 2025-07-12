@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

:: Go to script root
CD /D %~dp0

ECHO Installing Python dependencies...
CALL pip install -r requirements.txt
IF ERRORLEVEL 1 (
    ECHO "Failed to install requirements.txt. Exiting."
    EXIT /b 1
)
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

ECHO Running lint on Frontend...
CALL npm run lint
IF ERRORLEVEL 1 (
    ECHO "npm run lint failed. Exiting."
    EXIT /b 1
)

ECHO Running type-check on Frontend...
CALL npm run type-check
IF ERRORLEVEL 1 (
    ECHO "npm run type-check failed. Exiting."
    EXIT /b 1
)

ECHO Running vitest on Frontend...
CALL npm test -- --run
IF ERRORLEVEL 1 (
    ECHO "npm test failed. Exiting."
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

ECHO Running pytest on Solution...
CALL python -m pytest
IF ERRORLEVEL 1 (
    ECHO "pytest failed. Exiting."
    EXIT /b 1
)
