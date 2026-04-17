import logging
import pandas as pd
from ..models.compte import compte
from ..services.comptabilite import comptabilite

def load_comptabilite(db):
    """Reconstruit les objets Compte à partir des tables SQLite."""
    liste_comptes = []

    # Charger métadonnées
    try:
        df_meta = db.read_table("_metadata_accounts")
        meta_dict = df_meta.set_index("account_name").to_dict("index")
    except Exception:
        logging.warning("Aucune métadonnée trouvée.")
        meta_dict = {}

    # Parcourir toutes les tables
    for table in db.list_tables():
        if table.startswith("_"):
            continue

        try:
            df = db.read_table(table)
            info = meta_dict.get(table, {"devise": "EUR", "state": 1})
            comptes = compte(table, info["devise"], bool(info["state"]), df)
            liste_comptes.append(comptes)
        except Exception as e:
            logging.error(f"Erreur lecture table {table}: {e}")

    return comptabilite(liste_comptes)
