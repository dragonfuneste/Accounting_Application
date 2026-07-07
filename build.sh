#!/bin/bash
set -e

echo "============================================"
echo "  BUILD - Mes Comptes (Linux)"
echo "============================================"

# 1. Frontend React
echo ""
echo "[1/4] Build du frontend React..."
npm run build
echo "Frontend build OK"

# 2. Copier dist
echo ""
echo "[2/4] Copie du frontend build..."
rm -rf frontend_dist
cp -r dist frontend_dist
echo "Frontend copié OK"

# 3. PyInstaller
echo ""
echo "[3/4] Packaging du backend Python..."
source .accounting_venv/bin/activate
pip install pyinstaller -q
pyinstaller backend.spec --distpath dist_backend --workpath build_temp --noconfirm
echo "Backend packagé OK"

# 4. Electron
echo ""
echo "[4/4] Build de l'application Electron..."
cd electron
npm install -q
npm run build:linux
cd ..

echo ""
echo "============================================"
echo "  BUILD TERMINÉ !"
echo "  AppImage dans : electron/release/"
echo "============================================"