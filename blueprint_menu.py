from flask import Blueprint, jsonify, request
import pandas as pd

menu_bp = Blueprint('menu', __name__, url_prefix='/api/comptes')


def init_menu_blueprint(compta):
    """Injecte l'instance Comptabilite dans les routes du blueprint."""

    # ── GET tous les comptes ───────────────────────────────────────
    @menu_bp.route('', methods=['GET'])
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

    # ── GET détail complet d'un compte ───────────────────────────────
    @menu_bp.route('/<int:account_id>/detail', methods=['GET'])
    def get_compte_detail(account_id):
        compte = compta.get_compte(account_id)
        if not compte:
            return jsonify({"error": "Compte introuvable"}), 404

        cur = compta.con.cursor()
        cur.execute(
            "SELECT date, intitule, categorie, classe, est_revenu, valeur FROM transactions WHERE compte_id = ?",
            (account_id,)
        )
        rows = cur.fetchall()

        if not rows:
            return jsonify({
                "id": compte.id, "name": compte.name, "devise": compte.devise, "actif": compte.actif,
                "periode": {"debut": None, "fin": None, "nb_jours": 0},
                "nb_transactions": 0, "transaction_recurrente": None,
                "evolution_mensuelle": [], "comparaison_mois": None, "cumul": []
            })

        df = pd.DataFrame(rows, columns=['date', 'intitule', 'categorie', 'classe', 'est_revenu', 'valeur'])
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df = df.sort_values('date')

        debut = df['date'].min()
        fin   = df['date'].max()
        nb_jours = (fin - debut).days
        nb_transactions = len(df)

        combo = df.groupby(['categorie', 'classe']).size().sort_values(ascending=False)
        if len(combo) > 0:
            top_cat, top_classe = combo.index[0]
            transaction_recurrente = {"categorie": top_cat, "classe": top_classe, "occurrences": int(combo.iloc[0])}
        else:
            transaction_recurrente = None

        df['month'] = df['date'].dt.to_period('M').astype(str)
        monthly = df.groupby(['month', 'est_revenu'])['valeur'].sum().unstack(fill_value=0)
        if 0 not in monthly.columns: monthly[0] = 0.0
        if 1 not in monthly.columns: monthly[1] = 0.0
        monthly = monthly.sort_index()

        evolution_mensuelle = [
            {"month": m, "depenses": round(float(monthly.loc[m, 0]), 2),
             "revenus": round(float(monthly.loc[m, 1]), 2),
             "solde": round(float(monthly.loc[m, 1] - monthly.loc[m, 0]), 2)}
            for m in monthly.index
        ]

        comparaison_mois = None
        if len(monthly) >= 2:
            last_month, prev_month = monthly.index[-1], monthly.index[-2]
            last_dep, last_rev = monthly.loc[last_month, 0], monthly.loc[last_month, 1]
            prev_dep, prev_rev = monthly.loc[prev_month, 0], monthly.loc[prev_month, 1]
            last_solde, prev_solde = last_rev - last_dep, prev_rev - prev_dep

            def pct_change(new, old):
                return None if old == 0 else round(((new - old) / abs(old)) * 100, 1)

            comparaison_mois = {
                "mois_actuel": last_month, "mois_precedent": prev_month,
                "depenses_pct": pct_change(last_dep, prev_dep),
                "revenus_pct": pct_change(last_rev, prev_rev),
                "solde_pct": pct_change(last_solde, prev_solde),
                "depenses_actuel": round(float(last_dep), 2), "depenses_precedent": round(float(prev_dep), 2),
                "revenus_actuel": round(float(last_rev), 2), "revenus_precedent": round(float(prev_rev), 2),
            }

        df['depense_cumule'] = df.apply(lambda r: r['valeur'] if r['est_revenu'] == 0 else 0, axis=1).cumsum()
        df['revenu_cumule']  = df.apply(lambda r: r['valeur'] if r['est_revenu'] == 1 else 0, axis=1).cumsum()
        df['solde_cumule']   = df['revenu_cumule'] - df['depense_cumule']

        cumul = [
            {"date": d.strftime('%Y-%m-%d'), "depense_cumule": round(float(dc), 2),
             "revenu_cumule": round(float(rc), 2), "solde_cumule": round(float(sc), 2)}
            for d, dc, rc, sc in zip(df['date'], df['depense_cumule'], df['revenu_cumule'], df['solde_cumule'])
        ]

        return jsonify({
            "id": compte.id, "name": compte.name, "devise": compte.devise, "actif": compte.actif,
            "periode": {"debut": debut.strftime('%Y-%m-%d'), "fin": fin.strftime('%Y-%m-%d'), "nb_jours": nb_jours},
            "nb_transactions": nb_transactions, "transaction_recurrente": transaction_recurrente,
            "evolution_mensuelle": evolution_mensuelle, "comparaison_mois": comparaison_mois, "cumul": cumul
        })

    # ── POST créer un compte ─────────────────────────────────────────
    @menu_bp.route('', methods=['POST'])
    def create_compte():
        body   = request.get_json()
        name   = body.get('name', '').strip()
        devise = body.get('devise', 'EUR').upper()
        compta.add_account(name, devise)
        return jsonify({"name": name, "devise": devise}), 201

    # ── DELETE supprimer un compte ───────────────────────────────────
    @menu_bp.route('/<int:account_id>', methods=['DELETE'])
    def delete_compte(account_id):
        compta.delete_account(account_id)
        return jsonify({"deleted": account_id}), 200

    # ── Modifie nom / devise ─────────────────────────────────────────
    @menu_bp.route('/<int:account_id>', methods=['POST'])
    def modify_account(account_id):
        body   = request.get_json()
        name   = body.get('name', None)
        devise = body.get('devise', None)
        name   = name.strip() if name else None
        devise = devise.upper() if devise else None
        compta.modify_account(account_id, name, devise)
        return jsonify({"modify": account_id}), 202

    # ── PATCH toggle actif/inactif ───────────────────────────────────
    @menu_bp.route('/<int:account_id>/toggle', methods=['PATCH'])
    def toggle_compte(account_id):
        compte = compta.get_compte(account_id)
        if not compte:
            return jsonify({"error": "Compte introuvable"}), 404
        compte.toggle_actif()
        return jsonify({"id": account_id, "actif": compte.actif}), 200

    # ── GET historique cumulé entre deux comptes ─────────────────────
    @menu_bp.route('/<int:src_id>/intercompte/<int:dest_id>', methods=['GET'])
    def get_intercompte(src_id, dest_id):
        try:
            df = compta.get_intercompte_stats(src_id, dest_id)
            if df.empty:
                return jsonify([])
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            return jsonify(df.to_dict(orient='records'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── POST effectuer un virement intercompte ────────────────────────
    @menu_bp.route('/<int:src_id>/virement', methods=['POST'])
    def post_virement(src_id):
        body        = request.get_json()
        dest_id     = body.get('dest_id')
        date        = body.get('date')
        commentaire = body.get('commentaire', '')
        valeur_src  = body.get('valeur_src')
        valeur_dest = body.get('valeur_dest', valeur_src)

        if not dest_id or not date or valeur_src is None:
            return jsonify({"error": "Champs manquants (dest_id, date, valeur_src requis)"}), 400
        if src_id == dest_id:
            return jsonify({"error": "Le compte source et destinataire doivent être différents"}), 400

        try:
            compta.set_intercompte_transfert(src_id, dest_id, date, commentaire, valeur_src, valeur_dest)
            return jsonify({"success": True}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return menu_bp


def init_transactions_blueprint(compta):
    from flask import Blueprint
    tx_bp = Blueprint('transactions', __name__, url_prefix='/api/comptes')

    # ── GET transactions d'un compte ──────────────────────────────────
    @tx_bp.route('/<int:account_id>/transactions', methods=['GET'])
    def get_transactions(account_id):
        cur = compta.con.cursor()
        cur.execute(
            """SELECT id, date, intitule, categorie, classe, est_revenu, valeur
               FROM transactions WHERE compte_id = ? ORDER BY date DESC""",
            (account_id,)
        )
        rows = cur.fetchall()
        cols = ['id', 'date', 'intitule', 'categorie', 'classe', 'est_revenu', 'valeur']
        return jsonify([dict(zip(cols, r)) for r in rows])

    # ── GET valeurs distinctes pour les dropdowns ─────────────────────
    @tx_bp.route('/<int:account_id>/transactions/options', methods=['GET'])
    def get_options(account_id):
        cur = compta.con.cursor()
        cur.execute("SELECT DISTINCT categorie FROM transactions WHERE compte_id=? ORDER BY categorie", (account_id,))
        categories = [r[0] for r in cur.fetchall() if r[0]]
        cur.execute("SELECT DISTINCT classe FROM transactions WHERE compte_id=? ORDER BY classe", (account_id,))
        classes = [r[0] for r in cur.fetchall() if r[0]]
        return jsonify({"categories": categories, "classes": classes})

    # ── POST ajouter une transaction ──────────────────────────────────
    @tx_bp.route('/<int:account_id>/transactions', methods=['POST'])
    def add_transaction(account_id):
        compte = compta.get_compte(account_id)
        if not compte:
            return jsonify({"error": "Compte introuvable"}), 404
        body = request.get_json()
        try:
            cur = compta.con.cursor()
            cur.execute(
                """INSERT INTO transactions (compte_id, date, intitule, categorie, classe, est_revenu, valeur)
                   VALUES (?,?,?,?,?,?,?)""",
                (account_id, body['date'], body['intitule'], body['categorie'],
                 body['classe'], int(bool(body['est_revenu'])), float(body['valeur']))
            )
            compta.con.commit()
            return jsonify({"success": True}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── PUT modifier une transaction ──────────────────────────────────
    @tx_bp.route('/<int:account_id>/transactions/<int:tx_id>', methods=['PUT'])
    def modify_transaction(account_id, tx_id):
        body = request.get_json()
        try:
            cur = compta.con.cursor()
            cur.execute(
                """UPDATE transactions SET date=?, intitule=?, categorie=?, classe=?, est_revenu=?, valeur=?
                   WHERE id=? AND compte_id=?""",
                (body['date'], body['intitule'], body['categorie'], body['classe'],
                 int(bool(body['est_revenu'])), float(body['valeur']), tx_id, account_id)
            )
            compta.con.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── DELETE supprimer une transaction ──────────────────────────────
    @tx_bp.route('/<int:account_id>/transactions/<int:tx_id>', methods=['DELETE'])
    def delete_transaction(account_id, tx_id):
        try:
            cur = compta.con.cursor()
            cur.execute("DELETE FROM transactions WHERE id=? AND compte_id=?", (tx_id, account_id))
            compta.con.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return tx_bp