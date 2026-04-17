from api.serializer.compte_serial import compte_serial
from core.variables.variable import REVENU, DEPENSE, ECART , COLUMNS_STRUCTURE
from core.services.comptabilite import comptabilite
import datetime
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
        if "Date" in data and data["Date"]:
            date_obj = pd.to_datetime(data["Date"], dayfirst=True, format='mixed')
            data["Date"] = date_obj.strftime('%d/%m/%Y')
                
        self.compte.modify_lines(index, data)

    # ------------------------------------------------------------------------------------- #
    # INTERCOMPTE
    # ------------------------------------------------------------------------------------- #
    # Dans ton serializer (probablement comptabilite_serial.py)
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
        # Sécurité : On transforme le "2026-04-15" du JS en "15/04/2026"
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_fr = date_obj.strftime('%d/%m/%Y')
        except:
            date_fr = date_str # Au cas où c'est déjà du FR

        # On envoie la version FR au core
        self.compta.virement_intercompte(idx_src, idx_dst, date_fr, raison, montant_out, montant_in)


    # ------------------------------------------------------------------------------------- #
    # Statistic
    # ------------------------------------------------------------------------------------- #
    def get_stats_repartition(self, account_idx, days, selected_months=None):
        # On vérifie si l'index est valide via la classe compta
        if not self.compta.check_index(account_idx):
            return None
            
        compte_obj = self.compta.liste_compte[account_idx]
        
        # IMPORTANT : Il faut aussi que la méthode dans compte.py accepte selected_months
        return compte_obj.get_categories_repartition(days, selected_months)