"""
Module Onglet_Tableau - Gestion et affichage du tableau des transactions
Fonctionnalités :
    - Affichage du tableau avec tous les champs et transactions
    - Modification, ajout et suppression de lignes
    - Combobox intelligente avec autocomplétion pour Catégorie, Classe et Type
    - Recherche/filtrage en temps réel
    - Navigation au clavier (Entrée pour valider, Échap pour annuler)
    - Sauvegarde automatique après modifications
    - Affichage des totaux (revenus, dépenses, total)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from datetime import datetime
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


class AutocompleteCombobox(ttk.Combobox):
    """ComboBox avec autocomplétion intelligente."""
    
    def __init__(self, parent, *args, **kwargs):
        # Allow callers to pass enforce_selection to keep compatibility,
        # but default is to NOT force the value to be one of the suggestions.
        self.enforce_selection = kwargs.pop('enforce_selection', False)
        super().__init__(parent, *args, **kwargs)

        self.completion_data = list(self['values'])
        self.bind('<KeyRelease>', self.on_keyrelease)
        # Do not force value on focus out by default
        if not self.enforce_selection:
            self.bind('<FocusOut>', lambda e: None)
    
    def set_completion_data(self, data):
        """Met à jour la liste de complétions."""
        self.completion_data = sorted(list(set(data)))
        self['values'] = self.completion_data
    
    def on_keyrelease(self, event):
        """Filtre les suggestions en fonction de ce qui est écrit."""
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'BackSpace', 'Delete'):
            return
        
        value = self.get()
        if not value:
            self['values'] = self.completion_data
            return
        
        # Filtrer les données qui commencent ou contiennent le texte saisi
        matches = [item for item in self.completion_data 
                   if item.lower().startswith(value.lower())]
        
        if not matches:
            # Si pas de correspondance au début, chercher dans le texte
            matches = [item for item in self.completion_data 
                       if value.lower() in item.lower()]
        
        # Update the dropdown suggestions but do NOT overwrite the user's
        # current typing. This lets the user enter arbitrary/new values while
        # still seeing suggestions.
        self['values'] = matches
        
        # If enforce_selection=True, optionally auto-complete when a single
        # match exists (backwards-compatible behavior).
        if self.enforce_selection and len(matches) == 1:
            cur = self.get()
            self.set(matches[0])
            try:
                self.selection_range(len(cur), tk.END)
            except Exception:
                pass


class Onglet_Tableau(ttk.Frame):
    """Onglet pour afficher et gérer le tableau des transactions."""
    
    def __init__(self, parent, comptes, combo_var):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        self.combo_var = combo_var
        self.current_compte = None
        self.df_display = None  # DataFrame actuellement affiché (filtré ou non)
        self.df_backup = None   # Backup pour annuler les modifications
        # Etat de tri par colonne: True = asc, False = desc
        self._sort_state = {}
        
        # Observer le changement de compte sélectionné
        self.combo_var.trace('w', self.on_account_changed)
        
        self.create_ui()
    
    def create_ui(self):
        """Crée l'interface de l'onglet Tableau."""
        
        # Frame supérieur : Totaux + Recherche
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Totaux à gauche
        totals_frame = tk.Frame(top_frame)
        totals_frame.pack(side=tk.LEFT, padx=5)
        
        self.label_revenus = tk.Label(totals_frame, text="Revenus: 0.00€", font=("Arial", 10, "bold"), fg="green")
        self.label_revenus.pack(side=tk.LEFT, padx=10)
        
        self.label_depenses = tk.Label(totals_frame, text="Depenses: 0.00€", font=("Arial", 10, "bold"), fg="red")
        self.label_depenses.pack(side=tk.LEFT, padx=10)
        
        self.label_total = tk.Label(totals_frame, text="Total: 0.00€", font=("Arial", 10, "bold"), fg="blue")
        self.label_total.pack(side=tk.LEFT, padx=10)
        
        # Recherche à droite
        search_frame = tk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(search_frame, text="Recherche:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Treeview pour afficher les transactions
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Date", "Intitule", "Categorie", "Classe", "Type", "Valeur"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Définir les colonnes
        # Ajouter commande sur les en-têtes pour trier en cliquant
        self.tree.heading("Date", text="Date", command=lambda: self.sort_by_column("Date"))
        self.tree.heading("Intitule", text="Intitule", command=lambda: self.sort_by_column("Intitule"))
        self.tree.heading("Categorie", text="Categorie", command=lambda: self.sort_by_column("Categorie"))
        self.tree.heading("Classe", text="Classe", command=lambda: self.sort_by_column("Classe"))
        self.tree.heading("Type", text="Type", command=lambda: self.sort_by_column("Type"))
        self.tree.heading("Valeur", text="Valeur", command=lambda: self.sort_by_column("Valeur"))
        
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Intitule", width=150, anchor="w")
        self.tree.column("Categorie", width=120, anchor="center")
        self.tree.column("Classe", width=120, anchor="center")
        self.tree.column("Type", width=100, anchor="center")
        self.tree.column("Valeur", width=100, anchor="e")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-clic pour éditer
        self.tree.bind("<Double-1>", self.edit_cell)
        self.tree.bind("<Delete>", self.delete_row)
        
        # Frame inférieur : Boutons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_button = tk.Button(button_frame, text="Ajouter", command=self.add_row)
        add_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = tk.Button(button_frame, text="Supprimer", command=self.delete_selected_row)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        save_button = tk.Button(button_frame, text="Sauvegarder", command=self.save_all)
        save_button.pack(side=tk.LEFT, padx=5)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def on_account_changed(self, *args):
        """Appelé quand le compte sélectionné change."""
        account_name = self.combo_var.get()
        if account_name and account_name in self.comptes:
            self.current_compte = self.comptes[account_name]
            self.refresh_display()
    
    def refresh_display(self):
        """Rafraîchit l'affichage du tableau."""
        if not self.current_compte:
            return
        
        # Charger les données du compte
        self.df_display = self.current_compte.df.copy()
        self.df_backup = self.df_display.copy()
        
        # Appliquer le filtrage de recherche si nécessaire
        search_text = self.search_var.get().strip()
        if search_text:
            # Préparer une vue texte de toutes les colonnes pour une recherche
            df_search = self.df_display.copy()

            # Normaliser les dates en chaînes lisibles pour permettre la recherche
            for col in df_search.columns:
                try:
                    if pd.api.types.is_datetime64_any_dtype(df_search[col].dtype):
                        df_search[col] = df_search[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    # Dans le doute, on laisse la colonne telle quelle
                    pass

            # Remplacer les NA et convertir en chaîne
            df_search = df_search.fillna('').astype(str)

            # Recherche simple de sous-chaîne (pas d'expressions régulières)
            txt = str(search_text)
            mask = df_search.apply(lambda row: row.str.contains(txt, case=False, regex=False).any(), axis=1)
            df_filtered = self.df_display[mask]
        else:
            df_filtered = self.df_display
        
        self.populate_tree(df_filtered)
        self.update_totals()
    
    def on_search_changed(self, *args):
        """Appelé quand le texte de recherche change."""
        self.refresh_display()
    
    def populate_tree(self, df):
        """Remplit le treeview avec les données du dataframe."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for idx, row in df.iterrows():
            values = (row.get("Date", ""), row.get("Intitule", ""), row.get("Categorie", ""),
                     row.get("Classe", ""), row.get("Type", ""), f"{row.get('Valeur', 0):.2f}")
            self.tree.insert("", "end", iid=str(idx), values=values)

    def sort_by_column(self, column_name):
        """Trie l'affichage par une colonne lorsque l'utilisateur clique sur l'en-tête.

        - `Date` est triée en tant que datetime.
        - `Valeur` est triée en tant que numérique.
        - Les autres colonnes sont triées alphabétiquement.
        Le tri bascule entre ascendant/descendant à chaque clic.
        """
        if self.df_display is None:
            return

        # Déterminer l'ordre (toggle)
        prev = self._sort_state.get(column_name, False)
        ascending = not prev

        df = self.df_display.copy()

        try:
            if column_name == "Date":
                # S'assurer que c'est bien du datetime
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                    df = df.sort_values(by="Date", ascending=ascending, na_position='last')
            elif column_name == "Valeur":
                # Convertir en numérique puis trier
                if "Valeur" in df.columns:
                    df["Valeur"] = pd.to_numeric(df["Valeur"], errors='coerce').fillna(0)
                    df = df.sort_values(by="Valeur", ascending=ascending, na_position='last')
            else:
                if column_name in df.columns:
                    df[column_name] = df[column_name].fillna('').astype(str)
                    df = df.sort_values(by=column_name, ascending=ascending, na_position='last')
        except Exception:
            # En cas de problème de format, on tombe sur un tri au niveau string
            try:
                df = df.sort_values(by=column_name, ascending=ascending, na_position='last')
            except Exception:
                pass

        # Mettre à jour l'état et l'affichage
        self._sort_state[column_name] = ascending
        self.populate_tree(df.reset_index(drop=True))
    
    def update_totals(self):
        """Met à jour les totaux affichés."""
        if not self.current_compte:
            self.label_revenus.config(text="Revenus: 0.00€")
            self.label_depenses.config(text="Dépenses: 0.00€")
            self.label_total.config(text="Total: 0.00€")
            return
        
        # Utiliser les champs de la classe Compte qui se recalculent automatiquement
        revenues = self.current_compte.revenus
        expenses = self.current_compte.depenses
        total = revenues - expenses  # Total = revenus - dépenses
        
        self.label_revenus.config(text=f"Revenus: {revenues:.2f}€")
        self.label_depenses.config(text=f"Dépenses: {expenses:.2f}€")
        self.label_total.config(text=f"Total: {total:.2f}€")
    
    def edit_cell(self, event):
        """Édite une cellule."""
        item = self.tree.selection()
        if not item:
            return
        
        item = item[0]
        column = self.tree.identify_column(event.x)
        column_idx = int(column[1:]) - 1  # Convertir '#1' en index 0
        
        if column_idx < 0:
            return
        
        columns = ("Date", "Intitule", "Categorie", "Classe", "Type", "Valeur")
        column_name = columns[column_idx]
        
        # Récupérer la valeur actuelle
        values = self.tree.item(item, "values")
        current_value = values[column_idx]
        
        # Créer une fenêtre d'édition
        self.show_edit_dialog(item, column_name, current_value)
    
    def show_edit_dialog(self, item_id, column_name, current_value):
        """Affiche une fenêtre d'édition pour une cellule."""
        edit_window = tk.Toplevel(self)
        edit_window.title(f"Éditer {column_name}")
        edit_window.geometry("400x150")
        
        tk.Label(edit_window, text=f"Valeur pour {column_name}:", font=("Arial", 10)).pack(pady=10)
        
        if column_name in ["Categorie", "Classe", "Type"]:
            # ComboBox intelligente avec autocomplétion
            var = tk.StringVar(value=current_value)
            
            if column_name == "Categorie":
                suggestions = sorted(set(self.df_display["Categorie"].dropna()))
            elif column_name == "Classe":
                suggestions = sorted(set(self.df_display["Classe"].dropna()))
            else:  # Type
                suggestions = sorted(set(self.df_display["Type"].dropna()))
            
            entry = AutocompleteCombobox(edit_window, textvariable=var, values=suggestions, width=30)
        else:
            var = tk.StringVar(value=current_value)
            entry = tk.Entry(edit_window, textvariable=var, width=30)
        
        entry.pack(pady=10)
        entry.focus()
        entry.select_range(0, tk.END)
        
        def save_edit():
            new_value = var.get()
            self.save_cell_edit(item_id, column_name, new_value)
            edit_window.destroy()
        
        def cancel_edit(event=None):
            edit_window.destroy()
        
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=save_edit, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Annuler", command=cancel_edit, width=10).pack(side=tk.LEFT, padx=5)
        
        # Bind clavier
        entry.bind("<Return>", lambda e: save_edit())
        entry.bind("<Escape>", cancel_edit)
        edit_window.bind("<Escape>", cancel_edit)
    
    def save_cell_edit(self, item_id, column_name, new_value):
        """Sauvegarde la modification d'une cellule."""
        if not self.current_compte:
            return
        
        try:
            row_idx = int(item_id)
            
            # Utiliser la méthode modifier_ligne de la classe Compte
            if column_name == "Valeur":
                self.current_compte.modifier_ligne(row_idx, **{column_name: float(new_value)})
            else:
                self.current_compte.modifier_ligne(row_idx, **{column_name: new_value})
            
            # Rafraîchir l'affichage SANS sauvegarder
            self.refresh_display()
            messagebox.showinfo("Succès", "Modification enregistrée!")
            
        except ValueError:
            messagebox.showerror("Erreur", "Format de valeur invalide!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")
    
    def add_row(self):
        """Ajoute une nouvelle ligne au tableau avec une interface améliorée."""
        if not self.current_compte:
            messagebox.showerror("Erreur", "Aucun compte sélectionné!")
            return
        
        add_window = tk.Toplevel(self)
        add_window.title("Ajouter une transaction")
        add_window.geometry("550x600")
        add_window.resizable(False, False)
        
        # Titre
        title_label = tk.Label(add_window, text="Nouvelle Transaction", font=("Arial", 14, "bold"))
        title_label.pack(pady=15)
        
        # Frame principal avec scrollbar
        canvas = tk.Canvas(add_window)
        scrollbar = ttk.Scrollbar(add_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Variables
        entries = {}
        
        # 1. DATE avec DateEntry (calendrier) ou Entry simple
        date_frame = ttk.LabelFrame(scrollable_frame, text="Date", padding="10")
        date_frame.pack(fill=tk.X, pady=8)
        
        default_date = datetime.now()
        
        if DateEntry is not None:
            date_entry = DateEntry(date_frame, width=25, background='darkblue',
                                    foreground='white', borderwidth=2,
                                    year=default_date.year,
                                    month=default_date.month,
                                    day=default_date.day)
            date_entry.pack(fill=tk.X, padx=10, pady=5)
            entries["Date"] = date_entry
            entries["Date_is_calendar"] = True
        else:
            date_var = tk.StringVar(value=default_date.strftime("%Y-%m-%d"))
            date_entry = tk.Entry(date_frame, textvariable=date_var, width=30, font=("Arial", 11))
            date_entry.pack(fill=tk.X, padx=10, pady=5)
            entries["Date"] = date_var
            entries["Date_is_calendar"] = False
        
        # 2. INTITULÉ
        intitule_frame = ttk.LabelFrame(scrollable_frame, text="Intitulé", padding="10")
        intitule_frame.pack(fill=tk.X, pady=8)
        
        intitule_var = tk.StringVar()
        intitule_entry = tk.Entry(intitule_frame, textvariable=intitule_var, width=30, font=("Arial", 11))
        intitule_entry.pack(fill=tk.X, padx=10, pady=5)
        entries["Intitule"] = intitule_var
        
        # 3. CATÉGORIE - AutocompleteCombobox
        categorie_frame = ttk.LabelFrame(scrollable_frame, text="Catégorie", padding="10")
        categorie_frame.pack(fill=tk.X, pady=8)
        
        categorie_var = tk.StringVar()
        suggestions_cat = sorted(set(self.df_display["Categorie"].dropna())) if "Categorie" in self.df_display.columns else []
        categorie_combo = AutocompleteCombobox(categorie_frame, textvariable=categorie_var, 
                                               values=suggestions_cat, width=27, font=("Arial", 11))
        categorie_combo.pack(fill=tk.X, padx=10, pady=5)
        entries["Categorie"] = categorie_var
        
        # 4. CLASSE - AutocompleteCombobox
        classe_frame = ttk.LabelFrame(scrollable_frame, text="Classe", padding="10")
        classe_frame.pack(fill=tk.X, pady=8)
        
        classe_var = tk.StringVar()
        suggestions_cls = sorted(set(self.df_display["Classe"].dropna())) if "Classe" in self.df_display.columns else []
        classe_combo = AutocompleteCombobox(classe_frame, textvariable=classe_var, 
                                            values=suggestions_cls, width=27, font=("Arial", 11))
        classe_combo.pack(fill=tk.X, padx=10, pady=5)
        entries["Classe"] = classe_var
        
        # 5. TYPE - AutocompleteCombobox
        type_frame = ttk.LabelFrame(scrollable_frame, text="Type", padding="10")
        type_frame.pack(fill=tk.X, pady=8)
        
        type_var = tk.StringVar()
        suggestions_type = sorted(set(self.df_display["Type"].dropna())) if "Type" in self.df_display.columns else []
        type_combo = AutocompleteCombobox(type_frame, textvariable=type_var, 
                                          values=suggestions_type, width=27, font=("Arial", 11))
        type_combo.pack(fill=tk.X, padx=10, pady=5)
        entries["Type"] = type_var
        
        # 6. VALEUR
        valeur_frame = ttk.LabelFrame(scrollable_frame, text="Valeur", padding="10")
        valeur_frame.pack(fill=tk.X, pady=8)
        
        valeur_var = tk.StringVar()
        valeur_entry = tk.Entry(valeur_frame, textvariable=valeur_var, width=30, font=("Arial", 11))
        valeur_entry.pack(fill=tk.X, padx=10, pady=5)
        entries["Valeur"] = valeur_var
        
        # Boutons en bas (FIXE)
        button_frame = tk.Frame(add_window, bg="lightgray")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        
        def save_new_row():
            try:
                # Récupérer la date
                if entries["Date_is_calendar"]:
                    date_obj = entries["Date"].get_date()
                    date_obj = pd.to_datetime(date_obj)
                else:
                    date_str = entries["Date"].get()
                    date_obj = pd.to_datetime(date_str, errors="coerce")
                
                intitule = entries["Intitule"].get()
                categorie = entries["Categorie"].get()
                classe = entries["Classe"].get()
                type_op = entries["Type"].get()
                valeur = float(entries["Valeur"].get())
                
                # Valider les champs obligatoires
                if not intitule:
                    messagebox.showerror("Erreur", "L'intitulé est obligatoire!")
                    return
                
                if pd.isna(date_obj):
                    messagebox.showerror("Erreur", "Date invalide!")
                    return
                
                # Ajouter la ligne
                self.current_compte.ajouter_ligne(date_obj, intitule, categorie, classe, type_op, valeur)
                
                # Rafraîchir l'affichage
                self.refresh_display()
                add_window.destroy()
                messagebox.showinfo("Succès", "Transaction ajoutée!")
                
            except ValueError as e:
                messagebox.showerror("Erreur", f"Format invalide: {str(e)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
        
        def cancel():
            add_window.destroy()
        
        ok_button = tk.Button(button_frame, text="✓ OK", command=save_new_row, 
                             width=15, bg="green", fg="white", font=("Arial", 11, "bold"), 
                             padx=20, pady=10)
        ok_button.pack(side=tk.LEFT, padx=15, pady=10)
        
        cancel_button = tk.Button(button_frame, text="✗ Annuler", command=cancel, 
                                 width=15, bg="red", fg="white", font=("Arial", 11, "bold"),
                                 padx=20, pady=10)
        cancel_button.pack(side=tk.LEFT, padx=15, pady=10)
        
        add_window.bind("<Escape>", lambda e: cancel())
        
        # Focus sur le premier champ
        intitule_entry.focus()
    
    def delete_selected_row(self):
        """Supprime la ligne sélectionnée."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Erreur", "Aucune ligne sélectionnée!")
            return
        
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette transaction?"):
            self.delete_row()
    
    def delete_row(self, event=None):
        """Supprime une ligne."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        try:
            row_idx = int(item_id)
            # Utiliser la méthode supprimer_ligne de la classe Compte
            self.current_compte.supprimer_ligne(row_idx)
            # Rafraîchir SANS sauvegarder
            self.refresh_display()
            messagebox.showinfo("Succès", "Transaction supprimée!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def refresh(self):
        """Rafraîchit l'affichage de l'onglet."""
        self.refresh_display()
    
    def save_all(self):
        """Sauvegarde toutes les modifications dans le fichier Excel."""
        if not self.current_compte:
            messagebox.showerror("Erreur", "Aucun compte sélectionné!")
            return
        
        try:
            self.current_compte.sauvegarder()
            messagebox.showinfo("Succès", "Toutes les modifications ont été sauvegardées!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
