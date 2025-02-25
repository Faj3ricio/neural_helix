@echo off
set PYTHONPATH=C:\Users\login\pasta\raiz\do\projeto
cd /d C:\Users\login\pasta\onde\esta\o\scheduler
call C:\Users\login\Documents\pasta\.venv\Scripts\activate.bat
start /B pythonw scheduler.py > scheduler.log 2>&1
