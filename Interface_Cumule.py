from Fonction import *
from Compte import Compte
from Librairie import *
import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


class Onglet_Cumule(ttk.Frame):
    """Onglet pour afficher les graphiques cumulés de chaque compte et le total.
    
    Fonctionnalités:
    - Affiche un graphique cumulé par compte (Revenus - Dépenses)
    - Bouton pour ajouter le cumulé total (tous les comptes)
    - Affichage chronologique avec évolution du solde
    """

    def __init__(self, parent, comptes):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        self.show_total = False  # État pour afficher le total
        
        self.create_ui()
        self.refresh_display()

    def create_ui(self):
        """Crée l'interface avec contrôles et graphique."""
        # Frame supérieur avec contrôles
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        # Bouton pour afficher/cacher le cumulé total
        self.toggle_total_btn = ttk.Button(top, text="Afficher cumulé total", command=self.toggle_total)
        self.toggle_total_btn.pack(side=tk.LEFT, padx=4)

        # Bouton pour rafraîchir
        self.refresh_btn = ttk.Button(top, text="Rafraîchir", command=self.refresh_display)
        self.refresh_btn.pack(side=tk.LEFT, padx=4)

        # Frame pour le graphique
        graph_frame = ttk.LabelFrame(self, text='Graphique Cumulé')
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas = tk.Canvas(graph_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Frame inférieur pour afficher les valeurs actuelles
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(bottom_frame, text="Soldes actuels:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=4)
        
        # Frame scrollable pour les soldes des comptes
        self.soldes_frame = ttk.Frame(bottom_frame)
        self.soldes_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        
        ttk.Label(bottom_frame, text="| Total:").pack(side=tk.LEFT, padx=4)
        
        self.total_value_label = ttk.Label(bottom_frame, text="0.00€", 
                                           font=("Segoe UI", 12, "bold"), foreground="blue")
        self.total_value_label.pack(side=tk.LEFT, padx=4)

    def toggle_total(self):
        """Bascule l'affichage du cumulé total."""
        self.show_total = not self.show_total
        self.toggle_total_btn.config(
            text="Masquer cumulé total" if self.show_total else "Afficher cumulé total"
        )
        self.refresh_display()

    def refresh_display(self):
        """Crée et affiche le graphique cumulé de tous les comptes."""
        if not self.comptes:
            return

        # Créer la figure
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)

        # Stocker les courbes tracées pour la légende
        all_curves_traced = False
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.comptes) + 1))
        color_idx = 0
        
        # Variable pour stocker le cumul total final
        total_final_value = 0.0
        
        # Dictionnaire pour stocker les soldes des comptes
        soldes_comptes = {}

        # Tracer une courbe pour chaque compte
        for nom_compte, compte in self.comptes.items():
            df = compte.df.copy()
            
            if df.empty or 'Date' not in df.columns:
                continue

            # Préparer les données
            df = df.dropna(subset=['Date'])
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date')

            # Appliquer le signe selon le type (revenu/dépense)
            if 'Type' in df.columns:
                df['Valeur_Signee'] = df.apply(
                    lambda row: row['Valeur'] if str(row['Type']).lower() in ['revenu', 'income'] else -row['Valeur'],
                    axis=1
                )
            else:
                df['Valeur_Signee'] = df['Valeur']

            # Calcul du cumul
            df['Cumul'] = df['Valeur_Signee'].cumsum()
            
            # Stocker le solde final du compte
            soldes_comptes[nom_compte] = df['Cumul'].iloc[-1] if not df.empty else 0.0

            # Tracer la courbe
            ax.plot(df['Date'], df['Cumul'], 
                   marker='o', linestyle='-', 
                   label=f"{nom_compte}", 
                   color=colors[color_idx],
                   linewidth=2)
            color_idx += 1
            all_curves_traced = True

        # Ajouter le cumulé total si demandé
        if self.show_total:
            all_dfs = []
            
            for nom_compte, compte in self.comptes.items():
                df = compte.df.copy()
                
                if df.empty or 'Date' not in df.columns:
                    continue

                df = df.dropna(subset=['Date'])
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                # Appliquer le signe
                if 'Type' in df.columns:
                    df['Valeur_Signee'] = df.apply(
                        lambda row: row['Valeur'] if str(row['Type']).lower() in ['revenu', 'income'] else -row['Valeur'],
                        axis=1
                    )
                else:
                    df['Valeur_Signee'] = df['Valeur']

                all_dfs.append(df[['Date', 'Valeur_Signee']])

            if all_dfs:
                # Combiner tous les DataFrames
                df_total = pd.concat(all_dfs, ignore_index=True)
                df_total = df_total.sort_values('Date')
                
                # Calculer le cumul total
                df_total['Cumul'] = df_total['Valeur_Signee'].cumsum()
                
                # Récupérer la dernière valeur du cumul total
                total_final_value = df_total['Cumul'].iloc[-1] if not df_total.empty else 0.0
                
                # Tracer la courbe totale avec style différent (plus épais)
                ax.plot(df_total['Date'], df_total['Cumul'], 
                       marker='s', linestyle='--', linewidth=3,
                       label='TOTAL', 
                       color=colors[color_idx],
                       zorder=10)  # Mettre au-dessus des autres courbes

        # Mettre à jour le frame avec les soldes des comptes
        # Vider les anciens labels
        for widget in self.soldes_frame.winfo_children():
            widget.destroy()
        
        # Ajouter les soldes des comptes
        for nom_compte, solde in soldes_comptes.items():
            color = "green" if solde >= 0 else "red"
            label = ttk.Label(self.soldes_frame, text=f"{nom_compte}: {solde:.2f}€", 
                            foreground=color, font=("Segoe UI", 9))
            label.pack(side=tk.LEFT, padx=2)

        # Mettre à jour le label avec la valeur actuelle du total
        if self.show_total:
            # Déterminer la couleur selon le signe
            color = "green" if total_final_value >= 0 else "red"
            self.total_value_label.config(text=f"{total_final_value:.2f}€", foreground=color)
        else:
            self.total_value_label.config(text="0.00€", foreground="blue")

        # Personnalisation du graphique
        if all_curves_traced:
            ax.set_title("Évolution du solde cumulé par compte", fontsize=14, fontweight='bold')
            ax.set_xlabel("Date", fontsize=11)
            ax.set_ylabel("Solde cumulé (€)", fontsize=11)
            ax.axhline(0, color='red', linestyle='--', alpha=0.5, linewidth=1)
            ax.legend(loc='upper left', fontsize=9, framealpha=0.95)
            ax.grid(True, alpha=0.3)
            
            # Formatage des dates sur l'axe X
            fig.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "Aucune donnée disponible", 
                   ha='center', va='center',
                   transform=ax.transAxes, 
                   fontsize=14)

        fig.tight_layout()

        # Supprimer les anciens widgets du canvas
        for widget in self.canvas.winfo_children():
            widget.destroy()

        # Intégrer la figure dans tkinter
        chart_canvas = FigureCanvasTkAgg(fig, master=self.canvas)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        """Appelé pour rafraîchir l'onglet (interface commune)."""
        self.refresh_display()
