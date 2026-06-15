import os
import sys
import threading
import webbrowser
from flask import Flask, render_template, send_from_directory
from core.persistence.database_manager import DatabaseManager

# Import des blueprints
from api.blueprint.Account import account_details_routes
from api.blueprint.Dashboard import compta_routes
from api.blueprint.Intercompte import intercompte_routes
from api.blueprint.Statistic import stats_routes
from api.blueprint.prediction import prediction_routes
from api.blueprint.Objectif import projects_routes

# ── Résolution des chemins (dev ET .exe PyInstaller) ─────────────────────────
def _base_dir() -> str:
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _base_dir()
FRONT_END_DIR = os.path.join(BASE_DIR, 'front_end')
DATA_DIR = os.path.join(BASE_DIR, '_data')

# ── Flask ─────────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=FRONT_END_DIR,
    static_folder=FRONT_END_DIR,
)

# ── DatabaseManager ───────────────────────────────────────────────────────────
goal_path = os.path.join(DATA_DIR, 'goal2.json')
db_manager = DatabaseManager('Compte', goal_path)
app.db_manager = db_manager

# ── Blueprints ────────────────────────────────────────────────────────────────
app.register_blueprint(compta_routes)
app.register_blueprint(account_details_routes)
app.register_blueprint(intercompte_routes)
app.register_blueprint(stats_routes)
app.register_blueprint(prediction_routes)
app.register_blueprint(projects_routes)

# ── Routes HTML ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index/index.html', active='overview')

@app.route('/compte/<int:index>')
def compte(index):
    return render_template('compte/compte.html', active='compte', account_index=index)

@app.route('/intercompte/<int:index>')
def intercompte(index):
    return render_template('intercompte/intercompte.html', active='intercompte', account_index=index)

@app.route('/statistic/<int:index>')
def statistic(index):
    return render_template('statistic/statistic.html', active='statistic', account_index=index)

@app.route('/prediction/<int:index>')
def prediction(index):
    return render_template('prevision/prevision.html', active='prediction', account_index=index)

@app.route('/objectif/<int:index>')
def objectif(index):
    return render_template('objectif/objectif.html', active='objectif', account_index=index)

@app.route('/front_end/<path:path>')
def send_static(path):
    return send_from_directory(FRONT_END_DIR, path)

# ── Lancement ─────────────────────────────────────────────────────────────────
def open_browser():
    """Ouvre le navigateur sur l'app locale."""
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Lance l'ouverture du navigateur dans un thread 
    # pour ne pas bloquer le démarrage de Flask
    threading.Timer(1.0, open_browser).start()
    
    # Lancement du serveur
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)