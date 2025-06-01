import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib

"""
REFAIRE la gestion du click quand on change de compte
"""

class OngletGraphique(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.mode = True  # True = Suivi temporel, False = Camemberts
        self.build_interface()

    def build_interface(self):
        # Bouton pour changer de mode
        self.button_switch = ttk.Button(self, text="Changer de mode", command=self.switch_mode)
        self.button_switch.pack(pady=10)
        if self.mode:
            self.button_all = ttk.Button(self, text="Afficher tout", command=self.afficher_suivis_tout)
            self.button_all.pack(pady=5)

        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.display_graph()

    def switch_mode(self):
        self.mode = not self.mode
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.display_graph()
    def update_graph(self) :
        self.info_label.destroy();
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.display_graph()
        
    def display_graph(self):
        self.df = self.app.df  # Récupère les données

        if self.mode:

            
            self.info_label = ttk.Label(self, text="", foreground="blue")
            self.info_label.pack(pady=5)
            fig, self.ax = plt.subplots(figsize=(6, 4))
            self.Plot_Suivis(fig, self.ax)
        else:
            fig = plt.figure(figsize=(10, 8))
            self.ax1 = fig.add_subplot(2, 2, 1)
            self.ax2 = fig.add_subplot(2, 2, 2)
            self.ax3 = fig.add_subplot(2, 2, 3)
            self.ax4 = fig.add_subplot(2, 2, 4)
            self.Plot_Cammembert(fig)

        fig.canvas.mpl_connect('pick_event', self.on_click)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas.mpl_connect("button_press_event", self.on_click)

    def Plot_Suivis(self, fig, ax):
        self.df.loc[:, 'Date'] = pd.to_datetime(self.df['Date'])
        df_sorted = self.df.sort_values('Date')
        df_sorted = df_sorted.groupby('Date').sum(numeric_only=True)
        self.df_sorted = df_sorted  # Sauvegarde pour clics

        if df_sorted.empty:
            ax.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return

        ax.plot(df_sorted.index, df_sorted['Valeur'], marker="o", linestyle="-")
        ax.set_title("Suivi Temporel")
        ax.set_xlabel("Date")
        ax.set_ylabel("Valeur cumulée")
        

    def Plot_Cammembert(self, fig):
        self.df_depenses = self.df[self.df['Type'] == 'Depense']
        self.df_revenus = self.df[self.df['Type'] == 'Revenu']

        self.depenses_grouped = self.df_depenses.groupby('Categorie')['Valeur'].sum()
        self.revenus_grouped = self.df_revenus.groupby('Categorie')['Valeur'].sum()

        self.wedges1, _, _ = self.ax1.pie(
            self.depenses_grouped, labels=self.depenses_grouped.index,
            autopct='%1.1f%%', startangle=90)
        
        self.ax1.set_title("Répartition des dépenses")
        
        self.wedges2, _, _ = self.ax2.pie(
            self.revenus_grouped, labels=self.revenus_grouped.index,
            autopct='%1.1f%%', startangle=90)
        
        self.ax2.set_title("Répartition des revenus")


        # Rendre chaque secteur cliquable
        for wedge in self.wedges1 + self.wedges2:
            wedge.set_picker(True)

        
    def on_click(self, event):
        if self.mode:
            self.On_click_Suivis(event)
        else:
            self.On_click_Camembert(event)

    def On_click_Suivis(self,event):
            # Partie courbe
            if not hasattr(self, 'df_sorted') or self.df_sorted.empty:
                print("⚠️ Aucun df_sorted disponible")
                return
    
            if event.inaxes != self.ax or event.xdata is None:
                print("⚠️ Clic hors de l'axe ou données manquantes")
                return
    
            try:
                xdata = self.df_sorted.index
                clicked_date = matplotlib.dates.num2date(event.xdata).replace(tzinfo=None)
                closest_date = min(xdata, key=lambda d: abs(d - clicked_date))
    
                if not hasattr(self, 'df') or self.df.empty:
                    print("⚠️ Aucun df de référence disponible")
                    return
    
                df_filtered = self.df[self.df['Date'] <= closest_date]
    
                total_dep = df_filtered[df_filtered['Type'] == 'Depense']['Valeur'].sum()
                total_rev = df_filtered[df_filtered['Type'] == 'Revenu']['Valeur'].sum()
                solde = total_rev - total_dep
    
                self.info_label.config(
                    text=f"{closest_date.date()} → Dépenses : {total_dep:.2f}€, Revenus : {total_rev:.2f}€, Solde : {solde:.2f}€"
                )
            except Exception as e:
                print(f"❌ Erreur pendant le traitement du clic sur la courbe : {e}")

    def On_click_Camembert(self,event):
        # Partie diagramme circulaire
        wedge = event.artist
        label = wedge.get_label()

        # Réinitialiser opacité
        for w in getattr(self, 'wedges1', []) + getattr(self, 'wedges2', []):
            w.set_alpha(1.0)

        wedge.set_alpha(0.4)

        # Accès aux données filtrées
        df_dep = getattr(self, 'df_depenses', pd.DataFrame())
        df_rev = getattr(self, 'df_revenus', pd.DataFrame())

        df_classe_dep = df_dep[df_dep['Categorie'] == label] if not df_dep.empty else pd.DataFrame()
        df_classe_rev = df_rev[df_rev['Categorie'] == label] if not df_rev.empty else pd.DataFrame()

        grouped_dep = df_classe_dep.groupby('Classe')['Valeur'].sum() if not df_classe_dep.empty else pd.Series(dtype=float)
        grouped_rev = df_classe_rev.groupby('Classe')['Valeur'].sum() if not df_classe_rev.empty else pd.Series(dtype=float)

        self.ax3.clear()
        self.ax4.clear()
        self.ax3.axis("off")
        self.ax4.axis("off")

        if not grouped_dep.empty:
            self.ax3.pie(grouped_dep, labels=grouped_dep.index, autopct='%1.1f%%', startangle=90)
            self.ax3.set_title(f"Dépense '{label}' : {grouped_dep.sum():.2f}")
        else:
            self.ax3.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', transform=self.ax3.transAxes, fontsize=12)
            self.ax3.set_title(f"Dépense '{label}'")

        if not grouped_rev.empty:
            self.ax4.pie(grouped_rev, labels=grouped_rev.index, autopct='%1.1f%%', startangle=90)
            self.ax4.set_title(f"Revenu '{label}' : {grouped_rev.sum():.2f}")
        else:
            self.ax4.text(0.5, 0.5, "Aucune donnée", ha='center', va='center', transform=self.ax4.transAxes, fontsize=12)
            self.ax4.set_title(f"Revenu '{label}'")

        self.canvas.draw()
    def afficher_suivis_tout(self):
        
        if not hasattr(self.app, 'dataframes'):
            print("❌ self.app n'a pas d'attribut 'dataframes'")
            return
    
        dataframes = self.app.dataframes
    
        if isinstance(dataframes, dict):
            df_items = dataframes.items()  # (nom, df)
        elif isinstance(dataframes, list):
            df_items = [(f"Fichier {i+1}", df) for i, df in enumerate(dataframes)]
        else:
            print("❌ 'dataframes' doit être une liste ou un dictionnaire de DataFrames")
            return
    
        today = pd.Timestamp.today().normalize()
        self.ax.clear()
    
        courbe_tracee = False
    
        for nom, df in df_items:
            if df.empty:
                continue
    
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
    
            last_date = df['Date'].max().normalize()
            if last_date < today:
                df_grouped = df.groupby('Date').sum(numeric_only=True)
                last_value = df_grouped.loc[last_date]['Valeur']
                new_row = {
                    'Date': today,
                    'Valeur': last_value,
                    'Type': df[df['Date'] == last_date]['Type'].iloc[-1] if 'Type' in df.columns else '',
                    'Categorie': df[df['Date'] == last_date]['Categorie'].iloc[-1] if 'Categorie' in df.columns else '',
                    'Classe': df[df['Date'] == last_date]['Classe'].iloc[-1] if 'Classe' in df.columns else ''
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
            df_grouped = df.groupby('Date').sum(numeric_only=True)
            self.ax.plot(df_grouped.index, df_grouped['Valeur'], marker='o', linestyle='-', label=nom)
            courbe_tracee = True
    
        if not courbe_tracee:
            self.ax.text(0.5, 0.5, "Aucune donnée", ha='center', va='center',
                         transform=self.ax.transAxes, fontsize=14)
        else:
            self.ax.set_title("Suivi temporel - Par fichier")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Valeur cumulée")
            self.ax.legend()
    
        self.canvas.draw()
    
