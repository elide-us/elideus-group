@ECHO OFF
python scripts\generate_rpc_library.py
IF ERRORLEVEL 1 (
    ECHO "TypeScript generation failed."
    EXIT /b 1
)
python scripts\generate_user_context.py
IF ERRORLEVEL 1 (
    ECHO "UserContext generation failed."
    EXIT /b 1
)
python scripts\generate_rpc_client.py
IF ERRORLEVEL 1 (
    ECHO "RPC client generation failed."
    EXIT /b 1
)
