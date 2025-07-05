@ECHO OFF
CD frontend
CALL npm ci
IF ERRORLEVEL 1 (
    ECHO "npm ci failed. Exiting."
)
CALL npm run lint
IF ERRORLEVEL 1 (
    ECHO "npm run lint failed. Exiting."
    EXIT /b 1
)

CALL npm run type-check
IF ERRORLEVEL 1 (
    ECHO "npm run type-check failed. Exiting."
    EXIT /b 1
)

CALL npm test -- --run
IF ERRORLEVEL 1 (
    ECHO "npm test failed. Exiting."
    EXIT /b 1
)

CALL npm run build
IF ERRORLEVEL 1 (
    ECHO "npm run build failed. Exiting."
    EXIT /b 1
)
cd ..
CALL pytest
IF ERRORLEVEL 1 (
    ECHO "pytest failed. Exiting."
    EXIT /b 1
)
python -m uvicorn main:app --reload
