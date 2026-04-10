@ECHO OFF
SETLOCAL ENABLEEXTENSIONS
:: Go to script root
CD /D %~dp0
IF "%1"=="" GOTO HELP
SET CMD=%1
IF /I "%CMD%"=="start" GOTO DO_START
IF /I "%CMD%"=="fast" GOTO DO_FAST
IF /I "%CMD%"=="test" GOTO DO_TEST
IF /I "%CMD%"=="client" GOTO DO_CLIENT
:HELP
ECHO Usage: dev [start^|fast^|test^|client]
ECHO.
ECHO   start   - Install deps, run tests, start uvicorn
ECHO   fast    - Install deps, start uvicorn (skip tests)
ECHO   test    - Pull latest, install deps, run all tests
ECHO   client  - npm install + vite dev server for client/
EXIT /b 1

:INSTALL_DEPS
ECHO Installing Python dependencies...
CALL pip install -r requirements.txt
IF ERRORLEVEL 1 EXIT /b 1
CALL pip install -r requirements-dev.txt
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:CLIENT_INSTALL
CD client
ECHO Installing client dependencies...
CALL npm ci
IF ERRORLEVEL 1 (CD .. & EXIT /b 1)
CD ..
EXIT /b 0

:RUN_PYTEST
ECHO Running pytest on Solution...
CALL python -m pytest
IF ERRORLEVEL 1 EXIT /b 1
EXIT /b 0

:DO_START
CALL :INSTALL_DEPS || EXIT /b 1
CALL :CLIENT_INSTALL || EXIT /b 1
CALL :RUN_PYTEST || EXIT /b 1
ECHO.
ECHO Starting Uvicorn on http://localhost:8000 ...
ECHO Run 'dev client' in a second terminal for the client dev server.
ECHO.
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%

:DO_FAST
CALL :INSTALL_DEPS || EXIT /b 1
ECHO.
ECHO Starting Uvicorn on http://localhost:8000 ...
ECHO Run 'dev client' in a second terminal for the client dev server.
ECHO.
CALL python -m uvicorn main:app --reload --host localhost
EXIT /b %ERRORLEVEL%

:DO_TEST
ECHO Getting latest from GitHub...
CALL git pull origin test
IF ERRORLEVEL 1 EXIT /b 1
CALL :INSTALL_DEPS || EXIT /b 1
CALL :CLIENT_INSTALL || EXIT /b 1
CALL :RUN_PYTEST || EXIT /b 1
ECHO All tests passed.
EXIT /b 0

:DO_CLIENT
CALL :CLIENT_INSTALL || EXIT /b 1
ECHO.
ECHO Starting Vite dev server for client...
ECHO Backend must be running on http://localhost:8000 (use 'dev fast' in another terminal)
ECHO.
CD client
CALL npm run dev
CD ..
EXIT /b %ERRORLEVEL%