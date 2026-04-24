from api.serializer.compte_serial import compte_serial
from core.variables.variable import REVENU, DEPENSE, ECART , COLUMNS_STRUCTURE
from core.services.comptabilite import comptabilite
import datetime
import plotly.utils
import json
import pandas as pd

class comptabilite_serial():
    def __init__(self, compta : comptabilite):
        """Initialise le sérialiseur avec l'instance de comptabilité."""
        self.compta = compta

    def get_account_information_all(self) -> dict:
        """
        Retourne le JSON pour les statistiques globales du dashboard.
        """
        # Récupération des données brutes depuis le Core
        revenu_global, depense_global, solde_global = self.compta.compute_statistic()
        
        # Formatage en JSON (dictionnaire) avec conversion float pour la compatibilité
        return {
            f"{REVENU}": float(revenu_global),
            f"{DEPENSE}": float(depense_global),
            f"{ECART}": float(solde_global)
        }
    
    def get_account_information(self) -> list:
        """
        Retourne le JSON pour la liste des comptes (Interface de gestion).
        Chaque élément contient les infos de base et les stats du compte.
        """
        resultats = []
        for compte_obj in self.compta.liste_compte: #
            # On utilise le serial unitaire pour chaque compte
            serial_unitaire = compte_serial(compte_obj)
            
            # Récupération des dictionnaires formatés
            info = serial_unitaire.get_global_information()
            stats = serial_unitaire.statistic() 
            
            # Fusion des dictionnaires pour créer un objet JSON complet par compte
            account_json = {**info, **stats}
            resultats.append(account_json)
            
        return resultats

    # ------------------------------------------------------------------------------------- #
    # ACTIONS (Méthodes de modification qui ne renvoient généralement qu'un statut)
    # ------------------------------------------------------------------------------------- #

    def change_state(self, index: int) -> dict:
        """Bascule l'état d'un compte et confirme l'action."""
        self.compta.change_state(index)


    def delete_account(self, index: int) -> dict:
        """Supprime un compte et confirme l'action."""
        self.compta.delete_account(index)

    def create_account(self, name: str, devise: str) -> dict:
        """Crée un nouveau compte via le Core."""
        self.compta.creer_nouveau_compte(name, devise)

    # Remplace ta fonction modify_account par celle-ci
    def modify_line(self, index: int, data: dict):
        # Nettoyage de la valeur avant envoi au core
        if "Valeur" in data:
            val = str(data["Valeur"]).replace(',', '.')
            data["Valeur"] = float(val) if val.strip() else 0.0
                
        self.compte.modify_lines(index, data)

    # ------------------------------------------------------------------------------------- #
    # INTERCOMPTE
    # ------------------------------------------------------------------------------------- #
    def get_intercompte_stats(self, src_idx, dst_idx):
        res, solde, rev, dep = self.compta.cumulatif_intercompte(src_idx, dst_idx)
        
        if res.empty:
            return {"dates": [], "cumul": [], "labels": []}
            
        return {
            "dates": res[COLUMNS_STRUCTURE[0]].tolist(), # Les dates formatées et TRIÉES
            "cumul": res["Cumul"].tolist(),
            "labels": res[COLUMNS_STRUCTURE[1]].tolist(), # Les intitulés des virements
            "solde": solde
        }
    def virement_intercompte(self, idx_src, idx_dst, date_str, raison, montant_out, montant_in):
        """
        Prépare et normalise les données de virement avant l'envoi au Core.
        Assure que la date finit TOUJOURS en DD/MM/YYYY dans l'Excel.
        """
        self.compta.virement_intercompte(
            idx_src, 
            idx_dst, 
            date_str, 
            raison, 
            float(montant_out), 
            float(montant_in)
        )


    # ------------------------------------------------------------------------------------- #
    # Statistic
    # ------------------------------------------------------------------------------------- #
    def get_stats_repartition(self, account_idx, days, selected_months=None):
        if not self.compta.check_index(account_idx):
            return None
            
        compte_obj = self.compta.liste_compte[account_idx]
        return compte_obj.get_categories_repartition(days, selected_months)
    
    def get_sankey_data(self, account_idx, start_date=None, end_date=None):
        if not self.compta.check_index(account_idx):
            return None
            
        compte_obj = self.compta.liste_compte[account_idx]
        
        # On récupère le DataFrame complet
        df = compte_obj.df_actual.copy()
        
        # --- AJOUT DU FILTRE DE DATE ---
        if start_date and end_date:
            # Conversion de la colonne Date en datetime si nécessaire
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))
            df = df.loc[mask]
        # -------------------------------

        df['Valeur'] = df['Valeur'].abs()

        df_rev = df[df['Type'] == 'Revenu']
        df_dep = df[df['Type'] == 'Depense']

        # Flux Entrée -> Portefeuille
        flux_entree = df_rev.groupby('Categorie')['Valeur'].sum().reset_index()
        flux_entree.columns = ['source', 'value']
        flux_entree['target'] = 'PORTEFEUILLE'
        flux_entree['source'] = flux_entree['source'] + " " 

        # Flux Portefeuille -> Sortie
        flux_sortie = df_dep.groupby('Categorie')['Valeur'].sum().reset_index()
        flux_sortie.columns = ['target', 'value']
        flux_sortie['source'] = 'PORTEFEUILLE'

        flux_total = pd.concat([flux_entree, flux_sortie], ignore_index=True)
        nodes = list(pd.unique(flux_total[['source', 'target']].values.ravel('K')))
        mapping = {node: i for i, node in enumerate(nodes)}
        
        # Préparation des couleurs
        node_colors = ["#00adb5" if n == 'PORTEFEUILLE' else ("#2ecc71" if n.endswith(" ") else "#e74c3c") for n in nodes]

        # On retourne le dictionnaire prêt pour Plotly
        return {
            "nodes": [n.strip() for n in nodes],
            "node_colors": node_colors,
            "source": flux_total['source'].map(mapping).tolist(),
            "target": flux_total['target'].map(mapping).tolist(),
            "value": flux_total['value'].tolist(),
            "account_name": compte_obj.account_name
        }