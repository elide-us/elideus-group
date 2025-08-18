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
IF /I "%CMD%"=="restart" GOTO DO_RESTART
IF /I "%CMD%"=="refast" GOTO DO_REFAST


:HELP
ECHO Usage: dev [generate^|start^|fast^|test]
EXIT /b 1

:GET_LATEST
ECHO Getting latest from GitHub...
CALL git pull origin elideus
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:INSTALL_DEPS
ECHO Installing Python dependencies...
CALL pip install -r requirements.txt
IF ERRORLEVEL 1 EXIT /b 1
CALL pip install -r requirements-dev.txt
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:GENERATE_LIBS
python scripts\generate_rpc_library.py
IF ERRORLEVEL 1 EXIT /b 1
python scripts\generate_rpc_client.py
IF ERRORLEVEL 1 EXIT /b 1
python scripts\generate_rpc_metadata.py
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
CALL :GET_LATEST
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
CALL :GET_LATEST
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
CALL :FRONTEND_TASKS || EXIT /b 1
CALL :RUN_PYTEST
EXIT /b %ERRORLEVEL%

:DO_RESTART
CALL :GET_LATEST || EXIT /b 1
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
CALL :FRONTEND_TASKS || EXIT /b 1
CALL :RUN_PYTEST || EXIT /b 1
ECHO Starting Uvicorn...
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%

:DO_REFAST
CALL :GET_LATEST || EXIT /b 1
CALL :INSTALL_DEPS || EXIT /b 1
CALL :GENERATE_LIBS || EXIT /b 1
CD frontend
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
CALL :RUN_PYTEST || EXIT /b 1
ECHO Starting Uvicorn...
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%
