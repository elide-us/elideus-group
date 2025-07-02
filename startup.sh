#!/bin/bash
#set -e

# Start SQL Server in the background
#/opt/mssql/bin/sqlservr &

# Give SQL Server some time to start up
#echo "Sleeping 30 seconds to allow SQL Server to initialize..."
#sleep 30

# Start the FastAPI app
#exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000
