import sqlite3
from Compte import Compte
import logging 
import pandas as pd
class Comptabilite: 
    def __init__(self, name):
        # On ajoute check_same_thread=False
        self.con = sqlite3.connect(name, check_same_thread=False)
        self.cursor = self.con.cursor()
        # Activation des clés étrangères pour garantir l'intégrité
        self.cursor.execute("PRAGMA foreign_keys = ON")

    def get_compte(self, account_id):
        """Retourne une instance de la classe Compte pour un ID donné"""
        logging.info("Get le compte")
        self.cursor.execute("SELECT id FROM comptes WHERE id = ?", (account_id,))
        if self.cursor.fetchone():
            return Compte(account_id, self.cursor, self.con)
        logging.error("Le compte n'existe pas")
        return None

    def list_all_accounts(self):
        """Retourne une liste de tous les comptes présents en base"""
        logging.info("Liste tout les compte disponible")
        self.cursor.execute("SELECT id FROM comptes")
        ids = self.cursor.fetchall()
        return [Compte(i[0], self.cursor, self.con) for i in ids]

    def close(self):
        """Ferme la connexion proprement"""
        self.con.close()


    def get_stats(self):
            """Calcule revenus, dépenses et solde cumulés"""
            query = """
                SELECT 
                    date,
                    SUM(CASE WHEN est_revenu = 0 THEN valeur ELSE 0 END) OVER (ORDER BY date ASC) as depense_cumule,
                    SUM(CASE WHEN est_revenu = 1 THEN valeur ELSE 0 END) OVER (ORDER BY date ASC) as revenu_cumule,
                    SUM(CASE WHEN est_revenu = 1 THEN valeur ELSE -valeur END) OVER (ORDER BY date ASC) as solde_cumule
                FROM transactions
                ORDER BY date ASC
            """

            self.cursor.execute(query)
            res = self.cursor.fetchall()

            df = pd.DataFrame(res, columns=['date', 'depense_cumule', 'revenu_cumule', 'solde_cumule'])
            df['date'] = pd.to_datetime(df['date'], format='mixed')
            return df
    
    def get_intercompte_stats(self,src :int,  dest: int):
        query = """
            SELECT 
                t.date,
                SUM(CASE WHEN t.est_revenu = 0 THEN t.valeur ELSE 0 END) OVER (ORDER BY t.date ASC) as depense_cumule,
                SUM(CASE WHEN t.est_revenu = 1 THEN t.valeur ELSE 0 END) OVER (ORDER BY t.date ASC) as revenu_cumule,
                SUM(CASE WHEN t.est_revenu = 1 THEN t.valeur ELSE -t.valeur END) OVER (ORDER BY t.date ASC) as solde_cumule
            FROM transactions t
            WHERE t.compte_id = ?
            AND t.classe = (SELECT nom_compte FROM comptes WHERE id = ?)
            ORDER BY t.date ASC
        """
        self.cursor.execute(query, (src, dest))
        res = self.cursor.fetchall()
        print(res)
        
        df = pd.DataFrame(res, columns=['date', 'depense_cumule', 'revenu_cumule', 'solde_cumule'])
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        return df

    def set_intercompte_transfert(self,src:int,dest:int, date , commentaire : str, valeur_src : int , valeur_dest : int):
        logging.info("Ajout d'un transaction entre les deux compte")
        account_src = self.get_compte(src)
        account_dest = self.get_compte(dest)

        account_src.add_transaction(date,commentaire,str(dest),"Virement",False,valeur_src)
        account_dest.add_transaction(date,commentaire,str(src),"Virement",True,valeur_dest)
        logging.info("Virmeent intercompte validé")