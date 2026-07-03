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


def init_stats_blueprint(compta):
    from flask import Blueprint
    import pandas as pd
    import numpy as np
    stats_bp = Blueprint('stats', __name__, url_prefix='/api/comptes')

    @stats_bp.route('/<int:account_id>/stats', methods=['GET'])
    def get_stats(account_id):
        from flask import request as freq
        date_debut    = freq.args.get('date_debut')
        date_fin      = freq.args.get('date_fin')
        sans_virement = freq.args.get('sans_virement', 'false').lower() == 'true'

        cur = compta.con.cursor()
        cur.execute("SELECT id, date, intitule, categorie, classe, est_revenu, valeur FROM transactions WHERE compte_id=?", (account_id,))
        rows = cur.fetchall()

        if not rows:
            return jsonify({"months": [], "summary": {}, "monthly": [], "top3_monthly": [],
                            "cumul": [], "by_categorie": [], "top5_depenses": []})

        df = pd.DataFrame(rows, columns=['id','date','intitule','categorie','classe','est_revenu','valeur'])
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df = df.sort_values('date')

        # Tous les mois disponibles
        df['month'] = df['date'].dt.to_period('M')
        all_months = sorted(df['month'].unique().astype(str).tolist())

        # Filtrage période
        if date_debut:
            df = df[df['date'] >= pd.to_datetime(date_debut)]
        if date_fin:
            df = df[df['date'] <= pd.to_datetime(date_fin)]
        if sans_virement:
            df = df[df['categorie'] != 'Virement']

        if df.empty:
            return jsonify({"months": all_months, "summary": {}, "monthly": [], "top3_monthly": [],
                            "cumul": [], "by_categorie": [], "top5_depenses": []})

        df['month'] = df['date'].dt.to_period('M')

        # ── Résumé global ─────────────────────────────────────────────
        total_rev  = float(df[df['est_revenu']==1]['valeur'].sum())
        total_dep  = float(df[df['est_revenu']==0]['valeur'].sum())
        total_solde = total_rev - total_dep

        # ── Mensuel ───────────────────────────────────────────────────
        monthly_grp = df.groupby(['month','est_revenu'])['valeur'].sum().unstack(fill_value=0)
        if 0 not in monthly_grp.columns: monthly_grp[0] = 0.0
        if 1 not in monthly_grp.columns: monthly_grp[1] = 0.0

        monthly = []
        for m in monthly_grp.index:
            dep = float(monthly_grp.loc[m, 0])
            rev = float(monthly_grp.loc[m, 1])
            monthly.append({"month": str(m), "depenses": round(dep,2),
                            "revenus": round(rev,2), "solde": round(rev-dep,2)})

        avg_rev = round(sum(r['revenus']  for r in monthly) / len(monthly), 2)
        avg_dep = round(sum(r['depenses'] for r in monthly) / len(monthly), 2)
        avg_solde = round(avg_rev - avg_dep, 2)

        # ── Top 3 dépenses récurrentes par mois ───────────────────────
        top3_monthly = []
        for m in df['month'].unique():
            mdf = df[(df['month']==m) & (df['est_revenu']==0)]
            top = mdf.groupby(['intitule','categorie','classe'])['valeur'].sum().sort_values(ascending=False).head(3)
            top3_monthly.append({
                "month": str(m),
                "top3": [{"intitule": idx[0], "categorie": idx[1], "classe": idx[2], "valeur": round(float(v),2)}
                         for idx, v in top.items()]
            })

        # ── Cumulé pour graphique ─────────────────────────────────────
        df_s = df.sort_values('date').copy()
        df_s['dep_cum'] = df_s.apply(lambda r: r['valeur'] if r['est_revenu']==0 else 0, axis=1).cumsum()
        df_s['rev_cum'] = df_s.apply(lambda r: r['valeur'] if r['est_revenu']==1 else 0, axis=1).cumsum()
        df_s['solde_cum'] = df_s['rev_cum'] - df_s['dep_cum']

        # Tendance linéaire sur le solde cumulé
        x = np.arange(len(df_s))
        y = df_s['solde_cum'].values
        if len(x) > 1:
            coeffs = np.polyfit(x, y, 1)
            trend = np.polyval(coeffs, x).tolist()
        else:
            trend = y.tolist()

        cumul = [{
            "date": d.strftime('%Y-%m-%d'),
            "solde_cumule": round(float(s),2),
            "rev_cumule":   round(float(r),2),
            "dep_cumule":   round(float(dp),2),
            "trend":        round(float(t),2)
        } for d, s, r, dp, t in zip(df_s['date'], df_s['solde_cum'], df_s['rev_cum'], df_s['dep_cum'], trend)]

        solde_vals = [c['solde_cumule'] for c in cumul]
        cumul_meta = {
            "min": round(min(solde_vals),2),
            "max": round(max(solde_vals),2),
            "current": round(solde_vals[-1],2),
            "min_date": cumul[solde_vals.index(min(solde_vals))]['date'],
            "max_date": cumul[solde_vals.index(max(solde_vals))]['date'],
        }

        # ── Par catégorie (pour Sankey + camemberts) ──────────────────
        dep_by_cat = df[df['est_revenu']==0].groupby('categorie')['valeur'].sum().sort_values(ascending=False)
        rev_by_cat = df[df['est_revenu']==1].groupby('categorie')['valeur'].sum().sort_values(ascending=False)

        by_categorie_dep = [{"categorie": k, "valeur": round(float(v),2)} for k,v in dep_by_cat.items()]
        by_categorie_rev = [{"categorie": k, "valeur": round(float(v),2)} for k,v in rev_by_cat.items()]

        # Classes par catégorie
        classes_by_cat = {}
        for cat in df['categorie'].unique():
            sub = df[df['categorie']==cat]
            grp = sub.groupby('classe')['valeur'].sum().sort_values(ascending=False)
            classes_by_cat[cat] = [{"classe": k, "valeur": round(float(v),2)} for k,v in grp.items()]

        # ── Top 5 dépenses par intitulé ────────────────────────────────
        top5 = df[df['est_revenu']==0].groupby(['intitule','categorie','classe'])['valeur'].sum()\
               .sort_values(ascending=False).head(5)
        top5_depenses = [{"intitule": idx[0], "categorie": idx[1], "classe": idx[2], "total": round(float(v),2)}
                         for idx, v in top5.items()]

        return jsonify({
            "months": all_months,
            "summary": {
                "total_rev": round(total_rev,2),
                "total_dep": round(total_dep,2),
                "total_solde": round(total_solde,2),
                "avg_rev": avg_rev, "avg_dep": avg_dep, "avg_solde": avg_solde
            },
            "monthly": monthly,
            "top3_monthly": top3_monthly,
            "cumul": cumul,
            "cumul_meta": cumul_meta,
            "by_categorie_dep": by_categorie_dep,
            "by_categorie_rev": by_categorie_rev,
            "classes_by_cat": classes_by_cat,
            "top5_depenses": top5_depenses
        })

    return stats_bp


