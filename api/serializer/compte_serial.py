from core.models.compte import compte
from core.variables.variable import COLUMNS_STRUCTURE,REVENU,DEPENSE,ECART
from datetime import datetime
import pandas as pd
import numpy as np
from core.services.analyser_compte import analyser_compte

class compte_serial():
    def __init__(self,compte : compte):
        self.compte = compte
        pass

    def _serialize_value(self, val):
        """Convertit les types pandas/numpy en types Python natifs pour JSON."""
        if isinstance(val, pd.Timestamp):
            return val.strftime('%Y-%m-%d')
        elif isinstance(val, float) and np.isnan(val):
            return None
        elif isinstance(val, (np.integer,)):
            return int(val)
        elif isinstance(val, (np.floating,)):
            return float(val)
        elif isinstance(val, (np.bool_,)):
            return bool(val)
        return val

    def get_df(self):
        cols = COLUMNS_STRUCTURE
        rows = []
        for _, row in self.compte.df_actual.iterrows():
            # Accès par nom de colonne (plus fiable que par position)
            dico = {col: self._serialize_value(row[col]) for col in cols}
            dico['real_index'] = str(row['real_index'])
            rows.append(dico)
        return rows

    def get_global_information(self):
        return {"name": self.compte.account_name, "devise": self.compte.devise, "status": self.compte.state}

    # ------------------------------------------------------------------------------------- #

    def delete_line(self, index: str):
        self.compte.delete_lines(index)

    def add_line(self, data: dict):
        self.compte.add_lines(data)

    def modify_line(self, index: str, data: dict):
        self.compte.modify_line(index, data)

    # ------------------------------------------------------------------------------------- #
                                # FILTRAGE #
    # ------------------------------------------------------------------------------------- #

    def filtrer(self, column: str, keyword: str):
        self.compte.filtrage(column, keyword)

    def trier(self, column: str, croissant: bool):
        self.compte.triage(column, croissant)

    def trier_date(self, start_date: datetime, end_date: datetime):
        self.compte.Tri_Period(start_date, end_date)

    # ------------------------------------------------------------------------------------- #
                                # UNIQUE CLASSE #
    # ------------------------------------------------------------------------------------- #

    def get_unique_category(self):
        unique_category, _, _ = self.compte.uniques()
        return [category for category in unique_category]

    def get_unique_class(self):
        _, unique_classe, _ = self.compte.uniques()
        return [classe for classe in unique_classe]

    def get_unique_type(self):  # Corrigé : était une 2ème définition de get_unique_category
        _, _, unique_type = self.compte.uniques()
        return [types for types in unique_type]

    # ------------------------------------------------------------------------------------- #
                                # STATISTIC #
    # ------------------------------------------------------------------------------------- #

    def statistic(self):
        total_depense, total_revenu, total_ecart, _ = self.compte.statistic()
        return {f"{REVENU}": total_revenu, f"{DEPENSE}": total_depense, f"{ECART}": total_ecart}

    # ------------------------------------------------------------------------------------- #
                                # Prediction #
    # ------------------------------------------------------------------------------------- #

    def get_predictions_data(self, probabilite: int):
        """Génère et formate les données pour le JSON de la route"""
        analyseur = analyser_compte(self.compte)
        df_preds = analyseur.Generer_prediction()
        return {
            "predictions": analyseur.afficher_predictions(df_preds).to_dict(orient='records'),
            "stress_test": analyseur.simuler_scenario_stress(df_preds, probabilite).to_dict(orient='records'),
            "solde_actuel": analyseur.solde_actuel
        }