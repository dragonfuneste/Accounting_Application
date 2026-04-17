import os
from flask import Flask, render_template, send_from_directory
from core.persistence.database_manager import DatabaseManager
from api.blueprint.Account import account_details_routes # Import du nouveau blueprint
from api.blueprint.Dashboard import compta_routes
from api.blueprint.Intercompte import intercompte_routes
from api.blueprint.Statistic import stats_routes
# Puisque main.py est dans New_structure, on cible le dossier front_end à côté
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONT_END_DIR = os.path.join(BASE_DIR, "front_end")


# Chemin vers le dossier qui contient tes dossiers 'index', 'compte' et '_template'
template_dir = os.path.abspath('front_end')

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=template_dir) # Si tu stockes tes CSS/JS au même endroit


# Initialisation du Manager (Source de vérité)
#db_manager = DatabaseManager("Compte") 
db_manager = DatabaseManager("Compte") 
app.db_manager = db_manager

# Enregistrement du Blueprint API
app.register_blueprint(compta_routes)
app.register_blueprint(account_details_routes)
app.register_blueprint(intercompte_routes)
app.register_blueprint(stats_routes)
# --- ROUTES POUR L'INTERFACE ---

@app.route('/')
def index():
    return render_template('index/index.html', active='overview')

@app.route('/compte/<int:index>')
def compte(index):
    return render_template('compte/compte.html', active='compte', account_index=index)

@app.route('/intercompte/<int:index>')
def intercompte(index):
    return render_template('intercompte/intercompte.html', active='intercompte', account_index=index)
# Route pour servir les fichiers statiques (CSS/JS) correctement
@app.route('/statistic/<int:index>')
def statistic(index):
    return render_template('statistic/statistic.html', active='statistic', account_index=index)

@app.route('/front_end/<path:path>')
def send_static(path):
    return send_from_directory(FRONT_END_DIR, path)

if __name__ == "__main__":
    app.run(debug=True)