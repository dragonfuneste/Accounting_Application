"""
launcher.py  — Point d'entrée PyInstaller-compatible pour l'app Flask.

PyInstaller extrait les fichiers dans un dossier temporaire (_MEIPASS) quand
on utilise --onefile, ou dans le dossier du .exe en mode --onedir.
Ce module patch les chemins AVANT d'importer main, pour que Flask trouve
bien le dossier front_end et _data, qu'on soit en dev ou en .exe.
"""

import sys
import os


def resource_path(relative: str) -> str:
    """
    Retourne le chemin absolu vers `relative`, que l'on soit :
    - en développement (chemin normal relatif au script)
    - en .exe PyInstaller (chemin dans le dossier extrait _MEIPASS / dossier exe)
    """
    if hasattr(sys, '_MEIPASS'):
        # Mode .exe PyInstaller (one-folder ou one-file)
        base = sys._MEIPASS
    else:
        # Mode développement
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


# ── Patch des chemins avant import de main ────────────────────────────────────
# On injecte le dossier racine résolu dans sys.path pour que tous les imports
# relatifs (core, api, etc.) fonctionnent depuis le bon endroit.
_root = resource_path('.')
if _root not in sys.path:
    sys.path.insert(0, _root)

# On change aussi le répertoire de travail courant pour que les chemins
# relatifs dans main.py (ex : "./_data/goal2.json") pointent au bon endroit.
os.chdir(_root)


# ── Import et lancement de l'app ──────────────────────────────────────────────
if __name__ == '__main__':
    # Import différé : main.py doit trouver ses modules core/api grâce au sys.path patché
    import main  # noqa: F401 — le import suffit, app.run() est dans le if __name__ de main