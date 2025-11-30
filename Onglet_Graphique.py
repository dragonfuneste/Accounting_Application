
from Fonction import *
from Compte import Compte
from Librairie import *
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import traceback


class Onglet_Graphique(ttk.Frame):
    """Onglet graphique pour visualiser les dépenses et revenus par catégorie/classe.
    
    Fonctionnalités:
    - Deux graphiques (camembert): Dépenses et Revenus
    - Menu pour sélectionner les mois à afficher
    - Bouton pour basculer entre Catégorie et Classe
    - Affichage du % et de la somme en légende
    """

    def __init__(self, parent, comptes, combo_var):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        self.combo_var = combo_var
        self.current_compte = None
        self.view_by = 'Categorie'  # ou 'Classe'
        self.selected_months = []  # Mois sélectionnés pour afficher
        
        # Observer le changement de compte
        self.combo_var.trace('w', self.on_account_changed)
        
        self.create_ui()

    def create_ui(self):
        """Crée l'interface avec contrôles et graphiques."""
        # Frame supérieur avec contrôles
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        # Bouton pour basculer vue
        self.toggle_view_btn = ttk.Button(top, text=f"Vue: {self.view_by}", command=self.toggle_view)
        self.toggle_view_btn.pack(side=tk.LEFT, padx=4)

        # Label et Frame scrollable pour les checkboxes des mois
        ttk.Label(top, text="Mois à afficher:").pack(side=tk.LEFT, padx=4)
        
        # Créer un frame avec scrollbar pour les checkboxes
        months_frame = ttk.LabelFrame(top, text="Sélectionner les mois", relief=tk.RAISED)
        months_frame.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        
        # Canvas et scrollbar pour les checkboxes
        self.months_canvas = tk.Canvas(months_frame, height=30, bg='white', highlightthickness=1)
        scrollbar = ttk.Scrollbar(months_frame, orient=tk.HORIZONTAL, command=self.months_canvas.xview)
        self.months_scrollable_frame = ttk.Frame(self.months_canvas)
        
        self.months_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.months_canvas.configure(scrollregion=self.months_canvas.bbox("all"))
        )
        
        self.months_canvas.create_window((0, 0), window=self.months_scrollable_frame, anchor="nw")
        self.months_canvas.configure(xscrollcommand=scrollbar.set)
        
        self.months_canvas.pack(fill=tk.X, expand=True)
        scrollbar.pack(fill=tk.X)
        
        # Dictionnaire pour stocker les variables Checkbutton
        self.months_vars = {}
        
        # Bouton pour rafraîchir
        self.refresh_btn = ttk.Button(top, text="Rafraîchir", command=self.refresh_display)
        self.refresh_btn.pack(side=tk.LEFT, padx=4)

        # Frame pour les graphiques (côte à côte, même taille)
        graphs_frame = ttk.Frame(self)
        graphs_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Configurer le poids égal pour les deux colonnes
        graphs_frame.grid_columnconfigure(0, weight=1)
        graphs_frame.grid_columnconfigure(1, weight=1)

        # Frame pour graphique Dépenses
        dep_frame = ttk.LabelFrame(graphs_frame, text='Graphique Dépenses')
        dep_frame.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        self.canvas_dep = tk.Canvas(dep_frame, bg='white')
        self.canvas_dep.pack(fill=tk.BOTH, expand=True)

        # Frame pour graphique Revenus
        rev_frame = ttk.LabelFrame(graphs_frame, text='Graphique Revenus')
        rev_frame.grid(row=0, column=1, sticky='nsew', padx=4, pady=4)
        self.canvas_rev = tk.Canvas(rev_frame, bg='white')
        self.canvas_rev.pack(fill=tk.BOTH, expand=True)

    def on_account_changed(self, *args):
        """Appelé quand le compte sélectionné change."""
        name = self.combo_var.get()
        if name and name in self.comptes:
            self.current_compte = self.comptes[name]
            self.update_months_list()
            self.refresh_display()

    def toggle_view(self):
        """Bascule la vue entre Catégorie et Classe."""
        self.view_by = 'Classe' if self.view_by == 'Categorie' else 'Categorie'
        self.toggle_view_btn.config(text=f"Vue: {self.view_by}")
        self.refresh_display()

    def update_months_list(self):
        """Met à jour la liste des mois disponibles avec des checkboxes."""
        if not self.current_compte:
            return

        df = self.current_compte.df.copy()
        if df.empty or 'Date' not in df.columns:
            # Vider les checkboxes
            for widget in self.months_scrollable_frame.winfo_children():
                widget.destroy()
            self.months_vars = {}
            return

        df = df.dropna(subset=['Date'])
        months = sorted(df['Date'].dt.to_period('M').astype(str).unique().tolist())
        
        # Vider les anciennes checkboxes
        for widget in self.months_scrollable_frame.winfo_children():
            widget.destroy()
        self.months_vars = {}
        
        # Créer une checkbox pour chaque mois
        for month in months:
            var = tk.BooleanVar(value=True)  # Tous les mois sélectionnés par défaut
            self.months_vars[month] = var
            
            cb = tk.Checkbutton(self.months_scrollable_frame, text=month, variable=var,
                               bg='white', activebackground='lightblue', activeforeground='black')
            cb.pack(side=tk.LEFT, padx=4, pady=2)
        
        # Mettre à jour la liste des mois sélectionnés
        self.selected_months = months

    def refresh_display(self):
        """Rafraîchit les graphiques selon les mois sélectionnés."""
        if not self.current_compte:
            return

        try:
            # Récupérer les mois sélectionnés à partir des checkboxes
            self.selected_months = [month for month, var in self.months_vars.items() if var.get()]
            
            if not self.selected_months:
                # Si aucun mois n'est sélectionné, afficher tous
                self.selected_months = list(self.months_vars.keys())

            # Préparer les données
            df = self.current_compte.df.copy()
            if df.empty or 'Date' not in df.columns:
                return

            df = df.dropna(subset=['Date'])
            df['Mois'] = df['Date'].dt.to_period('M').astype(str)

            # Filtrer par mois sélectionnés
            if self.selected_months:
                df = df[df['Mois'].isin(self.selected_months)]

            # Créer les graphiques
            self.create_pie_chart(df, 'Depense', self.canvas_dep)
            self.create_pie_chart(df, 'Revenu', self.canvas_rev)

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            try:
                messagebox.showerror("Erreur rafraîchissement graphique", f"{str(e)}\nVoir la console pour la trace complète.")
            except Exception:
                pass

    def create_pie_chart(self, df, type_filter, canvas):
        """Crée un graphique camembert pour un type donné avec légende en bas."""
        # Filtrer par type
        df_type = df[df['Type'] == type_filter]
        if df_type.empty:
            # Vider le canvas si pas de données
            for widget in canvas.winfo_children():
                widget.destroy()
            return

        group_col = self.view_by
        
        # Regrouper par catégorie/classe et sommer
        data = df_type.groupby(group_col)['Valeur'].sum().sort_values(ascending=False)
        
        if data.empty:
            return

        # Créer la figure matplotlib avec hauteur suffisante pour la légende
        fig = Figure(figsize=(6, 6), dpi=100)
        ax = fig.add_subplot(111)

        # Préparer les données et labels
        total = data.sum()
        labels = []
        legend_labels = []
        
        for name, val in data.items():
            pct = (val / total * 100) if total != 0 else 0
            # Pour le camembert, on met juste le pourcentage
            labels.append(f"{pct:.1f}%")
            # Pour la légende, on met le nom, le montant et le pourcentage
            legend_labels.append(f"{name}: {val:.2f}€ ({pct:.1f}%)")

        # Créer le camembert
        colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
        wedges, texts, autotexts = ax.pie(data.values, labels=labels, autopct='',
                                            colors=colors, startangle=90)

        # Améliorer la police des étiquettes de pourcentage
        for text in texts:
            text.set_fontsize(8)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

        # Ajouter le titre
        ax.set_title(f"{type_filter} - Total: {total:.2f}€", fontsize=12, fontweight='bold', pad=10)

        # Ajouter la légende en bas avec deux colonnes
        ax.legend(legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), 
                  ncol=2, frameon=True, fontsize=8, framealpha=0.9)

        # Ajuster l'espacement pour laisser de la place à la légende
        fig.tight_layout()

        # Supprimer les anciens widgets du canvas
        for widget in canvas.winfo_children():
            widget.destroy()

        # Intégrer la figure dans tkinter
        chart_canvas = FigureCanvasTkAgg(fig, master=canvas)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """Méthode standard appelée par `refresh_all` de l'application principale.

        Met à jour la liste des mois disponibles puis rafraîchit l'affichage.
        """
        try:
            self.update_months_list()
            self.refresh_display()
        except Exception:
            # Ne pas remonter d'exception ici, refresh_all gère l'UI globale.
            pass