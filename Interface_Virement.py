from Fonction import *
from Compte import Compte
from Librairie import *
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, date as dt_date
import numpy as np


class Interface_Virement(ttk.Frame):
    """Onglet pour gérer les virements entre comptes.
    
    Fonctionnalités:
    - Sélectionner un compte source et un compte destination
    - Spécifier un montant et une date
    - Ajouter un virement (crée une dépense et un revenu)
    - Afficher le résumé des virements entre deux comptes
    - Graphique cumulé des échanges
    """

    def __init__(self, parent, comptes):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        
        self.create_ui()

    def create_ui(self):
        """Crée l'interface."""
        # Frame supérieur avec contrôles
        top_frame = ttk.LabelFrame(self, text="Ajouter un virement")
        top_frame.pack(fill=tk.X, padx=8, pady=8)

        # Sélection des comptes
        ttk.Label(top_frame, text="Compte source:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_source = ttk.Combobox(top_frame, values=list(self.comptes.keys()), state="readonly", width=15)
        if self.comptes:
            self.combo_source.current(0)
        self.combo_source.grid(row=0, column=1, padx=5, pady=5)
        self.combo_source.bind("<<ComboboxSelected>>", lambda e: self.update_affichage())

        ttk.Label(top_frame, text="Compte destination:").grid(row=0, column=2, padx=5, pady=5)
        self.combo_dest = ttk.Combobox(top_frame, values=list(self.comptes.keys()), state="readonly", width=15)
        if len(self.comptes) > 1:
            self.combo_dest.current(1)
        else:
            self.combo_dest.current(0)
        self.combo_dest.grid(row=0, column=3, padx=5, pady=5)
        self.combo_dest.bind("<<ComboboxSelected>>", lambda e: self.update_affichage())

        # Montant
        ttk.Label(top_frame, text="Montant (€):").grid(row=0, column=4, padx=5, pady=5)
        self.entry_montant = ttk.Entry(top_frame, width=12)
        self.entry_montant.grid(row=0, column=5, padx=5, pady=5)

        # Date du virement
        ttk.Label(top_frame, text="Date:").grid(row=0, column=6, padx=5, pady=5)
        self.date_virement = DateEntry(top_frame, width=12)
        self.date_virement.set_date(datetime.today())
        self.date_virement.grid(row=0, column=7, padx=5, pady=5)

        # Bouton d'ajout
        btn_add = ttk.Button(top_frame, text="Ajouter virement", command=self.ajouter_virement)
        btn_add.grid(row=0, column=8, padx=10, pady=5)

        # Résumé virement
        self.label_resume = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"), foreground="blue")
        self.label_resume.pack(pady=8)

        # Frame pour le graphique
        graph_frame = ttk.LabelFrame(self, text="Graphique des virements")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.frame_graph = tk.Canvas(graph_frame, bg='white')
        self.frame_graph.pack(fill=tk.BOTH, expand=True)

        # Initialiser l'affichage
        self.update_affichage()

    def ajouter_virement(self):
        """Ajoute un virement entre deux comptes."""
        try:
            montant = float(self.entry_montant.get())
            if montant <= 0:
                messagebox.showerror("Erreur", "Le montant doit être positif")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide")
            return

        source = self.combo_source.get()
        dest = self.combo_dest.get()

        if not source or not dest:
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux comptes")
            return

        if source == dest:
            messagebox.showerror("Erreur", "Les comptes source et destination doivent être différents")
            return

        date = self.date_virement.get_date()

        # Ajouter les lignes aux comptes avec les paramètres individuels
        try:
            # Convertir la date en pd.Timestamp
            date_ts = pd.Timestamp(date)
            
            # Dépense sur le compte source
            self.comptes[source].ajouter_ligne(
                date=date_ts,
                intitule="Virement",
                categorie="Banque",
                classe=dest,
                type_operation="Depense",
                valeur=montant
            )
            
            # Revenu sur le compte destination
            self.comptes[dest].ajouter_ligne(
                date=date_ts,
                intitule="Virement",
                categorie="Banque",
                classe=source,
                type_operation="Revenu",
                valeur=montant
            )
            
            # Sauvegarder les comptes
            self.comptes[source].sauvegarder()
            self.comptes[dest].sauvegarder()

            # Recharger les DataFrames depuis les fichiers pour s'assurer que les fichiers sur disque
            # contiennent bien les nouvelles lignes et que l'objet en mémoire est synchronisé.
            try:
                self.comptes[source].df = pd.read_excel(self.comptes[source].chemin)
                self.comptes[dest].df = pd.read_excel(self.comptes[dest].chemin)
            except Exception:
                # Si la lecture échoue, on ignore; les sauvegardes ont été tentées.
                pass

            # Confirmation à l'utilisateur avec informations de diagnostic simples
            try:
                n_source = len(self.comptes[source].df)
            except Exception:
                n_source = 'n/a'
            try:
                n_dest = len(self.comptes[dest].df)
            except Exception:
                n_dest = 'n/a'

            messagebox.showinfo(
                "Succès",
                f"Virement de {montant:.2f}€ de {source} vers {dest} ajouté.\n"
                f"Lignes dans {source}: {n_source} | Lignes dans {dest}: {n_dest}"
            )

            self.entry_montant.delete(0, tk.END)
            self.update_affichage()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout du virement: {str(e)}")

    def update_affichage(self):
        """Met à jour le résumé et le graphique."""
        source = self.combo_source.get()
        dest = self.combo_dest.get()

        if not source or not dest or source == dest or source not in self.comptes or dest not in self.comptes:
            self.label_resume.config(text="Sélectionnez deux comptes différents")
            self.draw_empty_graph()
            return

        # Récupérer les DataFrames des deux comptes
        df_source = self.comptes[source].df.copy()
        df_dest = self.comptes[dest].df.copy()

        # Nettoyage des dates
        if not df_source.empty and 'Date' in df_source.columns:
            df_source['Date'] = pd.to_datetime(df_source['Date'], errors='coerce')
        if not df_dest.empty and 'Date' in df_dest.columns:
            df_dest['Date'] = pd.to_datetime(df_dest['Date'], errors='coerce')

        # Filtrage des virements
        transferts_depense = df_source[
            (df_source['Type'] == 'Depense') & 
            (df_source['Categorie'] == 'Banque') & 
            (df_source['Classe'] == dest)
        ] if not df_source.empty else pd.DataFrame()
        
        transferts_revenu = df_dest[
            (df_dest['Type'] == 'Revenu') & 
            (df_dest['Categorie'] == 'Banque') & 
            (df_dest['Classe'] == source)
        ] if not df_dest.empty else pd.DataFrame()

        # Calcul des totaux
        total_envoye = transferts_depense['Valeur'].sum() if not transferts_depense.empty else 0
        total_recu = transferts_revenu['Valeur'].sum() if not transferts_revenu.empty else 0

        # Mise à jour du résumé
        self.label_resume.config(
            text=f"{source} → {dest}: Envoyé {total_envoye:.2f}€ | Reçu {total_recu:.2f}€ | Solde: {total_recu - total_envoye:.2f}€"
        )

        # Créer le graphique
        self.draw_graph(transferts_depense, transferts_revenu, source, dest)

    def draw_graph(self, transferts_depense, transferts_revenu, source, dest):
        """Crée le graphique cumulé des virements."""
        # Combiner les deux DataFrames
        df_plot = pd.concat([transferts_depense, transferts_revenu], ignore_index=True)
        
        if df_plot.empty:
            self.draw_empty_graph()
            return

        df_plot = df_plot.sort_values(by="Date")
        
        # Calculer le cumul signé
        df_plot['Sens'] = df_plot['Type'].apply(lambda x: -1 if x == 'Depense' else 1)
        df_plot['Cumulé'] = (df_plot['Valeur'] * df_plot['Sens']).cumsum()

        # Créer la figure
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)

        # Tracer la courbe
        ax.plot(df_plot['Date'], df_plot['Cumulé'], marker='o', linestyle='-', 
               linewidth=2, markersize=6, color='steelblue', label='Solde cumulé')
        
        # Ligne de référence à 0
        ax.axhline(0, color='red', linestyle='--', alpha=0.5)
        
        # Personnalisation
        ax.set_title(f"Évolution cumulée des virements: {source} ↔ {dest}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Solde cumulé (€)", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        # Formatage des dates
        fig.autofmt_xdate()
        fig.tight_layout()

        # Vider le canvas et afficher la figure
        for widget in self.frame_graph.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def draw_empty_graph(self):
        """Affiche un graphique vide avec message."""
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        
        ax.text(0.5, 0.5, "Aucun virement entre ces deux comptes", 
               ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.axis('off')

        for widget in self.frame_graph.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """Appelé pour rafraîchir l'onglet (interface commune)."""
        self.update_affichage()
