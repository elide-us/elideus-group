@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

:: Go to script root
CD /D %~dp0

IF "%1"=="" GOTO HELP

SET CMD=%1

IF /I "%CMD%"=="generate" GOTO DO_GENERATE
IF /I "%CMD%"=="start" GOTO DO_START
IF /I "%CMD%"=="fast" GOTO DO_FAST
IF /I "%CMD%"=="test" GOTO DO_TEST

:HELP
ECHO Usage: dev [generate^|start^|fast^|test]
EXIT /b 1

:INSTALL_DEPS
ECHO Installing Python dependencies...
CALL pip install -q -r requirements.txt
IF ERRORLEVEL 1 EXIT /b 1
CALL pip install -q -r requirements-dev.txt
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:GENERATE_LIBS
python scripts\generate_rpc_library.py
IF ERRORLEVEL 1 EXIT /b 1
python scripts\generate_rpc_client.py
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:FRONTEND_TASKS
CD frontend
ECHO Running npm ci on Frontend...
CALL npm ci
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
ECHO Running lint on Frontend...
CALL npm run lint
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
ECHO Running type-check on Frontend...
CALL npm run type-check
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
ECHO Running vitest on Frontend...
CALL npm test -- --run
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
ECHO Running tsc + vite on Frontend...
CALL npm run build
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
CD ..
EXIT /b 0

:RUN_PYTEST
ECHO Running pytest on Solution...
CALL python -m pytest
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:DO_GENERATE
CALL :GENERATE_LIBS
EXIT /b %ERRORLEVEL%

:DO_START
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
CALL :FRONTEND_TASKS || EXIT /b 1
CALL :RUN_PYTEST || EXIT /b 1
ECHO Starting Uvicorn...
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%

:DO_FAST
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
ECHO Starting Uvicorn...
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%

:DO_TEST
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
CALL :FRONTEND_TASKS || EXIT /b 1
CALL :RUN_PYTEST
EXIT /b %ERRORLEVEL%

