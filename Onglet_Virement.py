# -*- coding: utf-8 -*-
"""
Created on Fri May 30 12:20:43 2025

@author: loube
"""
""" 
        Onglet ou l'on gere les virement intercompte. On choisit un compte qui envoie l'argent 
        et un autre compte parmis la liste des compte proposé qui le recoit.
        On entre une somme à envoyer dans le champs associé. Et cela ajoute lorsque l'on clique sur ajouter virement
        une dépense pour le compte créditeur et un revenu pour le débiteur de la somme noté associé. Le champs de la
        Catégorie seras Banque et celui de la Classe sera l'autre compte associé à cette transaction
        
        Cette onglet affiche aussi combien d'argent à été envoyé/recu entre les deux compte séléctionné
        
        Il affiche également les variation sur un graphique cumulé des échange entre ses deux comptes de la date de départ 
        à la date de fin
"""
        
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OngletVirement(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        
        self.nom_affiche_vers_fichier = {
            nom.replace(".xlsx", ""): nom for nom in self.app.liste_compte
        }
        self.liste_affiche = list(self.nom_affiche_vers_fichier.keys())
        self.build_interface()

    def build_interface(self):
        frame_top = ttk.Frame(self)
        frame_top.pack(pady=10)

        # Sélection des comptes
        ttk.Label(frame_top, text="Compte source :").grid(row=0, column=0, padx=5)
        self.combo_source = ttk.Combobox(frame_top, values=self.liste_affiche, state="readonly")
        self.combo_source.current(0)
        self.combo_source.grid(row=0, column=1, padx=5)

        ttk.Label(frame_top, text="Compte destination :").grid(row=0, column=2, padx=5)

        self.combo_dest = ttk.Combobox(frame_top, values=self.liste_affiche, state="readonly")
        self.combo_dest.current(1 if len(self.liste_affiche) > 1 else 0)
        self.combo_dest.grid(row=0, column=3, padx=5)


        self.combo_source.bind("<<ComboboxSelected>>", lambda event: self.update_affichage())
        self.combo_dest.bind("<<ComboboxSelected>>", lambda event: self.update_affichage())

        # Montant
        ttk.Label(frame_top, text="Montant :").grid(row=0, column=4, padx=5)
        self.entry_montant = ttk.Entry(frame_top, width=10)
        self.entry_montant.grid(row=0, column=5, padx=5)

        # Date du virement
        ttk.Label(frame_top, text="Date :").grid(row=0, column=6, padx=5)
        self.date_virement = DateEntry(frame_top, width=12)
        self.date_virement.set_date(datetime.today())
        self.date_virement.grid(row=0, column=7, padx=5)

        # Bouton d'ajout
        btn = ttk.Button(frame_top, text="Ajouter virement", command=self.ajouter_virement)
        btn.grid(row=0, column=8, padx=10)

        # Résumé virement
        self.label_resume = ttk.Label(self, text="")
        self.label_resume.pack(pady=10)

        # Graphique
        self.frame_graph = ttk.Frame(self)
        self.frame_graph.pack(fill="both", expand=True)

        self.app.load_all_data()
        self.app.Choix_Compte()
        self.update_affichage()
        


    def ajouter_virement(self):
        try:
            montant = float(self.entry_montant.get())
        except ValueError:
            self.label_resume.config(text="Erreur : montant invalide")
            return

        source = self.combo_source.get()
        dest = self.combo_dest.get()

        if source == dest:
            self.label_resume.config(text="Erreur : les comptes doivent être différents")
            return

        date = self.date_virement.get_date()

        # Crée les lignes à ajouter
        ligne_depense = {
            "Date": date,
            "Intitule" : "Virement",
            "Categorie": "Banque",
            "Classe": dest,
            "Type": "Depense",
            "Valeur": montant
        }

        ligne_revenu = {
            "Date": date,
            "Intitule" : "Virement",
            "Categorie": "Banque",
            "Classe": dest,
            "Type": "Revenu",
            "Valeur": montant
        }



                
                
        # Ajoute dans les fichiers Excel
        for compte, ligne in zip([source+".xlsx", dest+".xlsx"], [ligne_depense, ligne_revenu]):
            df = pd.read_excel(compte)
            df = pd.concat([pd.DataFrame([ligne]),df], ignore_index=True)
            df.to_excel(compte, index=False)

        self.label_resume.config(text=f"Virement de {montant} € de {source} vers {dest} ajouté.")
        
        self.app.load_all_data()
        self.app.Choix_Compte()
        self.update_affichage()

    def update_affichage(self):
        source = self.combo_source.get()
        dest = self.combo_dest.get()
        plt.close()

        if source == "" or dest == "" or source == dest:
            return

        # Chargement des deux comptes
        df_source = pd.read_excel(source+'.xlsx')
        df_dest = pd.read_excel(dest+'.xlsx')

        # Nettoyage
        df_source['Date'] = pd.to_datetime(df_source['Date']).dt.date
        df_dest['Date'] = pd.to_datetime(df_dest['Date']).dt.date

        # Filtrage
        transferts_depense = df_source[(df_source['Type'] == 'Depense') & (df_source['Classe'] == dest)]
        transferts_revenu = df_dest[(df_dest['Type'] == 'Revenu') & (df_dest['Classe'] == source)]

        total_envoye = transferts_depense['Valeur'].sum()
        total_recu = transferts_revenu['Valeur'].sum()

        self.label_resume.config(
            text=f"Total de {source} → {dest} : Total envoyé {total_envoye} € | Total reçu : {total_recu} €"
        )

        # Graphique cumulé
        df_plot = pd.concat([transferts_depense, transferts_revenu])
        df_plot = df_plot.sort_values(by="Date")
        df_plot['Sens'] = df_plot['Type'].apply(lambda x: -1 if x == 'Depense' else 1)
        
        df_plot['Cumulé'] = (df_plot['Valeur'] * df_plot['Sens']).cumsum()

        for widget in self.frame_graph.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(7, 4))
        if not df_plot.empty:
            ax.plot(df_plot['Date'], df_plot['Cumulé'], marker='o')
            ax.set_title(f"Évolution cumulée {source} ↔ {dest}")
            ax.set_ylabel("Solde cumulé (€)")
            ax.grid(True)
        else:
            ax.text(0.5, 0.5, "Aucun Echange d'argent entre ses deux comptes", ha='center', va='center')
            ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        