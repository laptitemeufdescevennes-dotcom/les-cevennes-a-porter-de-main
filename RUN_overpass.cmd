@echo off
cd /d %~dp0
py -3 scripts\fetch_overpass_poi.py
pause
