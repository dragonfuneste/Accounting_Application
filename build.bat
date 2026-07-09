@echo off
echo ============================================
echo   BUILD - Mes Comptes
echo ============================================

rmdir /s /q node_modules
del package-lock.json
call npm install --legacy-peer-deps
:: 1. Builder le frontend React
echo.
echo [1/4] Build du frontend React...
call npm run build
if errorlevel 1 (
    echo ERREUR: npm run build a echoue
    pause
    exit /b 1
)
echo Frontend build OK

:: 2. Copier le dist React
echo.
echo [2/4] Copie du frontend build...
if exist frontend_dist rmdir /s /q frontend_dist
xcopy /e /i /q dist frontend_dist
echo Frontend copie OK

:: 3. Packager Flask avec PyInstaller
:: 3. Packager Flask avec PyInstaller
echo.
echo [3/4] Packaging du backend Python...
call .accounting_venv\Scripts\activate.bat

:: Si backend.spec existe, on l'utilise, sinon on crée l'exécutable directement à partir de main.py
if exist backend.spec (
    pyinstaller backend.spec --noconfirm
) else (
    pyinstaller --name backend_app --onefile --windowed main.py --noconfirm
)

if errorlevel 1 (
    echo ERREUR: PyInstaller a echoue
    pause
    exit /b 1
)
echo Backend packaged OK

:: 4. Builder l'app Electron
echo.
echo [4/4] Build de l'application Electron...
cd electron
call npm install 
call npm audit fix --force
call $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
call npm approve-scripts electron-winstaller
call npm run build:win

if errorlevel 1 (
    echo ERREUR: electron-builder a echoue
    pause
    exit /b 1
)
cd ..

echo.
echo ============================================
echo   BUILD TERMINE !
echo   Installer dans : electron\release\
echo ============================================
pause