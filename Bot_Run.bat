@echo off

call %~dp0venv\Scripts\activate

cd %~dp0application



python app.py

pause