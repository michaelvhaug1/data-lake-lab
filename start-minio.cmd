@echo off
rem Local S3-compatible object store. API on :9000, web console on :9001.
rem Credentials are for the local lab only; they are also in .env.
set MINIO_ROOT_USER=lakeadmin
set MINIO_ROOT_PASSWORD=lakeadmin123
"%~dp0tools\minio\minio.exe" server "%~dp0minio-data" --address :9000 --console-address :9001
