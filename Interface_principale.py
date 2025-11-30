from Fonction import *
from Compte import Compte
from Librairie import *
from Interface_Tableau import Onglet_Tableau, AutocompleteCombobox
from Interface_Compte import Onglet_Comptes
from Interface_Resume import Onglet_Resume
from Onglet_Graphique import Onglet_Graphique
from Interface_Cumule import Onglet_Cumule
from Interface_Virement import Interface_Virement
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import os
from datetime import datetime

class Gestionnaire_Onglets(tk.Tk):
    """Classe principale qui gère la barre supérieure et les onglets."""
    
    def __init__(self):
        super().__init__()
        self.title("Gestion des Comptes")
        self.geometry("800x600")

        # Configurer la fenêtre pour qu'elle soit redimensionnable
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Dictionnaire pour stocker les objets Compte
        self.comptes = {}
        self.info_file = "./csv/info.txt"
        self.csv_dir = "./csv"

        # Créer le répertoire s'il n'existe pas
        os.makedirs(self.csv_dir, exist_ok=True)

        # Charger les comptes depuis info.txt
        self.load_accounts()

        # Dictionnaire pour stocker les onglets
        self.onglets = {}

        # Créer l'interface utilisateur
        self.create_ui()

    def load_accounts(self):
        """Charge les comptes depuis info.txt et crée les objets Compte."""
        if os.path.exists(self.info_file):
            with open(self.info_file, 'r') as file:
                for line in file:
                    name, status, currency = line.strip().split(',')
                    compte = Compte(f"{self.csv_dir}/{name}.xlsx", status, currency)
                    compte.creation_date = self.get_creation_date(f"{self.csv_dir}/{name}.xlsx")
                    self.comptes[name] = compte
        else:
            with open(self.info_file, 'w') as file:
                pass  # Créer un fichier vide

    def get_creation_date(self, file_path):
        """Récupère la date de création d'un fichier."""
        if os.path.exists(file_path):
            return datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d')
        return None

    def save_accounts(self):
        """Sauvegarde les comptes dans info.txt."""
        with open(self.info_file, 'w') as file:
            for name, compte in self.comptes.items():
                file.write(f"{name},{compte.status},{compte.currency}\n")

    def create_ui(self):
        """Crée l'interface utilisateur."""
        # Frame pour les éléments en haut (barre de sélection du compte - globale)
        top_frame = tk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Combobox pour sélectionner un compte (autocomplete, suggestions only)
        self.combo_var = tk.StringVar()
        self.combo = AutocompleteCombobox(top_frame, textvariable=self.combo_var,
                          values=list(self.comptes.keys()), width=30)
        # Do not enforce selection — user can type any text; suggestions are shown.
        self.combo.pack(side=tk.LEFT, padx=5)

        # Bouton pour rafraîchir
        refresh_button = tk.Button(top_frame, text="Rafraîchir", command=self.refresh_all)
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Notebook (conteneur d'onglets)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Créer les onglets
        self.create_tabs()

    def create_tabs(self):
        """Crée les onglets de l'application."""
        # Onglet Comptes
        self.onglet_comptes = Onglet_Comptes(self.notebook, self.comptes, self.info_file, self.csv_dir)
        self.notebook.add(self.onglet_comptes, text="Comptes")
        self.onglets['comptes'] = self.onglet_comptes
        
        # Onglet Tableau
        self.onglet_tableau = Onglet_Tableau(self.notebook, self.comptes, self.combo_var)
        self.notebook.add(self.onglet_tableau, text="Tableau")
        self.onglets['tableau'] = self.onglet_tableau

        # Onglet Résumé
        try:
            self.onglet_resume = Onglet_Resume(self.notebook, self.comptes, self.combo_var)
            self.notebook.add(self.onglet_resume, text="Résumé")
            self.onglets['resume'] = self.onglet_resume
        except Exception:
            # Si l'import ou l'initialisation échoue, ne pas bloquer l'interface
            pass

        # Onglet Graphique
        try:
            self.onglet_graphique = Onglet_Graphique(self.notebook, self.comptes, self.combo_var)
            self.notebook.add(self.onglet_graphique, text="Graphique")
            self.onglets['graphique'] = self.onglet_graphique
        except Exception as e:
            # Si l'import ou l'initialisation échoue, ne pas bloquer l'interface
            print(f"Erreur lors du chargement de l'onglet Graphique: {e}")

        # Onglet Cumulé
        try:
            self.onglet_cumule = Onglet_Cumule(self.notebook, self.comptes)
            self.notebook.add(self.onglet_cumule, text="Cumulé")
            self.onglets['cumule'] = self.onglet_cumule
        except Exception as e:
            # Si l'import ou l'initialisation échoue, ne pas bloquer l'interface
            print(f"Erreur lors du chargement de l'onglet Cumulé: {e}")

        # Onglet Virement
        try:
            self.onglet_virement = Interface_Virement(self.notebook, self.comptes)
            self.notebook.add(self.onglet_virement, text="Virement")
            self.onglets['virement'] = self.onglet_virement
        except Exception as e:
            # Si l'import ou l'initialisation échoue, ne pas bloquer l'interface
            print(f"Erreur lors du chargement de l'onglet Virement: {e}")

    def refresh_all(self):
        """Rafraîchit tous les onglets et relit les fichiers Excel."""
        # Recharger les données depuis les fichiers Excel pour chaque compte existant
        for name, compte in self.comptes.items():
            compte.df = pd.read_excel(compte.chemin)
            compte.df["Date"] = pd.to_datetime(compte.df["Date"], errors="coerce")
            compte.date_debut = compte.df["Date"].min()
            compte.date_fin = compte.df["Date"].max()
            compte._Compte__recalculer_total()
        
        # Rafraîchir chaque onglet
        for onglet in self.onglets.values():
            onglet.refresh()





# Exemple d'utilisation
if __name__ == "__main__":
    app = Gestionnaire_Onglets()
    app.mainloop()