def init_stats_blueprint(compta):
    from flask import Blueprint
    stats_bp = Blueprint('stats', __name__, url_prefix='/api/comptes')

    @stats_bp.route('/<int:account_id>/stats', methods=['GET'])
    def get_stats(account_id):
        import numpy as np
        exclude_virement = request.args.get('exclude_virement', 'false').lower() == 'true'
        date_debut = request.args.get('debut')
        date_fin   = request.args.get('fin')

        cur = compta.con.cursor()
        cur.execute("SELECT * FROM transactions WHERE compte_id=?", (account_id,))
        rows = cur.fetchall()
        cols = ['id','compte_id','date','intitule','categorie','classe','est_revenu','valeur']

        import pandas as pd
        if not rows:
            return jsonify({"empty": True})

        df = pd.DataFrame(rows, columns=cols)
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df = df.sort_values('date')

        # ── Filtre virement ────────────────────────────────
        if exclude_virement:
            df = df[df['categorie'] != 'Virement']

        # ── Filtre période ─────────────────────────────────
        all_months = sorted(df['date'].dt.to_period('M').astype(str).unique().tolist())

        if date_debut:
            df = df[df['date'].dt.to_period('M').astype(str) >= date_debut]
        if date_fin:
            df = df[df['date'].dt.to_period('M').astype(str) <= date_fin]

        if df.empty:
            return jsonify({"empty": True, "all_months": all_months})

        df['month'] = df['date'].dt.to_period('M').astype(str)

        # ── Totaux période ─────────────────────────────────
        total_rev = float(df[df['est_revenu']==1]['valeur'].sum())
        total_dep = float(df[df['est_revenu']==0]['valeur'].sum())
        total_solde = total_rev - total_dep

        # ── Mensuel ────────────────────────────────────────
        monthly = df.groupby(['month','est_revenu'])['valeur'].sum().unstack(fill_value=0)
        if 0 not in monthly.columns: monthly[0] = 0.0
        if 1 not in monthly.columns: monthly[1] = 0.0
        monthly = monthly.sort_index()
        monthly['solde'] = monthly[1] - monthly[0]

        evolution_mensuelle = [
            {"month": m,
             "revenus": round(float(monthly.loc[m,1]),2),
             "depenses": round(float(monthly.loc[m,0]),2),
             "solde": round(float(monthly.loc[m,'solde']),2)}
            for m in monthly.index
        ]

        avg_rev = round(float(monthly[1].mean()), 2)
        avg_dep = round(float(monthly[0].mean()), 2)
        avg_solde = round(float(monthly['solde'].mean()), 2)

        # ── Top 3 dépenses récurrentes par mois ────────────
        dep_df = df[df['est_revenu']==0].copy()
        top3_rows = (dep_df.groupby(['month','intitule'])['valeur']
                     .agg(['sum','count']).reset_index()
                     .rename(columns={'sum':'total','count':'occurrences'}))
        top3_rows = top3_rows.sort_values(['month','total'], ascending=[True,False])
        top3_per_month = top3_rows.groupby('month').head(3)
        top3_dict = {}
        for _, r in top3_per_month.iterrows():
            top3_dict.setdefault(r['month'], []).append({
                "intitule": r['intitule'],
                "total": round(float(r['total']),2),
                "occurrences": int(r['occurrences'])
            })

        # ── Cumulé + tendance ───────────────────────────────
        df_sorted = df.sort_values('date').copy()
        df_sorted['delta'] = df_sorted.apply(
            lambda r: r['valeur'] if r['est_revenu']==1 else -r['valeur'], axis=1)
        df_sorted['cumul'] = df_sorted['delta'].cumsum()

        cumul_vals = df_sorted['cumul'].values.tolist()
        dates_str  = df_sorted['date'].dt.strftime('%Y-%m-%d').tolist()

        n = len(cumul_vals)
        x = np.arange(n)
        slope, intercept = np.polyfit(x, cumul_vals, 1)
        trend = (slope * x + intercept).tolist()

        cumul_min = round(float(min(cumul_vals)), 2)
        cumul_max = round(float(max(cumul_vals)), 2)
        cumul_cur = round(float(cumul_vals[-1]), 2)

        cumul_series = [
            {"date": d, "cumul": round(float(v),2), "trend": round(float(t),2)}
            for d, v, t in zip(dates_str, cumul_vals, trend)
        ]

        # ── Sankey / camembert par catégorie ───────────────
        cat_dep = (dep_df.groupby('categorie')['valeur'].sum()
                   .sort_values(ascending=False).reset_index())
        cat_rev = (df[df['est_revenu']==1].groupby('categorie')['valeur'].sum()
                   .sort_values(ascending=False).reset_index())

        sankey_dep = [{"categorie": r['categorie'], "valeur": round(float(r['valeur']),2)}
                      for _, r in cat_dep.iterrows()]
        sankey_rev = [{"categorie": r['categorie'], "valeur": round(float(r['valeur']),2)}
                      for _, r in cat_rev.iterrows()]

        # Classes par catégorie (pour drill-down camembert)
        classes_by_cat = {}
        for cat in dep_df['categorie'].unique():
            sub = dep_df[dep_df['categorie']==cat].groupby('classe')['valeur'].sum()
            sub = sub.sort_values(ascending=False)
            classes_by_cat[cat] = [{"classe": k, "valeur": round(float(v),2)}
                                    for k, v in sub.items()]

        # ── Top 5 dépenses par intitulé ────────────────────
        top5 = (dep_df.groupby('intitule')['valeur'].sum()
                .nlargest(5).reset_index()
                .rename(columns={'valeur':'total'}))
        top5_list = [{"intitule": r['intitule'], "total": round(float(r['total']),2)}
                     for _, r in top5.iterrows()]

        return jsonify({
            "empty": False,
            "all_months": all_months,
            "periode": {"debut": dates_str[0], "fin": dates_str[-1]},
            "totaux": {"revenus": round(total_rev,2), "depenses": round(total_dep,2), "solde": round(total_solde,2)},
            "moyennes": {"revenus": avg_rev, "depenses": avg_dep, "solde": avg_solde},
            "evolution_mensuelle": evolution_mensuelle,
            "top3_par_mois": top3_dict,
            "cumul_series": cumul_series,
            "cumul_stats": {"min": cumul_min, "max": cumul_max, "actuel": cumul_cur},
            "sankey": {"depenses": sankey_dep, "revenus": sankey_rev},
            "classes_by_cat": classes_by_cat,
            "top5_depenses": top5_list,
        })

    return stats_bp


