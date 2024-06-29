@echo off
REM Open server on port 6001
start cmd /k "cd /d C:\git\DistributedSystemsProject\test16 && python client.py"

REM Open server on port 6002
start cmd /k "cd /d C:\git\DistributedSystemsProject\test16 && python client.py"

REM Open server on port 6003
start cmd /k "cd /d C:\git\DistributedSystemsProject\test16 && python client.py"
