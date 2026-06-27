import sqlite3

def migrer_base_complete(ancienne_db_path, nouvelle_db_path):
    try:
        old_conn = sqlite3.connect(ancienne_db_path)
        new_conn = sqlite3.connect(nouvelle_db_path)
        
        # 1. Nettoyage
        new_conn.execute("DROP TABLE IF EXISTS transactions")
        new_conn.execute("DROP TABLE IF EXISTS comptes")
        
        # 2. Création de la structure
        new_conn.execute("""
            CREATE TABLE comptes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_compte TEXT UNIQUE,
                metadata TEXT
            )
        """)
        
        new_conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compte_id INTEGER,
                date TEXT,
                intitule TEXT,
                categorie TEXT,
                classe TEXT,
                est_revenu BOOLEAN,  -- 1 pour Revenu, 0 pour Dépense
                valeur REAL,
                FOREIGN KEY(compte_id) REFERENCES comptes(id)
            )
        """)
        
        # 3. Migration des comptes
        cursor_meta = old_conn.execute("SELECT * FROM _metadata_accounts")
        for meta in cursor_meta.fetchall():
            new_conn.execute("INSERT INTO comptes (nom_compte, metadata) VALUES (?, ?)", 
                           (meta[0], str(meta[1:])))
        
        # 4. Migration des transactions
        tables_comptes = ['CH_compte_courant', 'Compte_Courant', 'Compte_Jeune', 'Livret_Bleu']
        
        for table_name in tables_comptes:
            compte_data = new_conn.execute("SELECT id FROM comptes WHERE nom_compte = ?", (table_name,)).fetchone()
            
            if compte_data:
                compte_id = compte_data[0]
                # On récupère les données
                data = old_conn.execute(f"SELECT Date, Intitule, Categorie,Classe, Type, Valeur FROM {table_name}")
                
                for row in data.fetchall():
                    # Transformation : 'Revenu' devient 1, tout le reste (Dépense) devient 0
                    is_revenu = 1 if row[4].strip().lower() == 'revenu' else 0
                    
                    new_conn.execute("""
                        INSERT INTO transactions (compte_id, date, intitule, categorie,classe, est_revenu, valeur)
                        VALUES (?, ?, ?, ?,?, ?, ?)
                    """, (compte_id, row[0], row[1], row[2],row[3], is_revenu, row[5]))
            else:
                print(f"Attention : Compte '{table_name}' non trouvé.")
        
        new_conn.commit()
        print("Migration et normalisation des types réussies !")
        
    except sqlite3.Error as e:
        print(f"Erreur lors de la migration : {e}")
    finally:
        old_conn.close()
        new_conn.close()

migrer_base_complete('_data/Compte.db', '_data/Compte_rework.db')