def init_prediction_blueprint(compta):
    from flask import Blueprint
    pred_bp = Blueprint('prediction', __name__, url_prefix='/api/comptes')

    @pred_bp.route('/<int:account_id>/prediction', methods=['GET'])
    def get_prediction(account_id):
        try:
            from rapidfuzz import fuzz
        except ImportError:
            return jsonify({"error": "rapidfuzz non installé : pip install rapidfuzz"}), 500

        import pandas as pd, datetime, calendar

        n_months = int(request.args.get('n_months', 3))
        n_months = max(1, min(n_months, 24))

        cur = compta.con.cursor()
        cur.execute("SELECT * FROM transactions WHERE compte_id=? ORDER BY date DESC", (account_id,))
        rows = cur.fetchall()
        cols = ['id','compte_id','date','intitule','categorie','classe','est_revenu','valeur']

        if not rows:
            return jsonify({"predictions": [], "max_months": 0})

        df = pd.DataFrame(rows, columns=cols)
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df = df.sort_values('date')

        # Nombre de mois disponibles
        all_months = df['date'].dt.to_period('M').nunique()

        today = df['date'].max()
        cutoff = today - pd.DateOffset(months=n_months)
        window = df[df['date'] >= cutoff].copy()
        window_months = window['date'].dt.to_period('M').nunique()
        if window_months == 0:
            return jsonify({"predictions": [], "max_months": int(all_months)})

        # ── Regroupement fuzzy ────────────────────────────────
        # partial_ratio : détecte si une chaîne est contenue dans l'autre
        # ex: "Assurance" ≈ "Assurance swisscare" → 100%
        groups = {}
        for _, row in window.iterrows():
            key_base = (row['categorie'], row['classe'])
            label = str(row['intitule']).strip()
            matched_key = None
            best_score = 0
            for gkey in list(groups.keys()):
                if gkey[0] == key_base[0] and gkey[1] == key_base[1]:
                    score = fuzz.partial_ratio(label.lower(), gkey[2].lower())
                    if score >= 60 and score > best_score:
                        best_score = score
                        matched_key = gkey
            if matched_key:
                groups[matched_key].append(row)
            else:
                groups[(*key_base, label)] = [row]

        # ── Calcul prédictions ────────────────────────────────
        predictions = []
        next_month = (today + pd.DateOffset(months=1)).replace(day=1)

        for gkey, grows in groups.items():
            cat, classe, intitule = gkey
            months_seen = len(set(
                pd.Timestamp(r['date']).to_period('M') for r in grows
            ))
            # Dénominateur = n_months demandés, pas les mois uniques de la fenêtre
            # (évite la surestimation quand la fenêtre chevauche N+1 mois partiels)
            proba = round((months_seen / max(n_months, 1)) * 100, 1)
            vals  = [r['valeur'] for r in grows]
            avg_val = round(sum(vals) / len(vals), 2)
            days  = [pd.Timestamp(r['date']).day for r in grows]
            avg_day = int(round(sum(days) / len(days)))
            # clamp au dernier jour du mois suivant
            last_day = calendar.monthrange(next_month.year, next_month.month)[1]
            avg_day  = min(avg_day, last_day)
            pred_date = next_month.replace(day=avg_day).strftime('%Y-%m-%d')

            est_revenu = int(round(sum(r['est_revenu'] for r in grows) / len(grows)))

            predictions.append({
                'intitule':    intitule,
                'categorie':   cat,
                'classe':      classe,
                'est_revenu':  est_revenu,
                'valeur':      avg_val,
                'date':        pred_date,
                'probabilite': proba,
                'occurrences': len(grows),
                'mois_vus':    months_seen,
            })

        predictions.sort(key=lambda x: (-x['probabilite'], x['date']))

        # ── Cumul prédictif ───────────────────────────────────
        # Solde actuel réel
        df['delta'] = df.apply(
            lambda r: r['valeur'] if r['est_revenu'] == 1 else -r['valeur'], axis=1
        )
        solde_actuel = round(float(df['delta'].sum()), 2)

        # Projeter les prédictions triées par date
        cumul_pred = []
        running = solde_actuel
        rev_total = dep_total = 0.0
        for p in sorted(predictions, key=lambda x: x['date']):
            impact = p['valeur'] if p['est_revenu'] else -p['valeur']
            running = round(running + impact, 2)
            if p['est_revenu']:
                rev_total += p['valeur']
            else:
                dep_total += p['valeur']
            cumul_pred.append({
                'date':        p['date'],
                'intitule':    p['intitule'],
                'est_revenu':  p['est_revenu'],
                'valeur':      p['valeur'],
                'probabilite': p['probabilite'],
                'cumul':       running,
                'rev_cumul':   round(rev_total, 2),
                'dep_cumul':   round(dep_total, 2),
                'ecart':       round(rev_total - dep_total, 2),
            })

        return jsonify({
            "predictions":  predictions,
            "cumul_pred":   cumul_pred,
            "solde_actuel": solde_actuel,
            "max_months":   int(all_months),
            "summary": {
                "rev_prevu":  round(rev_total, 2),
                "dep_prevu":  round(dep_total, 2),
                "ecart_prevu": round(rev_total - dep_total, 2),
            }
        })

    return pred_bp


