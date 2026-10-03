@echo off
rem Opens a prompt with the venv, MinIO tools and lab env vars ready.
rem   python ingest.py 2024-02        land another month
rem   cd lakehouse ^&^& dbt build       run the models + tests
rem   duckdb warehouse.duckdb         poke at the warehouse
rem   mc ls lake/lake --recursive     list the bucket
for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do if not "%%a"=="" if not "%%a:~0,1%"=="#" set "%%a=%%b"
set PATH=%~dp0.venv\Scripts;%~dp0tools\minio;%PATH%
set PYTHONPATH=%~dp0
set DBT_PROFILES_DIR=%~dp0lakehouse
cd /d "%~dp0"
cmd /k
