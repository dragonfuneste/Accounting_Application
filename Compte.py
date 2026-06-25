import ast
import logging

class Compte:
    def __init__(self, account_id, cursor, connection):
        self.id = account_id
        self.cursor = cursor
        self.connection = connection
        self.name = None
        self.devise = "EUR" 
        self.actif = True
        self.load_account()

    def load_account(self):
        self.cursor.execute("SELECT nom_compte, metadata FROM comptes WHERE id = ?", (self.id,))
        result = self.cursor.fetchone()
        if result:
            self.name = result[0]
            try:
                meta_tuple = ast.literal_eval(result[1])
                self.devise = meta_tuple[0]
                self.actif = bool(meta_tuple[1])
            except (ValueError, SyntaxError, IndexError):
                logging.error(f"Erreur de formatage des métadonnées pour le compte {self.id}")
        else:
            logging.info("Aucun compte trouvé pour cet ID")

    def _save_metadata(self):
        """Méthode interne pour synchroniser les changements avec la DB"""
        new_metadata = str((self.devise, int(self.actif)))
        self.cursor.execute(
            "UPDATE comptes SET nom_compte = ?, metadata = ? WHERE id = ?",
            (self.name, new_metadata, self.id)
        )
        self.connection.commit()

    def modify_name(self, name):
        self.name = name
        self._save_metadata()

    def modify_devise(self, devise):
        self.devise = devise
        self._save_metadata()

    def toggle_actif(self):
        self.actif = not self.actif
        self._save_metadata()


    def get_date_range(self):
        """Retourne la première et la dernière date de transaction pour ce compte"""
        self.cursor.execute("""
            SELECT MIN(date), MAX(date) 
            FROM transactions 
            WHERE compte_id = ?
        """, (self.id,))
        result = self.cursor.fetchone()
        return result if result else (None, None)
    

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