from ..variables.variable import COLUMNS_STRUCTURE, DEPENSE,REVENU

import logging
import pandas as pd
from datetime import datetime

class compte:
    def __init__(self, account_name: str, devise: str, state: bool, df: pd.DataFrame):
        logging.info(f"Compte {account_name}, devise : {devise} / etat : {state}")
        self.account_name = account_name
        self.devise = devise
        self.state = state
        self.df = df
        self.df_actual = df.copy()
        self.uniques()
        
    def actualize_df(self):
        """Réinitialise la vue actuelle sur la source de vérité et met à jour les index."""
        self.df_actual = self.df.copy()
        self.uniques()
        logging.info(f"DF Actualisé pour le compte {self.account_name}")

    def add_lines(self, champs: dict):
        """Ajoute une ligne et synchronise la vue."""
        if self.state:
            # On récupère le nom de la colonne montant/valeur
            col_val = COLUMNS_STRUCTURE[5] 
            
            if col_val in champs:
                valeur_brute = champs[col_val]
                # SÉCURITÉ : On ne convertit que si ce n'est pas vide
                if valeur_brute != "" and valeur_brute is not None:
                    try:
                        champs[col_val] = abs(float(valeur_brute))
                    except ValueError:
                        champs[col_val] = 0.0
                else:
                    champs[col_val] = 0.0 # Valeur par défaut pour l'ajout initial
                
            new_row = pd.DataFrame([champs])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.actualize_df()
            logging.info(f"Ligne ajoutée dans {self.account_name}, champs : {champs}")

    def delete_lines(self, index: int):
        """Supprime une ligne par son index système."""
        if self.state and index in self.df.index:
            self.df = self.df.drop(index).reset_index(drop=True)
            self.actualize_df()
            logging.info(f"Ligne {index} supprimée de {self.account_name},  champs :  {index}")

    def modify_line(self, index: int, nouveaux_champs: dict):
        """Modifie les données d'une ligne spécifique."""
        logging.info(f"Ligne {index} modifie")
        if self.state and index in self.df.index:
            col_val = COLUMNS_STRUCTURE[5]
            for key, value in nouveaux_champs.items():
                if key == col_val:
                    value = abs(float(value))
                self.df.at[index, key] = value
            self.actualize_df()


    def triage(self, column, croissant):
        if column is None:
            # État "Initial" : on réinitialise la vue
            self.actualize_df()
        if column == "Date":
                # Utiliser format='mixed' ici aussi pour éviter les erreurs
                self.df_actual[column] = pd.to_datetime(self.df_actual[column], dayfirst=True, format='mixed')
                self.df_actual = self.df_actual.sort_values(by=column, ascending=croissant)
                self.df_actual[column] = self.df_actual[column].dt.strftime('%d/%m/%Y')
        else:
            self.df_actual = self.df_actual.sort_values(by=column, ascending=croissant)
    # Dans compte.py
    def filtrage(self, column: str, keyword: str):
        if column in COLUMNS_STRUCTURE:
            if not keyword or keyword.strip() == "":
                self.df_actual = self.df.copy() # On réinitialise si le mot-clé est vide
            else:
                # Filtrage insensible à la casse
                self.df_actual = self.df[self.df[column].astype(str).str.contains(keyword, case=False, na=False)]

    def Tri_Period(self, start_date: datetime, end_date: datetime):
        """Filtre la vue sur une plage de dates."""
        col_date = COLUMNS_STRUCTURE[0]
        temp_date = pd.to_datetime(self.df[col_date])
        mask = (temp_date >= start_date) & (temp_date <= end_date)
        self.df_actual = self.df.loc[mask]

    def uniques(self):
        """Extrait les listes uniques depuis df_actual (pour l'UI)."""
        col_category = COLUMNS_STRUCTURE[2]
        col_classe = COLUMNS_STRUCTURE[3]
        col_type = COLUMNS_STRUCTURE[4]
        if not self.df_actual.empty:
            unique_category = self.df_actual[col_category].unique().tolist()
            unique_classe = self.df_actual[col_classe].unique().tolist()
            unique_type = self.df_actual[col_type].unique().tolist()
        else:
            unique_category,unique_classe,unique_type = [],[],[]
        return unique_category,unique_classe,unique_type

    def statistic(self):
        """Calcule les stats (Dépenses et Revenus positifs)."""
        if self.df_actual.empty:
            return 0,0,0, []

        col_type = COLUMNS_STRUCTURE[4]
        col_val = COLUMNS_STRUCTURE[5]
        col_category = COLUMNS_STRUCTURE[2]
        
        # Totaux globaux
        total_depense = self.df_actual[self.df_actual[col_type] == DEPENSE][col_val].sum()
        total_revenu = self.df_actual[self.df_actual[col_type] == REVENU][col_val].sum()
        total_ecart = total_revenu - total_depense

        # Groupement par catégorie et type (déplié pour calcul d'écart)
        stats = self.df_actual.groupby([col_category, col_type])[col_val].sum().unstack(fill_value=0)
        
        # Calcul de l'écart par ligne de catégorie si les colonnes existent
        if REVENU in stats.columns and DEPENSE in stats.columns:
            stats["Ecart"] = stats[REVENU] - stats[DEPENSE]
        return total_depense,total_revenu,total_ecart,stats
    
    def statistic_temporel(self, period='all'):
        if self.df_actual.empty:
            return pd.Series(), pd.Series(), pd.Series()

        col_date = COLUMNS_STRUCTURE[0]
        col_type = COLUMNS_STRUCTURE[4]
        col_val = COLUMNS_STRUCTURE[5]

        # Travailler sur une copie propre
        df_temp = self.df_actual.copy()

        # FORCE la conversion et gère les erreurs en les transformant en NaT (Not a Time)
        df_temp[col_date] = pd.to_datetime(df_temp[col_date], dayfirst=True, errors='coerce')
        
        # Supprime les lignes où la date est invalide (sécurité)
        df_temp = df_temp.dropna(subset=[col_date])

        # 1. TRIER d'abord le DataFrame brut
        df_temp = df_temp.sort_values(by=col_date)

        # 2. Calculer les flux
        df_temp[REVENU] = df_temp.apply(lambda x: x[col_val] if x[col_type] == REVENU else 0, axis=1)
        df_temp[DEPENSE] = df_temp.apply(lambda x: x[col_val] if x[col_type] == DEPENSE else 0, axis=1)

        # 3. Grouper par date. Pandas garde l'ordre si on ne précise rien, 
        # mais on force avec sort=True
        df_grouped = df_temp.groupby(col_date, sort=True)[[REVENU, DEPENSE]].sum()

        # 4. Cumuler (le cumul suit maintenant l'ordre chronologique parfait)
        df_cumulative = df_grouped.cumsum()

        # 5. Filtrage de la période
        if period != 'all':
            try:
                nb_jours = int(period)
                date_limite = pd.Timestamp.now() - pd.Timedelta(days=nb_jours)
                df_cumulative = df_cumulative[df_cumulative.index >= date_limite]
            except:
                pass

        return df_cumulative[REVENU], df_cumulative[DEPENSE], (df_cumulative[REVENU] - df_cumulative[DEPENSE])
    
    def get_categories_repartition(self, start_date=None, end_date=None):
        df_temp = self.df_actual.copy()
        col_date = COLUMNS_STRUCTURE[0]
        col_type = COLUMNS_STRUCTURE[4]
        col_val = COLUMNS_STRUCTURE[5]

        df_temp[col_date] = pd.to_datetime(df_temp[col_date], dayfirst=True, errors='coerce')
        df_temp = df_temp.dropna(subset=[col_date])
        
        # Filtrage par plage précise
        if start_date:
            df_temp = df_temp[df_temp[col_date] >= pd.to_datetime(start_date)]
        if end_date:
            df_temp = df_temp[df_temp[col_date] <= pd.to_datetime(end_date)]

        df_rev = df_temp[df_temp[col_type] == REVENU]
        df_dep = df_temp[df_temp[col_type] == DEPENSE]

        stats_rev = df_rev.groupby("Categorie")[col_val].sum().round(2).to_dict()
        stats_dep = df_dep.groupby("Categorie")[col_val].sum().round(2).to_dict()

        return {
            "revenus": stats_rev,
            "depenses": stats_dep,
            "total_revenu": round(sum(stats_rev.values()), 2),
            "total_depense": round(sum(stats_dep.values()), 2)
        }

    def classe_temporel(self,classe,period,collums):
        col_date = COLUMNS_STRUCTURE[0]
        col_type = COLUMNS_STRUCTURE[4]
        col_val = COLUMNS_STRUCTURE[5]
        df_temp = self.df_actual[self.df_actual[collums] == classe].copy()

        df_temp[col_date] = pd.to_datetime(df_temp[col_date], dayfirst=True, errors='coerce')       
        df_temp = df_temp.dropna(subset=[col_date])
        df_temp = df_temp.sort_values(by=col_date)

        df_temp[REVENU] = df_temp.apply(lambda x: x[col_val] if x[col_type] == REVENU else 0, axis=1)
        df_temp[DEPENSE] = df_temp.apply(lambda x: x[col_val] if x[col_type] == DEPENSE else 0, axis=1)

        df_grouped = df_temp.groupby(col_date, sort=True)[[REVENU, DEPENSE]].sum()
        df_cumulative = df_grouped.cumsum()

        if period != 'all':
            try:
                nb_jours = int(period)
                date_limite = pd.Timestamp.now() - pd.Timedelta(days=nb_jours)
                df_cumulative = df_cumulative[df_cumulative.index >= date_limite]
            except:
                pass
        return df_cumulative[REVENU], df_cumulative[DEPENSE], (df_cumulative[REVENU] - df_cumulative[DEPENSE])