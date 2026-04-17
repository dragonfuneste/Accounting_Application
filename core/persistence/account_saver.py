import logging
import pandas as pd

def save_comptabilite(db, comptabilite):
    """Sauvegarde tous les comptes dans la DB."""
    conn_tables = set(db.list_tables())
    comptes_actuels = {c.account_name for c in comptabilite.liste_compte}

    # Supprimer les tables orphelines
    for table in conn_tables - comptes_actuels:
        if not table.startswith("_"):
            db.drop_table(table)

    # Sauvegarder les comptes
    meta_data = []
    for compte in comptabilite.liste_compte:
        df = compte.df.copy()
        if "Date" in df.columns:
            df["Date"] = df["Date"].astype(str)

        db.write_table(compte.account_name, df)

        meta_data.append({
            "account_name": compte.account_name,
            "devise": compte.devise,
            "state": int(compte.state)
        })

    # Sauvegarder métadonnées
    meta_df = pd.DataFrame(meta_data)
    db.write_table("_metadata_accounts", meta_df)
