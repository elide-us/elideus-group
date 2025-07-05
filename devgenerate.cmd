@ECHO OFF
python scripts\generate_ts_library.py
IF ERRORLEVEL 1 (
    ECHO "TypeScript generation failed."
    EXIT /b 1
)
