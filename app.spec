# -*- mode: python ; coding: utf-8 -*-
# app.spec — PyInstaller spec pour l'application Flask
# Usage : pyinstaller app.spec

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Dossier racine du projet (là où se trouve ce .spec) ──────────────────────
ROOT = os.path.dirname(os.path.abspath(SPEC))

# ── Fichiers à embarquer (sources, destination dans le bundle) ───────────────
added_datas = [
    # Toute l'interface HTML/CSS/JS
    (os.path.join(ROOT, 'front_end'), 'front_end'),
    # Données JSON
    (os.path.join(ROOT, '_data'),     '_data'),
    # Icône (aussi accessible au runtime si besoin)
    (os.path.join(ROOT, 'icone.ico'), '.'),
]

# ── Imports cachés que PyInstaller rate souvent ───────────────────────────────
hidden = [
    'flask',
    'flask.templating',
    'jinja2',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.debug',
    'pandas',
    'numpy',
    'sklearn',          # si tu utilises scikit-learn dans analyser_compte
    'scipy',
]
hidden += collect_submodules('core')
hidden += collect_submodules('api')

a = Analysis(
    [os.path.join(ROOT, 'launcher.py')],
    pathex=[ROOT],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PyQt5', 'wx'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # ← --onedir (recommandé avec Flask)
    name='MonAppFinance',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,              # ← False = pas de fenêtre console noire
    icon=os.path.join(ROOT, 'icone.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MonAppFinance',       # ← nom du dossier de sortie dans dist/
)
