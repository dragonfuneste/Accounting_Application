import os
from flask import Flask, render_template, jsonify, request
from Comptabilite import Comptabilite

app = Flask(__name__)


DB_PATH = os.path.join('_data/Compte_rework.db')
compta = Comptabilite(DB_PATH)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/comptes')
def get_comptes():
    comptes = compta.list_all_accounts()
    data = []
    for c in comptes:
        dates = c.get_date_range()
        if c.actif:
            stats = c.get_stats()
            revenus  = round(stats['revenus'], 2)
            depenses = round(stats['depenses'], 2)
            solde    = round(stats['solde'], 2)
        else:
            revenus = depenses = solde = 0.0
        data.append({
            "id": c.id,
            "name": c.name,
            "devise": c.devise,
            "actif": c.actif,
            "debut": dates[0],
            "fin": dates[1],
            "revenus": revenus,
            "depenses": depenses,
            "solde": solde
        })
    return jsonify(data)


@app.route('/api/comptes/<int:account_id>/edit', methods=['POST'])
def edit_compte(account_id):
    compte = compta.get_compte(account_id)
    if not compte:
        return jsonify({"error": "Compte introuvable"}), 404
    body = request.get_json()
    if 'name' in body:
        compte.modify_name(body['name'])
    if 'devise' in body:
        compte.modify_devise(body['devise'])
    return jsonify({"success": True, "name": compte.name, "devise": compte.devise})


@app.route('/api/comptes/<int:account_id>/toggle', methods=['POST'])
def toggle_compte(account_id):
    compte = compta.get_compte(account_id)
    if not compte:
        return jsonify({"error": "Compte introuvable"}), 404
    compte.toggle_actif()
    return jsonify({"success": True, "actif": compte.actif})


if __name__ == '__main__':
    app.run(debug=True)