import sqlite3
from Compte import Compte

class Comptabilite: 
    def __init__(self, name):
        # On ajoute check_same_thread=False
        self.con = sqlite3.connect(name, check_same_thread=False)
        self.cursor = self.con.cursor()
        # Activation des clés étrangères pour garantir l'intégrité
        self.cursor.execute("PRAGMA foreign_keys = ON")

    def get_compte(self, account_id):
        """Retourne une instance de la classe Compte pour un ID donné"""
        # On vérifie d'abord si le compte existe
        self.cursor.execute("SELECT id FROM comptes WHERE id = ?", (account_id,))
        if self.cursor.fetchone():
            return Compte(account_id, self.cursor, self.con)
        return None

    def list_all_accounts(self):
        """Retourne une liste de tous les comptes présents en base"""
        self.cursor.execute("SELECT id FROM comptes")
        ids = self.cursor.fetchall()
        return [Compte(i[0], self.cursor, self.con) for i in ids]

    def close(self):
        """Ferme la connexion proprement"""
        self.con.close()


    def get_stats(self):
        """Calcule revenus, dépenses et solde"""
        query = """
            SELECT 
                SUM(CASE WHEN est_revenu = 1 THEN valeur ELSE 0 END) as revenus,
                SUM(CASE WHEN est_revenu = 0 THEN valeur ELSE 0 END) as depenses
            FROM transactions 
            WHERE compte_id = ?
        """
        self.cursor.execute(query, (self.id,))
        res = self.cursor.fetchone()
        
        return {
            "revenus": res[0] or 0,
            "depenses": res[1] or 0, 
            "solde": res[0] - res[1] or 0
        }