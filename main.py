import os
from flask import Flask, render_template, jsonify, request
from Comptabilite import Comptabilite

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
compta = Comptabilite(os.path.join(BASE_DIR, '_data', 'Compte_rework.db'))


@app.route('/')
def index():
    return render_template('menu_compte.html')

@app.route('/compte')
def compte():
    return render_template('compte_sub_menu.html')


@app.route('/api/comptes')
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

        # count transactions
        compta.cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE compte_id = ?", (c.id,)
        )
        nb_transactions = compta.cursor.fetchone()[0]

        data.append({
            "id": c.id,
            "name": c.name,
            "devise": c.devise,
            "actif": c.actif,
            "debut": debut,
            "fin": fin,
            "revenus": revenus,
            "depenses": depenses,
            "solde": solde,
            "nb_transactions": nb_transactions
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


@app.route('/api/comptes', methods=['POST'])
def create_compte():
    body   = request.get_json()
    name   = body.get('name', '').strip()
    devise = body.get('devise', 'EUR').strip().upper()
    if not name:
        return jsonify({"error": "Nom requis"}), 400
    try:
        metadata = str((devise, 1))
        compta.cursor.execute(
            "INSERT INTO comptes (nom_compte, metadata) VALUES (?, ?)",
            (name, metadata)
        )
        compta.con.commit()
        new_id = compta.cursor.lastrowid
        return jsonify({"success": True, "id": new_id, "name": name, "devise": devise})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/comptes/<int:account_id>', methods=['DELETE'])
def delete_compte(account_id):
    compte = compta.get_compte(account_id)
    if not compte:
        return jsonify({"error": "Compte introuvable"}), 404
    try:
        compta.cursor.execute("DELETE FROM transactions WHERE compte_id = ?", (account_id,))
        compta.cursor.execute("DELETE FROM comptes WHERE id = ?", (account_id,))
        compta.con.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/virement', methods=['POST'])
def virement():
    body        = request.get_json()
    source_id   = body.get('source_id')
    dest_id     = body.get('dest_id')
    date        = body.get('date')
    commentaire = body.get('commentaire', 'Virement')
    valeur_src  = float(body.get('valeur_source'))
    valeur_dest = float(body.get('valeur_dest', valeur_src))

    if not all([source_id, dest_id, date, valeur_src]):
        return jsonify({"error": "Champs manquants"}), 400
    if source_id == dest_id:
        return jsonify({"error": "Source et destination identiques"}), 400

    try:
        compta.set_intercompte_transfert(
            source_id, dest_id, date, commentaire, valeur_src, valeur_dest
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/comptes/<int:account_id>/intercompte')
def get_intercompte(account_id):
    """Stats des transactions entre deux comptes"""
    dest_id = request.args.get('dest_id', type=int)
    if not dest_id:
        return jsonify({"error": "dest_id requis"}), 400
    print("Teste :", account_id, dest_id)
    df = compta.get_intercompte_stats(account_id, dest_id)
    return jsonify(df.to_dict(orient='records'))



@app.route('/api/comptes/<int:account_id>/transactions')
def get_transactions(account_id):
    """Retourne les transactions d'un compte, filtrable par classe"""
    classe = request.args.get('classe')
    try:
        if classe:
            compta.cursor.execute(
                """SELECT id, date, intitule, categorie, classe, est_revenu, valeur
                   FROM transactions WHERE compte_id = ? AND classe = ?
                   ORDER BY date DESC""",
                (account_id, classe)
            )
        else:
            compta.cursor.execute(
                """SELECT id, date, intitule, categorie, classe, est_revenu, valeur
                   FROM transactions WHERE compte_id = ?
                   ORDER BY date DESC""",
                (account_id,)
            )
        rows = compta.cursor.fetchall()
        cols = ['id','date','intitule','categorie','classe','est_revenu','valeur']
        return jsonify([dict(zip(cols, r)) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/intercompte')
def intercompte():
    return render_template('intercompte.html')


if __name__ == '__main__':
    app.run(debug=True)