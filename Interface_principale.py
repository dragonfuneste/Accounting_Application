# -*- coding: utf-8 -*-
"""
Created on Fri May 30 12:06:08 2025

@author: loube
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkcalendar import DateEntry
from datetime import datetime
from Onglet_Resumee import OngletResumer
from Onglet_Virement import OngletVirement
from Onglet_Tableau import OngletTableau
from Onglet_Graphique import OngletGraphique
class Test(tk.Tk):
    def __init__(self, liste_compte):
        super().__init__()
        self.selected_account = 0
        
        self.liste_compte = liste_compte
        self.dataframes = {}  # Dictionnaire pour stocker tous les DataFrames
        self.current_account = None
        
        # Charger tous les DataFrames au démarrage
        self.load_all_data()
        
        self.title("Application Budget V2")
        self.geometry("1400x700")
        
        
        
        self.start_date =datetime(2025, 2, 9)
        self.end_date = datetime.today().date()
        self.start_date_old = self.start_date
        self.end_date_old = self.end_date
        
         
        self.Interface_init()

    def load_all_data(self):
        """Charge tous les fichiers Excel dans un dictionnaire"""
        for compte in self.liste_compte:
            try:
                df = pd.read_excel(compte)
                df.columns = df.columns.str.strip()
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                self.dataframes[compte] = df
            except Exception as e:
                print(f"Erreur lors du chargement de {compte}: {str(e)}")
        
        # Définir le premier compte comme courant par défaut
        if self.liste_compte:
            self.current_account = self.liste_compte[0]
            self.df = self.dataframes[self.current_account].copy()
            self.df_original = self.dataframes[self.current_account].copy()
        
    
    def Interface_init(self):
        """Création de l'interface avec la sélection du compte et les onglets"""
        frame_select = ttk.Frame(self)
        frame_select.pack(fill="x", padx=10, pady=5)

        label_compte = ttk.Label(frame_select, text="Sélectionnez un compte :")
        label_compte.pack(side="left")

        self.combo_compte = ttk.Combobox(frame_select, values=self.liste_compte, state="readonly")
        self.combo_compte.current(0)
        self.combo_compte.pack(side="left", padx=10)
        self.combo_compte.bind("<<ComboboxSelected>>")

        btn_update = ttk.Button(frame_select, text="Ouvrir", command=self.Choix_Compte)
        btn_update.pack(side="left", padx=10)

        # Créer le notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Ajouter les onglets
        self.page_resumer = OngletResumer(self.notebook, self)
        self.page_tableau = OngletTableau(self.notebook, self)
        self.page_virement = OngletVirement(self.notebook, self)
        self.page_Graphique = OngletGraphique(self.notebook, self)  
        
        
        self.notebook.add(self.page_resumer, text="Résumé")
        self.notebook.add(self.page_virement, text="Virement")
        self.notebook.add(self.page_tableau, text="Tableau")
        self.notebook.add(self.page_Graphique, text="Graphique")
        
        self.Update()

    def Choix_Compte(self):
        """Callback quand un compte est sélectionné dans la ComboBox"""
        self.selected_account = self.combo_compte.get()
        if self.selected_account in self.dataframes:
            self.current_account = self.selected_account
            self.df = self.dataframes[self.selected_account].copy()
            self.df_original = self.dataframes[self.selected_account].copy()
            self.Update()

    def Update(self) :
        self.Update_Filtrage()
        self.page_resumer.update_data_Date()
        self.page_tableau.update_tableau()
        

    def Update_Filtrage(self) : 
        self.start_date = self.page_resumer.start_date.get_date()
        self.end_date = self.page_resumer.end_date.get_date()

        self.df = self.df_original[
            (self.df_original['Date'] >= self.start_date) & (self.df_original['Date'] <= self.end_date)
        ]
        self.start_date_old = self.start_date
        self.end_date_old = self.end_date
        
# Liste des comptes disponibles
liste_compte = ["Compte_Courant.xlsx", "Livret_Bleu.xlsx", "Compte_Jeune.xlsx"]

# Lancement de l'application
app = Test(liste_compte)
app.mainloop()