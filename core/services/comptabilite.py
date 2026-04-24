from ..models.compte import compte
from ..variables.variable import *
import logging
import datetime
import pandas as pd 


class comptabilite:
    def __init__(self, liste_compte: list[compte]):
        logging.info(f"Initialisation de la classe comptabilite")
        self.liste_compte = liste_compte

    # ------------------------------------------------------------------------------------- #
                                # CLASSIC FUNCTION #
    # ------------------------------------------------------------------------------------- #
    def check_index(self,index:int):
        return ( 0 <= index < len(self.liste_compte))

    def modifier_compte(self, index: int, nouveau_nom: str, nouvelle_devise: str):
        """Met à jour les informations d'un compte spécifique."""
        if 0 <= index < len(self.liste_compte):
            compte = self.liste_compte[index]
            
            # On met à jour les attributs de l'objet Compte
            compte.account_name = nouveau_nom
            compte.devise = nouvelle_devise
            print('success')
            logging.info(f"💾 Core : Compte {index} mis à jour -> {nouveau_nom} ({nouvelle_devise})")
        else:
            raise IndexError("Index de compte hors limites")
        
    def delete_account(self,index):
        if (self.check_index(index)):
            name = self.liste_compte[index].account_name
            self.liste_compte.pop(index)
            logging.info(f"Suppression de {name} réussit dans comptabilite")

    def creer_nouveau_compte(self, nom: str, devise: str):
        """Initialise une nouvelle table de compte."""
        if any(c.account_name == nom for c in self.liste_compte):
            return
        df_vide = pd.DataFrame(columns=COLUMNS_STRUCTURE)
        logging.info(f"Creation de {nom} ")
        nouveau = compte(nom, devise, True, df_vide)
        self.liste_compte.append(nouveau)
    


    def change_state(self, index: int):
        """Bascule l'état d'un compte."""
        if self.check_index(index):
            self.liste_compte[index].state = not self.liste_compte[index].state
            logging.info(f"Creation de {self.liste_compte[index].account_name} changement de l etat {self.liste_compte[index].state} ")
    

   
    def compute_statistic(self):
        revenu_global = 0
        depense_global = 0 
        for compte in self.liste_compte:
            if compte.state:
                total_depense,total_revenu,_,_ =compte.statistic()
                revenu_global += total_revenu
                depense_global += total_depense
        solde_global = revenu_global - depense_global
        return revenu_global,depense_global,solde_global

    def compute_statistic_temporel(self,period='30'):
        name = []
        dict_compte = []
        for compte in self.liste_compte:
            compte.triage("Date",True)
            names, _, ecart_cummule = compte.statistic_temporel(period=period)
            dict_compte.append(ecart_cummule)
            name.append(compte.account_name)
        return name,dict_compte
    
    # ------------------------------------------------------------------------------------- #
                                # INTERCOMPTE ACCOUNT #
    # ------------------------------------------------------------------------------------- #
    def virement_intercompte(self,idx_src : int ,idx_dst : int ,date : datetime,raison: str,montant_out : str,montant_in:int):
        src, dst = self.liste_compte[idx_src], self.liste_compte[idx_dst]
        
        logging.info(f"Exécution d'un virement inter-compte : {src.account_name} -> {dst.account_name} ")
        if src.state and dst.state:
            # Sortie
            src.add_lines({COLUMNS_STRUCTURE[0]: date, COLUMNS_STRUCTURE[1]: f"{raison}", 
                           COLUMNS_STRUCTURE[2]: "Virement", COLUMNS_STRUCTURE[3]: f"{dst.account_name}", COLUMNS_STRUCTURE[4]: DEPENSE, COLUMNS_STRUCTURE[5]: montant_out})
            # Entrée
            dst.add_lines({COLUMNS_STRUCTURE[0]: date, COLUMNS_STRUCTURE[1]: f"{raison}", 
                           COLUMNS_STRUCTURE[2]: "Virement", COLUMNS_STRUCTURE[3]: f"{src.account_name}", COLUMNS_STRUCTURE[4]: REVENU, COLUMNS_STRUCTURE[5]: montant_in})
        
        
    def cumulatif_intercompte(self, idx_src: int, idx_dst: int):
            
            src, dst = self.liste_compte[idx_src], self.liste_compte[idx_dst]
            
            # On filtre les lignes où la destination est mentionnée
            intercompte = src.df[src.df[COLUMNS_STRUCTURE[3]] == dst.account_name].copy()
            
            if intercompte.empty:
                return pd.DataFrame(), 0, 0, 0

            col_date = COLUMNS_STRUCTURE[0]
            
            # 1. Conversion robuste (Format FR vers Objet Date)
            intercompte[col_date] = pd.to_datetime(intercompte[col_date], dayfirst=True, errors='coerce')
            intercompte = intercompte.dropna(subset=[col_date]) 
            
            # 2. Tri chronologique indispensable pour le graphique
            intercompte = intercompte.sort_values(by=col_date)

            # 3. Calculs des totaux
            depenses_total = round(intercompte[intercompte[COLUMNS_STRUCTURE[4]] == DEPENSE][COLUMNS_STRUCTURE[5]].sum(), 2)
            revenus_total = round(intercompte[intercompte[COLUMNS_STRUCTURE[4]] == REVENU][COLUMNS_STRUCTURE[5]].sum(), 2)
            solde = round(revenus_total - depenses_total, 2)

            # 4. Calcul du cumul (Dépense = Sortie de cash)
            valeurs_signees = intercompte.apply(
                lambda row: row[COLUMNS_STRUCTURE[5]] if row[COLUMNS_STRUCTURE[4]] == DEPENSE else -row[COLUMNS_STRUCTURE[5]], 
                axis=1
            )
            intercompte["Cumul"] = round(valeurs_signees.cumsum(), 2)
            
            # 5. Préparation pour le JSON (On convertit l'objet Date en String ISO pour Chart.js)
            resultat = intercompte.copy()
            return resultat, solde, revenus_total, depenses_total