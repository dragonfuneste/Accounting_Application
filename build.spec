# -*- mode: python ; coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# build.spec — PyInstaller spec pour Application Compte V4
#
# Usage :
#   pyinstaller build.spec
#
# Prérequis :
#   pip install pyinstaller
#   L'icône icone.ico doit être dans le même dossier que ce fichier (racine projet).
#
# Résultat :
#   dist/ApplicationCompte/ApplicationCompte.exe  (dossier one-folder)
# ─────────────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path

ROOT = Path(SPECPATH)        # dossier racine du projet (là où est build.spec)

# ── Données à embarquer (assets non-Python) ───────────────────────────────────
# Syntaxe : (source_glob_ou_dossier, destination_dans_le_bundle)
added_datas = [
    # Tous les templates / CSS / JS front-end
    (str(ROOT / 'front_end'),   'front_end'),
    # Données JSON de l'application
    (str(ROOT / '_data'),       '_data'),
]

# ── Imports cachés fréquents avec Flask/Pandas/Jinja2 ────────────────────────
hidden_imports = [
    'flask',
    'flask.templating',
    'jinja2',
    'jinja2.ext',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.debug',
    'pandas',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.skiplist',
    'numpy',
    'openpyxl',         # si tu lis des .xlsx
    'hashlib',
    'logging',
    'uuid',
    'json',
]

a = Analysis(
    [str(ROOT / 'main.py')],        # point d'entrée
    pathex=[str(ROOT)],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'PIL',
        'IPython', 'jupyter', 'notebook',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # one-folder (plus fiable que one-file pour Flask)
    name='ApplicationCompte',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                       # compression UPX si disponible
    console=False,                  # False = pas de fenêtre console noire
    icon=str(ROOT / 'icone.ico'),   # icône .ico à la racine du projet
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ApplicationCompte',
)
