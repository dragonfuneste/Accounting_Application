from Compte import *

class FonctionFiltre:
    """
    Classe permettant de filtrer les données d'un Compte
    sans modifier l'original.

    Elle récupère automatiquement :
      - la date min et max
      - la liste des valeurs uniques pour Categorie, Classe et Type
    dans l'objet Compte fourni.
    """

    def __init__(self, compte):
        # Sauvegarde de la référence au Compte
        self.compte = compte

        # Copie locale du tableau
        self.df = compte.df.copy()

        # Récupération automatique des bornes de dates
        self.date_debut = compte.date_debut
        self.date_fin = compte.date_fin

        # Récupération des valeurs uniques
        self.categories = compte.categories_uniques()
        self.classes = compte.classes_uniques()
        self.types = compte.types_uniques()

    # -------------------------------------------------------------------
    #  FILTRE MULTI-CONDITIONS
    # -------------------------------------------------------------------

    def filtrer(self, **conditions):
        """
        Filtre les données de façon flexible.

        Exemples :
        filtrer(Categorie="Achat")
        filtrer(Categorie=["Achat", "Transport"], Classe="Maison")
        filtrer(Date_debut="2024-01-01", Date_fin="2024-06-01")

        Retourne un DataFrame filtré.
        """

        filtered = self.df.copy()

        # Extraction des filtres de dates
        date_debut = conditions.pop("Date_debut", None)
        date_fin = conditions.pop("Date_fin", None)

        # Application filtre date début
        if date_debut is not None:
            filtered = filtered[filtered["Date"] >= pd.to_datetime(date_debut)]

        # Application filtre date fin
        if date_fin is not None:
            filtered = filtered[filtered["Date"] <= pd.to_datetime(date_fin)]

        # Application des filtres restants (colonnes normales)
        for colonne, valeur in conditions.items():

            if colonne not in filtered.columns:
                raise KeyError(f"La colonne '{colonne}' n'existe pas.")

            if isinstance(valeur, list):      # Multi-choix
                filtered = filtered[filtered[colonne].isin(valeur)]
            else:                             # Valeur unique
                filtered = filtered[filtered[colonne] == valeur]

        return filtered

    # -------------------------------------------------------------------
    #  GETTERS POUR FACILITER L’UTILISATION
    # -------------------------------------------------------------------

    def bornes_dates(self):
        """Retourne (date_min, date_max)."""
        return self.date_debut, self.date_fin

    def valeurs_uniques(self, colonne):
        """Retourne les valeurs uniques d'une colonne."""
        if colonne not in self.df.columns:
            raise KeyError(f"La colonne '{colonne}' n'existe pas.")
        return sorted(self.df[colonne].dropna().unique())

    def get_categories(self):
        return self.categories

    def get_classes(self):
        return self.classes

    def get_types(self):
        return self.types

    def dataframe(self):
        """Retourne la version locale du DataFrame."""
        return self.df.copy()





