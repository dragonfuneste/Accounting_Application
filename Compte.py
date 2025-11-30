from Librairie import *

class Compte:
    """
    Classe représentant un compte comptable géré via un fichier Excel.
    """

    def __init__(self, chemin, etat="ouvert", currency="Euros"):
        self.chemin = chemin
        self.nom = os.path.splitext(os.path.basename(chemin))[0]
        self.total = 0
        self.revenus = 0 
        self.depenses = 0 
        self.etat = etat 
        self.currency = currency
        self.df = pd.read_excel(chemin)

        # Conversion obligatoire de la colonne Date en datetime
        if "Date" not in self.df.columns:
            raise ValueError("Le fichier Excel doit contenir une colonne 'Date'.")

        self.df["Date"] = pd.to_datetime(self.df["Date"], errors="coerce")

        # Calcul auto des dates min/max
        self.date_debut = self.df["Date"].min()
        self.date_fin = self.df["Date"].max()
        self.__recalculer_total()

    # ------------------------------------------------------------
    #        FONCTIONS DE MANIPULATION DU TABLEAU
    # ------------------------------------------------------------

    def ajouter_ligne(self, date, intitule, categorie, classe, type_operation, valeur):
        """Ajoute une ligne au tableau."""
        if (self.etat=='ouvert'):
            nouvelle_ligne = {
                "Date": date,
                "Intitule": intitule,
                "Categorie": categorie,
                "Classe": classe,
                "Type": type_operation,
                "Valeur": valeur
            }
            self.df = pd.concat([self.df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

            # Mise à jour automatique des bornes de dates
            self.date_debut = self.df["Date"].min()
            self.date_fin = self.df["Date"].max()
            self.__recalculer_total()
        else : 
            print("Compte fermé")

    def supprimer_ligne(self, index):
        """Supprime une ligne du tableau via son index."""
        if (self.etat=='ouvert'):
            if index < 0 or index >= len(self.df):
                raise IndexError("Indice hors limite.")
            self.df = self.df.drop(index).reset_index(drop=True)

            # Mise à jour auto dates
            self.date_debut = self.df["Date"].min()
            self.date_fin = self.df["Date"].max()
            self.__recalculer_total()
        else : 
            print("Compte fermé")

    def modifier_ligne(self, index, **champs):
        """
        Modifie une ligne du tableau, par exemple :
        compte.modifier_ligne(2, Intitule="Achat", Valeur=200)
        """
        print(self.etat)
        if (self.etat=='ouvert'):
            if index < 0 or index >= len(self.df):
                raise IndexError("Indice hors limite.")

            for cle, valeur in champs.items():
                if cle not in self.df.columns:
                    raise KeyError(f"Champ '{cle}' inconnu.")
                self.df.at[index, cle] = valeur

            # Mise à jour auto dates
            self.date_debut = self.df["Date"].min()
            self.date_fin = self.df["Date"].max()
            self.__recalculer_total()
        else : 
            print("Compte fermé")

    def trier(self, colonne, decroissant=False):
        """Trie la table selon une colonne."""
        if colonne not in self.df.columns:
            raise KeyError(f"La colonne '{colonne}' n'existe pas.")
        self.df = self.df.sort_values(by=colonne, ascending=not decroissant).reset_index(drop=True)

    # -------------------------------------------------------------------
    # VALEURS UNIQUES
    # -------------------------------------------------------------------

    def valeurs_uniques(self, colonne):
        """Retourne la liste triée des valeurs uniques d'une colonne."""
        if colonne not in self.df.columns:
            raise KeyError(f"La colonne '{colonne}' n'existe pas.")
        return sorted(self.df[colonne].dropna().unique())

    def categories_uniques(self):
        return self.valeurs_uniques("Categorie")

    def classes_uniques(self):
        return self.valeurs_uniques("Classe")

    def types_uniques(self):
        return self.valeurs_uniques("Type")

    # ------------------------------------------------------------
    #        SAUVEGARDE AVEC BACKUP
    # ------------------------------------------------------------

    def sauvegarder(self):
        """
        Sauvegarde les modifications :
          - créer ./backup/ si inexistant
          - copie l'ancien fichier dans backup_backup_nom.xlsx
          - remplace le fichier original par la version modifiée
        """
        # Création du dossier backup si absent
        backup_dir = "./backup"
        os.makedirs(backup_dir, exist_ok=True)

        # Chemin du backup
        backup_path = os.path.join(backup_dir, f"backup_{self.nom}.xlsx")

        # Copie du fichier original en backup
        if os.path.exists(self.chemin):
            with open(self.chemin, "rb") as src, open(backup_path, "wb") as dst:
                dst.write(src.read())

        # Avant d'écrire, trier par Date du plus récent au plus ancien si possible
        try:
            if "Date" in self.df.columns:
                # S'assurer que la colonne Date est en datetime
                self.df["Date"] = pd.to_datetime(self.df["Date"], errors="coerce")
                self.trier("Date", decroissant=True)
        except Exception:
            # Si le tri échoue, continuer quand même à sauvegarder
            pass

        # Écriture du fichier mis à jour
        self.df.to_excel(self.chemin, index=False)

    def __str__(self):
        return (
            f"Compte : {self.nom}\n"
            f"Chemin : {self.chemin}\n"
            f"Lignes : {len(self.df)}\n"
            f"Date début : {self.date_debut}\n"
            f"Date fin : {self.date_fin}\n"
        )
    def __recalculer_total(self):
        self.depenses = round(self.df[self.df["Type"] == "Depense"]["Valeur"].sum(),2)
        self.revenus  = round(self.df[self.df["Type"] == "Revenu"]["Valeur"].sum(),2)

        self.total = round(self.revenus - self.depenses,2)


