@echo off
echo [1/4] Activation de la venv...
call "%~dp0venv\Scripts\activate.bat"

echo [2/4] Installation de PyInstaller dans la venv...
pip install pyinstaller --quiet

echo [3/4] Generation du .exe...
pyinstaller app.spec --clean --noconfirm

echo [4/4] Termine !
echo Le .exe se trouve dans : dist\MonAppFinance\MonAppFinance.exe
pause