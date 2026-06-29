from flask import Flask, jsonify, request
from flask_cors import CORS
from Comptabilite import Comptabilite

compta = Comptabilite("./_data/Compte_rework.db")

app = Flask(__name__)
CORS(app)


# ── GET tous les comptes ───────────────────────────────────────────
@app.route('/api/comptes', methods=['GET'])
def get_comptes():
    comptes = compta.list_all_accounts()
    data = []
    for c in comptes:
        if c.actif:
            stats = c.get_account_stats()
            if stats.empty:
                revenus = depenses = solde = 0.0
                debut = fin = None
            else:
                revenus  = round(float(stats['revenu_cumule'].iloc[-1]), 2)
                depenses = round(float(stats['depense_cumule'].iloc[-1]), 2)
                solde    = round(float(stats['solde_cumule'].iloc[-1]), 2)
                debut    = str(stats['date'].iloc[0].date())
                fin      = str(stats['date'].iloc[-1].date())
        else:
            revenus = depenses = solde = 0.0
            dates = c.get_date_range()
            debut, fin = dates[0], dates[1]

        data.append({
            "id":       c.id,
            "name":     c.name,
            "devise":   c.devise,
            "status":   c.actif,
            "debut":    debut,
            "fin":      fin,
            "revenus":  revenus,
            "depenses": depenses,
            "solde":    solde,
        })
    return jsonify(data)


# ── POST créer un compte ───────────────────────────────────────────
@app.route('/api/comptes', methods=['POST'])
def create_compte():
    body   = request.get_json()
    name   = body.get('name', '').strip()
    devise = body.get('devise', 'EUR').upper()

    compta.add_account(name,devise)
    return jsonify({"name": name, "devise": devise}), 201


# ── DELETE supprimer un compte ─────────────────────────────────────
@app.route('/api/comptes/<int:account_id>', methods=['DELETE'])
def delete_compte(account_id):
    compta.delete_account(account_id)
    return jsonify({"deleted": account_id}), 200


# ── PATCH toggle actif/inactif ─────────────────────────────────────
@app.route('/api/comptes/<int:account_id>/toggle', methods=['PATCH'])
def toggle_compte(account_id):
    compte = compta.get_compte(account_id)
    if not compte:
        return jsonify({"error": "Compte introuvable"}), 404
    compte.toggle_actif()
    return jsonify({"id": account_id, "actif": compte.actif}), 200


# ── Hello (debug) ──────────────────────────────────────────────────
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello World depuis Flask!", "test": 50})


if __name__ == '__main__':
    app.run(port=5000, debug=True)