

from Librairie import tk,ttk,pd,DateEntry,dt

class OngletResumer(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.detail_visible = False
        self.build_interface()
        self.update_data_Date()
        

    def build_interface(self):
        # ====== HAUT : filtres de dates alignés ======
        filtre_frame = ttk.Frame(self)
        filtre_frame.pack(pady=10)

        ttk.Label(filtre_frame, text="Date de début :").pack(side="left", padx=5)
        self.start_date = DateEntry(filtre_frame, width=12)
        self.start_date.set_date(self.app.start_date_old)
        self.start_date.pack(side="left")

        ttk.Label(filtre_frame, text="Date de fin :").pack(side="left", padx=5)
        self.end_date = DateEntry(filtre_frame, width=12)
        self.end_date.set_date(self.app.end_date_old)
        self.end_date.pack(side="left")

        # Liaison automatique des changements de dates
        self.start_date.bind("<<DateEntrySelected>>", lambda e: self.update_data_Date())
        self.end_date.bind("<<DateEntrySelected>>", lambda e: self.update_data_Date())

        # ====== CENTRE : résumé principal (gros texte) ======
        self.zone_resume = ttk.Label(self, font=("Arial", 16, "bold"), anchor="center")
        self.zone_resume.pack(pady=20)
        self.max_info_label = ttk.Label(self, text="", font=("Arial", 12, "italic"))
        self.max_info_label.pack(pady=5)

        # ====== BAS : double tableau ======
        self.frame_bas = ttk.Frame(self)
        self.frame_bas.pack(expand=True, fill="both", padx=10, pady=5)

        # Gauche : par catégorie
        self.tree_categorie = ttk.Treeview(self.frame_bas, columns=["Catégorie", "Dépense (€)"], show="headings", height=10)
        self.tree_categorie.heading("Catégorie", text="Catégorie")
        self.tree_categorie.heading("Dépense (€)", text="Dépense (€)")
        self.tree_categorie.column("Dépense (€)", anchor="center")
        self.tree_categorie.pack(side="left", padx=10, fill="y")

        # Droite : par mois
        self.tree_mois = ttk.Treeview(self.frame_bas, columns=["Mois", "Dépense", "Revenu", "Solde"], show="headings", height=10)
        for col in self.tree_mois["columns"]:
            self.tree_mois.heading(col, text=col)
            self.tree_mois.column(col, anchor="center")
        self.tree_mois.pack(side="right", expand=True, fill="both", padx=10)

        # Liaison des événements de sélection
        self.tree_categorie.bind("<<TreeviewSelect>>", self.on_categorie_select)
        self.tree_mois.bind("<<TreeviewSelect>>", self.on_mois_select)

        # ====== Bouton fenêtre latérale ======
        btn = ttk.Button(self, text="Afficher détail par catégorie/mois", command=self.toggle_detail)
        btn.pack(pady=10)
        
        # Frame glissante (invisible au départ)
        self.detail_frame = ttk.Frame(self)
        self.detail_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.detail_frame.pack_forget()  # Caché au départ

    def toggle_detail(self):
        if self.detail_visible:
            self.detail_frame.pack_forget()
        else:
            self.detail_frame.pack(fill="both", expand=False, padx=10, pady=5)
            self.afficher_detail_categorie_mois()
        self.detail_visible = not self.detail_visible

    def update_data_Date(self):
        # Mise à jour de l'intervalle
        self.app.start_date_old = self.start_date.get_date()
        self.app.end_date_old = self.end_date.get_date()

        # Filtrage du DataFrame
        df = self.app.df_original
        self.app.df = df[
            (df['Date'] >= self.app.start_date_old) &
            (df['Date'] <= self.app.end_date_old)
        ]

        self.afficher_resume()
        self.afficher_par_categorie()
        self.afficher_par_mois()
        if self.detail_visible:
            self.afficher_detail_categorie_mois()

    def afficher_resume(self):
        df = self.app.df
        dep = df[df['Type'] == 'Depense']['Valeur'].sum()
        rev = df[df['Type'] == 'Revenu']['Valeur'].sum()
        solde = rev - dep
        self.zone_resume.config(text=f"Revenus : {rev:.2f} €    |    Dépenses : {dep:.2f} €    |    Solde : {solde:.2f} €")

    def afficher_par_categorie(self):
        for row in self.tree_categorie.get_children():
            self.tree_categorie.delete(row)
    
        df = self.app.df.copy()
        if 'Categorie' in df.columns:
            df['Signed'] = df.apply(lambda row: row['Valeur'] if row['Type'] == 'Revenu' else -row['Valeur'], axis=1)
            cat_data = df.groupby("Categorie")["Signed"].sum().sort_values(key=abs, ascending=False)
            for cat, val in cat_data.items():
                self.tree_categorie.insert("", "end", values=(cat, f"{val:.2f}"))

    def afficher_par_mois(self):
        for row in self.tree_mois.get_children():
            self.tree_mois.delete(row)

        df = self.app.df.copy()
        if not df.empty:
            df['Mois'] = pd.to_datetime(df['Date']).dt.to_period("M").astype(str)
            grouped = df.groupby(['Mois', 'Type'])['Valeur'].sum().unstack().fillna(0)
            grouped['Solde'] = grouped.get('Revenu', 0) - grouped.get('Depense', 0)

            for mois, row in grouped.iterrows():
                dep = row.get('Depense', 0)
                rev = row.get('Revenu', 0)
                solde = row.get('Solde', 0)
                self.tree_mois.insert("", "end", values=(mois, f"{dep:.2f}", f"{rev:.2f}", f"{solde:.2f}"))

    def afficher_detail_categorie_mois(self):
        # Nettoyer la frame
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
    
        df = self.app.df.copy()
        if df.empty:
            tk.Label(self.detail_frame, text="Aucune donnée.").pack()
            return
    
        df['Mois'] = pd.to_datetime(df['Date']).dt.to_period("M").astype(str)
        df['Signed'] = df.apply(lambda row: row['Valeur'] if row['Type'] == 'Revenu' else -row['Valeur'], axis=1)
        grouped = df.groupby(['Mois', 'Categorie'])['Signed'].sum().unstack().fillna(0)
    
        colonnes = ['Mois'] + list(grouped.columns)
    
        self.detail_tree = ttk.Treeview(self.detail_frame, columns=colonnes, show="headings")
        for col in colonnes:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, anchor="center", width=100)
        self.detail_tree.pack(fill="both", expand=True)
        self.detail_tree.bind("<<TreeviewSelect>>", self.on_detail_select)
    
        for mois, row in grouped.iterrows():
            valeurs = [mois] + [f"{row[col]:.2f}" for col in grouped.columns]
            self.detail_tree.insert("", "end", values=valeurs)

    def on_categorie_select(self, event):
        selected = self.tree_categorie.selection()
        if not selected:
            return
            
        item = self.tree_categorie.item(selected[0])
        categorie = item['values'][0]
        
        df = self.app.df.copy()
        df = df[df['Categorie'] == categorie]
        self.show_max_transaction(df, f"pour la catégorie {categorie}")

    def on_mois_select(self, event):
        selected = self.tree_mois.selection()
        if not selected:
            return
            
        item = self.tree_mois.item(selected[0])
        mois = item['values'][0]
        
        df = self.app.df.copy()
        df['Mois'] = pd.to_datetime(df['Date']).dt.to_period("M").astype(str)
        df = df[df['Mois'] == mois]
        self.show_max_transaction(df, f"pour le mois {mois}")

    def on_detail_select(self, event):
        selected = self.detail_tree.selection()
        if not selected:
            return
            
        item = self.detail_tree.item(selected[0])
        mois = item['values'][0]
        
        # Obtenir la colonne cliquée de manière plus robuste
        col = self.detail_tree.identify_column(event.x)
        
        # Vérifier que la colonne est valide (commence par # et a un numéro)
        if not col or not col.startswith('#') or len(col) < 2:
            return
        
        try:
            col_index = int(col[1:]) - 1  # On enlève le # et on convertit en index (0-based)
        except ValueError:
            return
        
        # Vérifier si on a cliqué sur une catégorie (col_index > 0)
        if col_index > 0 and col_index < len(self.detail_tree['columns']):
            # Obtenir le nom de la catégorie depuis l'en-tête
            categorie = self.detail_tree['columns'][col_index]
            
            df = self.app.df.copy()
            df['Mois'] = pd.to_datetime(df['Date']).dt.to_period("M").astype(str)
            df = df[(df['Mois'] == mois) & (df['Categorie'] == categorie)]
            self.show_max_transaction(df, f"pour {mois} et {categorie}")
        
        
    def show_max_transaction(self, df, context=""):
        if df.empty:
            self.max_info_label.config(text=f"Aucune donnée {context}")
            return
    
        # Trouver la ligne avec la valeur absolue la plus forte
        df['Abs'] = df['Valeur'].abs()
        max_row = df.loc[df['Abs'].idxmax()]
    
        valeur = max_row['Valeur']
        type_ = max_row['Type']
        Intitule_ = max_row['Intitule']
        categorie = max_row.get('Categorie', 'Inconnue')
        date = max_row['Date']

        self.max_info_label.config(
            text=f" {valeur:.2f} € ({type_}) | Catégorie: {categorie} | Date: {date} | {Intitule_}"
        )