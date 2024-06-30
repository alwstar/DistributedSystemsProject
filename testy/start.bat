@echo off
REM Open command line
start cmd /k "cd /d C:\git\DistributedSystemsProject\testy && python server.py 6001"
start cmd /k "cd /d C:\git\DistributedSystemsProject\testy && python client.py"
start cmd /k "cd /d C:\git\DistributedSystemsProject\testy && python client.py"
start cmd /k "cd /d C:\git\DistributedSystemsProject\testy && python client.py"
timeout /t 10 /nobreak >nul
start cmd /k "cd /d C:\git\DistributedSystemsProject\testy && python server.py 6002"