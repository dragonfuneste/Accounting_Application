import os
from flask import Flask
from flask_cors import CORS
from Comptabilite import Comptabilite
from Projet import ProjetManager
from blueprint_menu import (
    init_menu_blueprint,
    init_transactions_blueprint,
    init_stats_blueprint,
    init_prediction_blueprint,
    init_global_blueprint,
    init_projet_blueprint,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, '_data', 'Compte_rework.db')
JSON_PATH = os.path.join(BASE_DIR, '_data', 'projects.json')

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
    app.run(port=5000, debug=True)