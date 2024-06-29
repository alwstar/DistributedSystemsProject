@echo off
REM Open server on port 6001
start cmd /k "cd /d C:\git\DistributedSystemsProject\test22 && python server.py 6001"

REM Open server on port 6002
start cmd /k "cd /d C:\git\DistributedSystemsProject\test22 && python server.py 6002"

REM Open server on port 6003
start cmd /k "cd /d C:\git\DistributedSystemsProject\test22 && python server.py 6003"
