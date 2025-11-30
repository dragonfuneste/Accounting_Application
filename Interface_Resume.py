from Fonction import *
from Compte import Compte
from Librairie import *
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import os
from datetime import datetime
import re


class Onglet_Resume(ttk.Frame):
    """Onglet résumé du compte sélectionné.

    Fonctionnalités principales (inspirées de `Onglet_Tableau`):
    - Basculer la vue entre `Categorie` et `Classe`.
    - Afficher un tableau mensuel des dépenses par catégorie/classe.
    - Lignes additionnelles pour totaux mensuels (Dépenses, Revenus) et cumulés.
    - Lignes finales indiquant la plus grosse dépense/revenu par colonne (nom + montant).
    - Double-clic sur une cellule (mois x catégorie/classe) ouvre une fenêtre montrant la répartition
      par l'autre dimension (ex: si vue=Catégorie, montrer répartition par Classe pour ce mois+catégorie).
    """

    def __init__(self, parent, comptes, combo_var):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        self.combo_var = combo_var
        self.current_compte = None
        self.view_by = 'Categorie'  # ou 'Classe'
        self.show_as_percent = False  # État du mode affichage (montant ou %)

        # Observer le changement de compte
        self.combo_var.trace('w', self.on_account_changed)

        self.create_ui()

    def create_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        # Un seul bouton pour basculer la vue et rafraîchir
        self.toggle_refresh_btn = ttk.Button(top, text=f"Vue: {self.view_by} — Basculer/Rafraîchir",
                                             command=self.toggle_and_refresh)
        self.toggle_refresh_btn.pack(side=tk.LEFT)

        # Bouton pour basculer entre montant et pourcentage dans les popups
        self.toggle_display_btn = ttk.Button(top, text='Affichage: Montant', command=self.toggle_display_mode)
        self.toggle_display_btn.pack(side=tk.LEFT, padx=6)

        # Deux tableaux : Dépenses puis Revenus
        # Cadre pour les dépenses
        dep_frame = ttk.LabelFrame(self, text='Dépenses')
        dep_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        dep_vsb = ttk.Scrollbar(dep_frame, orient=tk.VERTICAL)
        dep_hsb = ttk.Scrollbar(dep_frame, orient=tk.HORIZONTAL)
        self.tree_dep = ttk.Treeview(dep_frame, show='headings', yscrollcommand=dep_vsb.set, xscrollcommand=dep_hsb.set)
        dep_vsb.config(command=self.tree_dep.yview)
        dep_hsb.config(command=self.tree_dep.xview)
        self.tree_dep.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        dep_vsb.pack(side=tk.LEFT, fill=tk.Y)
        dep_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        # Utiliser un seul clic pour ouvrir la répartition (demande utilisateur)
        self.tree_dep.bind('<ButtonRelease-1>', lambda e: self.on_cell_double(e, 'Depense'))

        # Cadre pour les revenus
        rev_frame = ttk.LabelFrame(self, text='Revenus')
        rev_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        rev_vsb = ttk.Scrollbar(rev_frame, orient=tk.VERTICAL)
        rev_hsb = ttk.Scrollbar(rev_frame, orient=tk.HORIZONTAL)
        self.tree_rev = ttk.Treeview(rev_frame, show='headings', yscrollcommand=rev_vsb.set, xscrollcommand=rev_hsb.set)
        rev_vsb.config(command=self.tree_rev.yview)
        rev_hsb.config(command=self.tree_rev.xview)
        self.tree_rev.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        rev_vsb.pack(side=tk.LEFT, fill=tk.Y)
        rev_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_rev.bind('<ButtonRelease-1>', lambda e: self.on_cell_double(e, 'Revenu'))

        # Petit panneau d'aide / légende
        help_frame = ttk.Frame(self)
        help_frame.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(help_frame, text="Cliquer sur une cellule pour voir la répartition par l'autre dimension.").pack(side=tk.LEFT)

    def on_account_changed(self, *args):
        name = self.combo_var.get()
        if name and name in self.comptes:
            self.current_compte = self.comptes[name]
            self.refresh_display()

    def toggle_view(self):
        self.view_by = 'Classe' if self.view_by == 'Categorie' else 'Categorie'
        self.toggle_refresh_btn.config(text=f"Vue: {self.view_by} — Basculer/Rafraîchir")

    def refresh(self):
        self.refresh_display()

    def toggle_and_refresh(self):
        """Basculer la vue puis rafraîchir l'affichage (bouton unique demandé)."""
        # Basculer la vue
        self.view_by = 'Classe' if self.view_by == 'Categorie' else 'Categorie'
        self.toggle_refresh_btn.config(text=f"Vue: {self.view_by} — Basculer/Rafraîchir")
        # Rafraîchir
        self.refresh_display()

    def toggle_display_mode(self):
        """Basculer entre affichage montant et pourcentage dans les tableaux et popups."""
        self.show_as_percent = not self.show_as_percent
        self.toggle_display_btn.config(text='Affichage: Pourcentage' if self.show_as_percent else 'Affichage: Montant')
        # Rafraîchir les tableaux pour qu'ils affichent montant ou % selon le nouvel état
        self.refresh_display()

    def refresh_display(self):
        """Construit et affiche le tableau résumé selon la vue sélectionnée."""
        if not self.current_compte:
            return

        df = self.current_compte.df.copy()
        if df.empty:
            # Vider le tree
            for iid in self.tree_dep.get_children():
                self.tree_dep.delete(iid)
            for iid in self.tree_rev.get_children():
                self.tree_rev.delete(iid)
            return

        # Préparer colonne mois
        if 'Date' in df.columns:
            df = df.dropna(subset=['Date'])
            df['Mois'] = df['Date'].dt.to_period('M').astype(str)
        else:
            df['Mois'] = ''

        group_col = self.view_by
        other_col = 'Classe' if group_col == 'Categorie' else 'Categorie'

        # Liste ordonnée des clés (lignes)
        keys = []
        if group_col in df.columns:
            keys = sorted([v for v in df[group_col].dropna().unique()])

        # Pour chaque type, ne garder que les clés qui ont des valeurs non-nulles
        keys_dep = [k for k in keys if df[(df[group_col] == k) & (df['Type'] == 'Depense')]['Valeur'].fillna(0).abs().sum() != 0]
        keys_rev = [k for k in keys if df[(df[group_col] == k) & (df['Type'] == 'Revenu')]['Valeur'].fillna(0).abs().sum() != 0]

        # Colonnes = mois + total (le premier champ de chaque ligne sera la clé)
        months = sorted(df['Mois'].unique())
        cols_dep = [group_col] + months + ['Total']
        cols_rev = [group_col] + months + ['Total']

        # Vider et configurer arbres
        for t in (self.tree_dep, self.tree_rev):
            for iid in t.get_children():
                t.delete(iid)

        self.tree_dep.config(columns=cols_dep)
        self.tree_rev.config(columns=cols_rev)

        # Configurer en-têtes pour dépense avec tri par montant au clic
        for i, c in enumerate(cols_dep):
            if i == 0:
                self.tree_dep.heading(c, text=group_col); self.tree_dep.column(c, width=160, anchor='w')
            elif c == 'Total':
                self.tree_dep.heading(c, text='Total'); self.tree_dep.column(c, width=110, anchor='e')
            else:
                # month columns — tri par clic
                def make_sort_handler(tree, col):
                    sort_state = {'ascending': False}  # État de tri pour cette colonne
                    def sort_by_col():
                        items = [(tree.set(k, col), k) for k in tree.get_children('')]
                        def extract_number(s):
                            """Extrait le nombre d'une chaîne (montant ou pourcentage)"""
                            if not s:
                                return 0
                            match = re.search(r'-?\d+\.?\d*', s)
                            return float(match.group()) if match else 0
                        # Alterner entre ascendant et descendant
                        sort_state['ascending'] = not sort_state['ascending']
                        items.sort(key=lambda x: extract_number(x[0]), reverse=not sort_state['ascending'])
                        for idx, (val, k) in enumerate(items):
                            tree.move(k, '', idx)
                    return sort_by_col
                self.tree_dep.heading(c, text=c, command=make_sort_handler(self.tree_dep, c))
                self.tree_dep.column(c, width=100, anchor='e')

        # Configurer en-têtes pour revenu avec tri par montant au clic
        for i, c in enumerate(cols_rev):
            if i == 0:
                self.tree_rev.heading(c, text=group_col); self.tree_rev.column(c, width=160, anchor='w')
            elif c == 'Total':
                self.tree_rev.heading(c, text='Total'); self.tree_rev.column(c, width=110, anchor='e')
            else:
                def make_sort_handler(tree, col):
                    sort_state = {'ascending': False}  # État de tri pour cette colonne
                    def sort_by_col():
                        items = [(tree.set(k, col), k) for k in tree.get_children('')]
                        def extract_number(s):
                            """Extrait le nombre d'une chaîne (montant ou pourcentage)"""
                            if not s:
                                return 0
                            match = re.search(r'-?\d+\.?\d*', s)
                            return float(match.group()) if match else 0
                        # Alterner entre ascendant et descendant
                        sort_state['ascending'] = not sort_state['ascending']
                        items.sort(key=lambda x: extract_number(x[0]), reverse=not sort_state['ascending'])
                        for idx, (val, k) in enumerate(items):
                            tree.move(k, '', idx)
                    return sort_by_col
                self.tree_rev.heading(c, text=c, command=make_sort_handler(self.tree_rev, c))
                self.tree_rev.column(c, width=100, anchor='e')

        # Remplir les lignes par clé (chaque ligne = une catégorie/classe)
        for k in keys_dep:
            row = [k]
            total_k = 0.0
            month_values = {}
            for m in months:
                s = df[(df['Mois'] == m) & (df[group_col] == k) & (df['Type'] == 'Depense')]['Valeur'].sum()
                month_values[m] = s
                total_k += s
            
            # Afficher en pourcentage ou en montant selon l'état du toggle
            if self.show_as_percent:
                grand_total_dep_temp = df[df['Type'] == 'Depense']['Valeur'].sum()
                for m in months:
                    pct = (month_values[m] / grand_total_dep_temp * 100) if grand_total_dep_temp != 0 else 0
                    row.append(f"{pct:.1f}%")
                pct_total = (total_k / grand_total_dep_temp * 100) if grand_total_dep_temp != 0 else 0
                row.append(f"{pct_total:.1f}%")
            else:
                for m in months:
                    row.append(f"{month_values[m]:.2f}")
                row.append(f"{total_k:.2f}")
            
            self.tree_dep.insert('', 'end', iid=f"dep_{k}", values=row)

        # Ligne totaux par mois + total général pour dépense
        total_row = ['Total']
        grand_total_dep = 0.0
        month_totals_dep = {}
        for m in months:
            s = df[(df['Mois'] == m) & (df['Type'] == 'Depense')]['Valeur'].sum()
            month_totals_dep[m] = s
            grand_total_dep += s
        
        if self.show_as_percent:
            for m in months:
                row.append(f"{month_totals_dep[m] / grand_total_dep * 100:.1f}%" if grand_total_dep != 0 else "0.0%")
            total_row.extend([f"{month_totals_dep[m] / grand_total_dep * 100:.1f}%" if grand_total_dep != 0 else "0.0%" for m in months])
            total_row.append("100.0%")
        else:
            total_row.extend([f"{month_totals_dep[m]:.2f}" for m in months])
            total_row.append(f"{grand_total_dep:.2f}")
        
        self.tree_dep.insert('', 'end', iid='__total_dep__', values=total_row)

        for k in keys_rev:
            row = [k]
            total_k = 0.0
            month_values = {}
            for m in months:
                s = df[(df['Mois'] == m) & (df[group_col] == k) & (df['Type'] == 'Revenu')]['Valeur'].sum()
                month_values[m] = s
                total_k += s
            
            # Afficher en pourcentage ou en montant selon l'état du toggle
            if self.show_as_percent:
                grand_total_rev_temp = df[df['Type'] == 'Revenu']['Valeur'].sum()
                for m in months:
                    pct = (month_values[m] / grand_total_rev_temp * 100) if grand_total_rev_temp != 0 else 0
                    row.append(f"{pct:.1f}%")
                pct_total = (total_k / grand_total_rev_temp * 100) if grand_total_rev_temp != 0 else 0
                row.append(f"{pct_total:.1f}%")
            else:
                for m in months:
                    row.append(f"{month_values[m]:.2f}")
                row.append(f"{total_k:.2f}")
            
            self.tree_rev.insert('', 'end', iid=f"rev_{k}", values=row)

        total_row = ['Total']
        grand_total_rev = 0.0
        month_totals_rev = {}
        for m in months:
            s = df[(df['Mois'] == m) & (df['Type'] == 'Revenu')]['Valeur'].sum()
            month_totals_rev[m] = s
            grand_total_rev += s
        
        if self.show_as_percent:
            total_row.extend([f"{month_totals_rev[m] / grand_total_rev * 100:.1f}%" if grand_total_rev != 0 else "0.0%" for m in months])
            total_row.append("100.0%")
        else:
            total_row.extend([f"{month_totals_rev[m]:.2f}" for m in months])
            total_row.append(f"{grand_total_rev:.2f}")
        
        self.tree_rev.insert('', 'end', iid='__total_rev__', values=total_row)
    def on_cell_double(self, event, type_filter=None):
        """Affiche la répartition par l'autre dimension pour la cellule cliquée.

        `type_filter` vaut 'Depense' ou 'Revenu' lorsque le bind l'envoie.
        """
        widget = event.widget
        try:
            item = widget.identify_row(event.y)
            col = widget.identify_column(event.x)
        except Exception:
            return

        if not item or not col:
            return

        col_idx = int(col.replace('#', '')) - 1
        values = widget.item(item, 'values')
        # la première colonne (index 0) est la clé (Categorie/Classe) — ignorer
        if col_idx == 0:
            return

        # Récupérer la clef (nom de la catégorie/classe) depuis la première valeur de la ligne
        key_value = values[0] if values else None
        if not key_value:
            return

        # La colonne correspondante contient le mois (ou 'Total')
        try:
            col_name = widget['columns'][col_idx]
        except Exception:
            return

        # Ignorer la colonne Total
        if col_name == 'Total':
            return

        month = col_name

        # Construire la popup de répartition en respectant le type si fourni
        self.show_breakdown(month, key_value, type_filter)

    def show_breakdown(self, month, key_value, type_filter=None):
        """Affiche la répartition par l'autre dimension pour un mois donné et une valeur de clé.

        Si `type_filter` est fourni ('Depense' ou 'Revenu'), la répartition n'inclut
        que les lignes de ce type.
        """
        if not self.current_compte:
            return

        df = self.current_compte.df.copy()
        df = df.dropna(subset=['Date'])
        df['Mois'] = df['Date'].dt.to_period('M').astype(str)

        group_col = self.view_by
        other_col = 'Classe' if group_col == 'Categorie' else 'Categorie'

        # Filtrer le mois et la clé
        df_m = df[df['Mois'] == month]
        df_k = df_m[df_m[group_col] == key_value]

        # Appliquer le filtre de type si demandé
        if type_filter in ('Depense', 'Revenu'):
            df_k = df_k[df_k['Type'] == type_filter]

        # Répartition par other_col: somme des valeurs (après filtrage)
        if other_col not in df_k.columns or df_k.empty:
            messagebox.showinfo("Répartition", "Aucune donnée disponible pour cette sélection.")
            return

        repart = df_k.groupby(other_col)['Valeur'].sum().sort_values(ascending=False)

        popup = tk.Toplevel(self)
        popup.title(f"Répartition de {key_value} — {month}")
        popup.geometry('420x360')
        # Rendre la popup non-modale pour qu'elle soit indépendante des autres fenêtres
        # popup.transient(self)  # Commenté pour que la popup soit indépendante

        # Valeur totale pour cette sélection (respectant éventuellement le filtre de type)
        sum_value = float(df_k['Valeur'].sum()) if not df_k.empty else 0.0
        type_label = type_filter if type_filter in ('Depense', 'Revenu') else 'Tous'

        header_text = f"{type_label} — {month} — {key_value} : {sum_value:.2f}€"

        # Choisir une couleur selon le type
        if type_label == 'Depense':
            banner_bg = '#C0392B'  # red
        elif type_label == 'Revenu':
            banner_bg = '#27AE60'  # green
        else:
            banner_bg = '#2980B9'  # blue

        # Banner header with colored background and bold white text
        header_frame = tk.Frame(popup, bg=banner_bg)
        header_frame.pack(fill=tk.X)
        header = tk.Label(header_frame, text=header_text, bg=banner_bg, fg='white',
                          font=("Segoe UI", 13, "bold"), pady=8)
        header.pack(side=tk.LEFT, padx=10)

        # Small copy button to copy the total value to clipboard
        def copy_total():
            try:
                popup.clipboard_clear()
                popup.clipboard_append(f"{sum_value:.2f}")
                messagebox.showinfo("Copié", "Valeur copiée dans le presse-papier.")
            except Exception:
                pass

        copy_btn = ttk.Button(header_frame, text='Copier', command=copy_total)
        copy_btn.pack(side=tk.RIGHT, padx=8, pady=6)

        tv = ttk.Treeview(popup, columns=(other_col, 'Montant'), show='headings')
        tv.heading(other_col, text=other_col)
        tv.heading('Montant', text='Montant')
        tv.column(other_col, width=260)
        tv.column('Montant', width=120, anchor='e')
        tv.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        total = repart.sum()

        def populate_tree():
            """Remplit l'arbre avec les valeurs affichées (montant ou %)."""
            for item in tv.get_children():
                tv.delete(item)
            for idx, (name, val) in enumerate(repart.items()):
                if self.show_as_percent:
                    pct = (val / total * 100) if total != 0 else 0
                    tv.insert('', 'end', values=(name, f"{pct:.1f}%"))
                else:
                    pct = (val / total * 100) if total != 0 else 0
                    tv.insert('', 'end', values=(name, f"{val:.2f} ({pct:.1f}%)"))

        # Remplir l'arbre initialement
        populate_tree()

        # Stocker la fonction populate_tree pour pouvoir la mettre à jour si le mode change
        # (on crée un listener passif : la popup se met à jour si l'utilisateur change le mode depuis l'onglet)
        def update_on_mode_change():
            """Vérifie si le mode a changé et remet à jour l'arbre."""
            populate_tree()
            # Rappeler cette fonction dans 500ms pour un refresh continu
            popup.after(500, update_on_mode_change)

        update_on_mode_change()

        btn = ttk.Button(popup, text='Fermer', command=popup.destroy)
        btn.pack(pady=6)