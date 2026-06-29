import ast
import logging
import pandas as pd 
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
    

    def get_account_stats(self):
            """Calcule revenus, dépenses et solde cumulés"""
            query = """
                SELECT 
                    date,
                    SUM(CASE WHEN est_revenu = 0 THEN valeur ELSE 0 END) OVER (ORDER BY date ASC) as depense_cumule,
                    SUM(CASE WHEN est_revenu = 1 THEN valeur ELSE 0 END) OVER (ORDER BY date ASC) as revenu_cumule,
                    SUM(CASE WHEN est_revenu = 1 THEN valeur ELSE -valeur END) OVER (ORDER BY date ASC) as solde_cumule
                FROM transactions 
                WHERE compte_id = ?
                ORDER BY date ASC
            """

            self.cursor.execute(query, (self.id,))
            res = self.cursor.fetchall()

            df = pd.DataFrame(res, columns=['date', 'depense_cumule', 'revenu_cumule', 'solde_cumule'])
            df['date'] = pd.to_datetime(df['date'], format='mixed')
            return df
    

    def add_transaction(self,date , intitule : str, categorie :str,classe :str,est_revenu : bool , valeur : int ):
        query = """
        INSERT INTO transactions 
            (compte_id, date, intitule, categorie, classe, est_revenu, valeur) 
        VALUES 
            (?,?,?,?,?,?,?);
        """
        self.cursor.execute(query, (self.id,date,intitule,categorie,classe,est_revenu,valeur))


    def filter(self, date_debut=None, date_fin=None, categorie=None, classe=None, est_revenu=None):
        query = """
            SELECT * FROM transactions
            WHERE compte_id = ?
            AND ( ? IS NULL OR date >= ? )
            AND ( ? IS NULL OR date <= ? )
            AND ( ? IS NULL OR categorie = ? )
            AND ( ? IS NULL OR classe = ? )
            AND ( ? IS NULL OR est_revenu = ? )
        """
        params = (
            self.id,
            date_debut, date_debut,
            date_fin, date_fin,
            categorie, categorie,
            classe, classe,
            est_revenu, est_revenu
        )

        # Exécution
        self.cursor.execute(query, params)
        resultats = self.cursor.fetchall()
        return resultats
    def delete_transaction():
        pass

    def modify_transaction():
        pass