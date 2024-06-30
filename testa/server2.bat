@echo off
REM Open command line
start cmd /k "cd /d C:\git\DistributedSystemsProject\testa && python server.py 6001"
timeout /t 10 /nobreak >nul
start cmd /k "cd /d C:\git\DistributedSystemsProject\testa && python server.py 6002"