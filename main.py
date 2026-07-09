import os
from flask import Flask
from flask_cors import CORS
from back_end.Comptabilite import Comptabilite
from back_end.Projet import ProjetManager
from blueprint_menu import (
    init_menu_blueprint,
    init_transactions_blueprint,
    init_stats_blueprint,
    init_prediction_blueprint,
    init_global_blueprint,
    init_projet_blueprint,
)
import os
import sys

# 1. Déterminer où se trouve réellement l'exécutable ou le script
if getattr(sys, 'frozen', False):
    # Chemin du dossier contenant le .exe
    BASE_EXE_DIR = os.path.dirname(sys.executable)
else:
    # Chemin du dossier contenant le script .py en dev
    BASE_EXE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Localiser _data (on cherche dans le dossier de l'exe, ou un dossier parent)
# Si vous avez déplacé _data, ajustez le '..' selon vos besoins
DATA_DIR = os.path.join(BASE_EXE_DIR, '_data')

# Si, après compilation, _data est dans le dossier parent du .exe (cas fréquent)
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(os.path.dirname(BASE_EXE_DIR), '_data')

DB_PATH   = os.path.join(DATA_DIR, 'Compte_rework.db')
JSON_PATH = os.path.join(DATA_DIR, 'projects.json')

# 3. Debug : Écriture du rapport dans le dossier de l'exécutable
debug_log = os.path.join(BASE_EXE_DIR, "debug_path.txt")
with open(debug_log, "w", encoding="utf-8") as f:
    f.write("--- Rapport de Debug ---\n")
    f.write(f"Dossier de l'exe/script : {BASE_EXE_DIR}\n")
    f.write(f"Dossier _data cible : {DATA_DIR}\n")
    f.write(f"DB_PATH attendu : {DB_PATH}\n")
    f.write(f"Le fichier BDD existe ? : {'OUI' if os.path.exists(DB_PATH) else 'NON'}\n")
    f.write(f"Dossier actuel (cwd) : {os.getcwd()}\n")
    
    if not os.path.exists(DB_PATH):
        f.write("\nERREUR CRITIQUE: Le fichier BDD est introuvable !\n")

# Initialisation
compta  = Comptabilite(DB_PATH)
manager = ProjetManager(JSON_PATH, compta.con)
app = Flask(__name__)
CORS(app)

app.register_blueprint(init_menu_blueprint(compta))
app.register_blueprint(init_transactions_blueprint(compta))
app.register_blueprint(init_stats_blueprint(compta))
app.register_blueprint(init_prediction_blueprint(compta))
app.register_blueprint(init_global_blueprint(compta))
app.register_blueprint(init_projet_blueprint(manager))

if __name__ == '__main__':
    try:
        # On désactive debug=True pour le build, c'est crucial !
        app.run(port=5000, debug=False)
    except Exception as e:
        # En cas d'erreur au démarrage, on écrit l'erreur dans un fichier
        # pour pouvoir la lire même si la fenêtre se ferme
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(f"Erreur fatale au lancement : {str(e)}")
        # On attend une entrée pour que vous ayez le temps de lire
        input("Le serveur a crashé. Appuyez sur Entrée pour quitter...")