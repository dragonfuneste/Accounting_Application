# -*- coding: utf-8 -*-
"""
Created on Fri May 30 12:43:56 2025

@author: loube
"""



from Librairie import os, shutil, pd,np,tk,ttk,messagebox,simpledialog,filedialog,DateEntry,dt

class OngletTableau(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.df = self.app.df_original.copy()
        self.Tri = False
        self.tree = None
        self.entry_editor = None  # Champ d'édition flottant
        self.selected_column = None
        self.selected_row = None

        self.creation_layout()
    def Tri_collonne(self, column):
        """Trie la colonne et met à jour l'affichage."""
        self.df = self.df.sort_values(by=column, ascending=self.Tri)
        self.Tri = not self.Tri  # Inverse l'ordre du tri
        self.remplir_tableau()  # Met à jour l'affichage

    def creation_layout(self):
        """Création du Treeview et gestion des événements."""
        
                # Barre de recherche
        frame_recherche = ttk.Frame(self)
        frame_recherche.pack(pady=5)
        
        ttk.Label(frame_recherche, text="Rechercher :").pack(side=tk.LEFT, padx=5)
        
        self.entry_recherche = ttk.Entry(frame_recherche)
        self.entry_recherche.pack(side=tk.LEFT, padx=5)
        self.entry_recherche.bind("<KeyRelease>", self.rechercher)  # Met à jour à chaque touche pressée
        
        
        self.tree = ttk.Treeview(self, columns=list(self.df.columns), show='headings')
        for col in self.df.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.Tri_collonne(c))  # Ajout du clic sur l'en-tête

            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Double-clic pour éditer directement une cellule
        self.tree.bind("<Double-1>", self.editer_cellule)

        # Boutons
        bouton_frame = ttk.Frame(self)
        bouton_frame.pack(pady=10)

        ttk.Button(bouton_frame, text="Ajouter", command=self.Ajouter).pack(side=tk.LEFT, padx=5)
        ttk.Button(bouton_frame, text="Supprimer", command=self.Supprimer).pack(side=tk.LEFT, padx=5)
        ttk.Button(bouton_frame, text="Sauvegarder", command=self.Sauvegarder).pack(side=tk.LEFT, padx=5)
        
        
        
        
        self.remplir_tableau()
    def convertir_dates(self):
        """Convertit la colonne 'Date' en datetime de manière sûre."""
        if 'Date' in self.df.columns:
            self.df = self.df.copy()  # S'assurer que ce n'est pas une vue
            self.df.loc[:, 'Date'] = pd.to_datetime(self.df['Date'])  # Utilisation de .loc
        
    def update_tableau(self):
        self.df = self.app.df_original.copy()  
        self.remplir_tableau() 
    def choisir_date(self, valeur_initiale=None):
        """Ouvre une fenêtre popup pour sélectionner une date."""
        popup = tk.Toplevel(self)
        popup.title("Sélectionner une date")
        
        ttk.Label(popup, text="Choisissez une date :").pack(pady=5)
    
        date_picker = DateEntry(popup, width=12, background='darkblue', foreground='white', borderwidth=2)
        
        if valeur_initiale:
            if isinstance(valeur_initiale, str):  
                try:
                    valeur_initiale = dt.strptime(valeur_initiale, "%Y-%m-%d").date()
                except ValueError:
                    pass  # Garde la valeur telle quelle si la conversion échoue
            date_picker.set_date(valeur_initiale)
    
        date_picker.pack(pady=5)
        
        valeur_selectionnee = tk.StringVar()
    
        def valider():
            valeur_selectionnee.set(date_picker.get_date().strftime("%Y-%m-%d"))  # Conversion explicite en texte
            popup.destroy()
    
        ttk.Button(popup, text="Valider", command=valider).pack(pady=10)
    
        popup.wait_window()
        return valeur_selectionnee.get()  # Retourne une date formatée "YYYY-MM-DD"
    
    def editer_cellule(self, event):
        """Permet d’éditer une cellule avec un champ texte ou une liste déroulante pour certaines colonnes."""
        item_id = self.tree.selection()
        if not item_id:
            return
        item_id = item_id[0]
    
        self.selected_row = int(item_id)
        col_id = self.tree.identify_column(event.x)
        self.selected_column = int(col_id[1:]) - 1
    
        valeur_actuelle = self.df.iloc[self.selected_row, self.selected_column]
        x, y, width, height = self.tree.bbox(item_id, self.selected_column)
        colonne_actuelle = self.df.columns[self.selected_column]
    
        if colonne_actuelle.lower() in ["date"]:
            # Ouvre une fenêtre pour choisir une date
            nouvelle_date = self.choisir_date(valeur_actuelle)
            if nouvelle_date:
                self.df.iloc[self.selected_row, self.selected_column] = nouvelle_date
                self.remplir_tableau()  # Mise à jour immédiate du tableau
                self.convertir_dates()
                if not pd.api.types.is_datetime64_any_dtype(self.df['Date']):
                    self.df.loc[:, 'Date'] = pd.to_datetime(self.df['Date'], errors='coerce')  # 'coerce' pour gérer les formats invalides
    
        elif colonne_actuelle.lower() in ["categorie", "classe", "type"]:
            valeurs_existantes = self.df[colonne_actuelle].dropna().unique().tolist()
    
            self.entry_editor = ttk.Combobox(self.tree, values=valeurs_existantes)
            self.entry_editor.place(x=x, y=y, width=width, height=height)
            self.entry_editor.set(valeur_actuelle)
            self.entry_editor.focus()
    
            self.entry_editor.bind("<<ComboboxSelected>>", self.valider_modification)
            self.entry_editor.bind("<Return>", self.valider_modification)
    
        else:
            self.entry_editor = tk.Entry(self.tree)
            self.entry_editor.place(x=x, y=y, width=width, height=height)
            self.entry_editor.insert(0, valeur_actuelle)
            self.entry_editor.focus()
            self.entry_editor.bind("<Return>", self.valider_modification)
            self.entry_editor.bind("<Escape>", self.annuler_modification)
            self.tree.bind("<Button-1>", self.annuler_si_clique_exterieur)
    
        self.remplir_tableau()

                
        # Mise à jour immédiate de l'affichage
        self.remplir_tableau()
    def annuler_modification(self, event):
        """Annule la modification et restaure la valeur initiale."""
        self.entry_editor.destroy()  # Supprime le champ d'édition
        self.entry_editor = None  # Réinitialise l'éditeur
        self.remplir_tableau()  # Met à jour le tableau sans modification
    
    def annuler_si_clique_exterieur(self, event):
        """Annule la modification si l'utilisateur clique en dehors du champ d'édition."""
        if self.entry_editor:
            self.entry_editor.destroy()
            self.entry_editor = None
            self.remplir_tableau()
    def valider_modification(self, event):
        """Enregistre la modification et met à jour le tableau en gérant les types correctement."""
        new_value = self.entry_editor.get()
    
        # Vérifie si la colonne contient des nombres et convertit la valeur
        colonne_actuelle = self.df.columns[self.selected_column]
        if pd.api.types.is_numeric_dtype(self.df[colonne_actuelle]):
            try:
                new_value = float(new_value)  # Convertit en float
            except ValueError:
                messagebox.showerror("Erreur", f"Valeur invalide pour la colonne {colonne_actuelle}")
                return  # Annule la modification en cas d'erreur de conversion
    
        self.df.iloc[self.selected_row, self.selected_column] = new_value
        self.entry_editor.destroy()
        self.entry_editor = None
        self.remplir_tableau()

    def Ajouter(self):
        """Ajoute une ligne vide en haut du tableau pour une modification manuelle."""
        nouvelles_valeurs = [""] * len(self.df.columns)  # Crée une ligne vide
        
        # Demander la date via le calendrier
        if "Date" in self.df.columns:
            nouvelles_valeurs[self.df.columns.get_loc("Date")] = self.choisir_date()
            self.convertir_dates()
            if not pd.api.types.is_datetime64_any_dtype(self.df['Date']):
                self.df.loc[:, 'Date'] = pd.to_datetime(self.df['Date'], errors='coerce')  # 'coerce' pour gérer les formats invalides
        nouvelle_ligne = pd.DataFrame([nouvelles_valeurs], columns=self.df.columns)
    
        # Ajoute la ligne en tête du DataFrame
        self.df = pd.concat([nouvelle_ligne, self.df], ignore_index=True)
    
        # Mise à jour de l'affichage
        self.remplir_tableau()
    def Supprimer(self):
        item_id = self.tree.selection()  
        if not item_id:
            return
        item_id = int(item_id[0]) 
    
        
        self.df.drop(index=item_id, inplace=True)
        self.df.reset_index(drop=True, inplace=True)  
    
        
        self.remplir_tableau()
    
        print(f"Ligne supprimée, ID : {item_id}")
    
    def get_Champs_de_collonne(self, column_name):
        """Retourne les valeurs uniques d'une colonne"""
        return sorted(self.df[column_name].dropna().unique().tolist())
    

    def rechercher(self, event=None):
        """Filtre les résultats du tableau en fonction du texte entré sans modifier le DataFrame original."""
        mot_cle = self.entry_recherche.get().strip().lower()
        
        if not mot_cle:
            # Affiche toutes les données si le champ de recherche est vide
            self.remplir_tableau(self.app.df_original.copy())
        else:
            # Filtre le DataFrame original pour l'affichage uniquement
            df_filtre = self.app.df_original[
                self.app.df_original.apply(lambda row: row.astype(str).str.contains(mot_cle, case=False, na=False).any(), axis=1)
            ]
            self.remplir_tableau(df_filtre)

    def remplir_tableau(self, df=None):
        """Remplit le tableau avec les données du DataFrame fourni ou de self.df par défaut."""
        if df is None:
            df = self.df
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, row in df.iterrows():
            self.tree.insert("", "end", values=list(row), iid=str(i))  # ID = index du DataFrame
    
    def Sauvegarder(self):
        """Sauvegarde le fichier sous forme de backup et met à jour l'original."""
        source = self.app.current_account  # Nom du fichier source
        dest = f"./backup/backup_{source}"  # Fichier de sauvegarde dans le dossier backup
        
        os.makedirs("./backup", exist_ok=True)  # Assure l'existence du dossier backup
        
        # Lire le fichier source s'il existe
        try:
            df_source = pd.read_excel(source, engine="openpyxl")
        except FileNotFoundError:
            df_source = pd.DataFrame(columns=self.df.columns)  # Crée un DataFrame vide si le fichier n'existe pas
        
        # Sauvegarde l'ancien fichier
        df_source.to_excel(dest, index=False)
    
        # Met à jour le fichier source avec les données originales (self.df)
        self.df.to_excel(source, index=False)
    
        self.app.load_all_data()
        messagebox.showinfo("Succès", f"Sauvegarde réussie :\nOriginal: {source}\nBackup: {dest}")