def init_global_blueprint(compta):
    from flask import Blueprint
    global_bp = Blueprint('global', __name__, url_prefix='/api/global')

    @global_bp.route('/cumul', methods=['GET'])
    def get_global_cumul():
        import pandas as pd

        cur = compta.con.cursor()
        # Récupère tous les comptes actifs + leurs transactions
        cur.execute("SELECT id, nom_compte, metadata FROM comptes")
        comptes_rows = cur.fetchall()

        result = []
        for cid, nom, metadata in comptes_rows:
            # Vérifier actif via metadata
            try:
                import ast
                meta = ast.literal_eval(metadata)
                actif = bool(meta[1])
            except Exception:
                actif = True
            if not actif:
                continue

            cur2 = compta.con.cursor()
            cur2.execute(
                "SELECT date, est_revenu, valeur FROM transactions WHERE compte_id=? ORDER BY date ASC",
                (cid,)
            )
            rows = cur2.fetchall()
            if not rows:
                continue

            df = pd.DataFrame(rows, columns=['date', 'est_revenu', 'valeur'])
            df['date'] = pd.to_datetime(df['date'], format='mixed')
            df = df.sort_values('date')
            df['delta'] = df.apply(
                lambda r: r['valeur'] if r['est_revenu'] == 1 else -r['valeur'], axis=1
            )
            df['cumul'] = df['delta'].cumsum()

            series = [
                {"date": d.strftime('%Y-%m-%d'), "cumul": round(float(v), 2)}
                for d, v in zip(df['date'], df['cumul'])
            ]

            result.append({
                "id":     cid,
                "name":   nom,
                "series": series,
                "date_min": series[0]['date'],
                "date_max": series[-1]['date'],
                "cumul_final": series[-1]['cumul'],
            })

        return jsonify(result)

    return global_bp