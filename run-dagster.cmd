@echo off
rem Dagster UI + daemon. Needs MinIO running (start-minio.cmd) first.
set DAGSTER_HOME=%~dp0.dagster
if not exist "%DAGSTER_HOME%" mkdir "%DAGSTER_HOME%"
set PYTHONPATH=%~dp0
"%~dp0.venv\Scripts\dagster.exe" dev -f "%~dp0pipeline\definitions.py" -h 127.0.0.1 -p 3000
