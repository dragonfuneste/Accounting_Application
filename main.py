from flask import Flask
from flask_cors import CORS
from Comptabilite import Comptabilite
from blueprint_menu import init_menu_blueprint, init_transactions_blueprint

compta = Comptabilite("./_data/Compte_rework.db")

app = Flask(__name__)
CORS(app)

app.register_blueprint(init_menu_blueprint(compta))
app.register_blueprint(init_transactions_blueprint(compta))


if __name__ == '__main__':
    app.run(port=5000, debug=True)