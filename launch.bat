@echo off
:: 1. Active l'environnement virtuel
call D:\Software\Accounting_Application\venv\Scripts\activate.bat

:: 2. Ouvre le navigateur sur ton adresse locale
start http://127.0.0.1:5000

:: 3. Lance le serveur Python
python D:\Software\Accounting_Application\main.py

pause