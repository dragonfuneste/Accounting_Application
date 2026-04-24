from core.models.compte import compte
from core.variables.variable import COLUMNS_STRUCTURE,REVENU,DEPENSE,ECART
from datetime import datetime
import pandas as pd
from core.services.analyser_compte import analyser_compte
class compte_serial():
    def __init__(self,compte : compte):
        self.compte =compte
        pass

    def get_df(self):
            cols = COLUMNS_STRUCTURE 
            rows = []
            # On utilise to_dict('records') c'est plus rapide, 
            # mais on doit s'assurer que real_index est bien dedans
            for _, row in self.compte.df_actual.iterrows():
                dico = {cols[i]: row[i] for i in range(len(cols))}
                # ICI : On ajoute l'ID unique qui est dans la colonne 'real_index' du DataFrame
                dico['real_index'] = str(row['real_index']) 
                rows.append(dico)
            
            return rows
        

    def get_global_information(self):
        return {"name": self.compte.account_name , "devise": self.compte.devise, "status": self.compte.state}
    

    # ------------------------------------------------------------------------------------- #
    
    def delete_line(self,index: str):
        self.compte.delete_lines(index) 
    
    def add_line(self, data: dict):
        self.compte.add_lines(data)

    def modify_line(self, index: str, data: dict):
        self.compte.modify_line(index, data)
        
    # ------------------------------------------------------------------------------------- #
                                # FILTRAGE #
    # ------------------------------------------------------------------------------------- #

    def filtrer(self, column: str, keyword: str):
        self.compte.filtrage(column,keyword)

    def trier(self,column: str, croissant: bool):
        self.compte.triage(column,croissant) 
    
    def trier_date(self,start_date: datetime, end_date: datetime):
        self.compte.Tri_Period(start_date,end_date)

    # ------------------------------------------------------------------------------------- #
                                # UNIQUE CLASSE #
    # ------------------------------------------------------------------------------------- #
    def get_unique_category(self):
        unique_category,_,_ = self.compte.uniques()
        return [{category} for category in unique_category]
    
    def get_unique_class(self):
        _,unique_classe,_ = self.compte.uniques()
        return [{classe} for classe in unique_classe]
    
    def get_unique_category(self):
        _,_,unique_type = self.compte.uniques()
        return [{types} for types in unique_type]
    # ------------------------------------------------------------------------------------- #
                                # STATISTIC #
    # ------------------------------------------------------------------------------------- #

    def statistic(self):
        total_depense,total_revenu,total_ecart,_ = self.compte.statistic()
        return {f"{REVENU}": total_revenu,f"{DEPENSE}": total_depense,f"{ECART}": total_ecart}
    # ------------------------------------------------------------------------------------- #
                                # Prediction #
    # ------------------------------------------------------------------------------------- #
    def get_predictions_data(self,probabilite : int):
        """Génère et formate les données pour le JSON de la route"""
        # Initialisation de l'analyseur
        analyseur = analyser_compte(self.compte)
        
        # Génération des données
        df_preds = analyseur.Generer_prediction()
        
        # Formatage pour le Web (JSON)
        return {
            "predictions": analyseur.afficher_predictions(df_preds).to_dict(orient='records'),
            "stress_test": analyseur.simuler_scenario_stress(df_preds,probabilite).to_dict(orient='records'),
            "solde_actuel": analyseur.solde_actuel
        }