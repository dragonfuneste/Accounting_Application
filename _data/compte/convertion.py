import pandas as pd
import sqlite3
import os

def create_perfect_db(db_name="Compte.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 1. Création et Remplissage à la main de _metadata_accounts
    print("--- Création de la table _metadata_accounts (Manuel) ---")
    cursor.execute("DROP TABLE IF EXISTS _metadata_accounts")
    cursor.execute('''
        CREATE TABLE _metadata_accounts (
            account_name TEXT,
            devise TEXT,
            state INTEGER
        )
    ''')

    # On définit ici tes comptes exactement comme ils apparaissent dans MaCompta_Test
    accounts_data = [
        ('Compte_Courant', 'EUR', 1),
        ('Compte_Jeune', 'EUR', 1),
        ('Livret_Bleu', 'EUR', 1),
        ('CH_Compte_Courant', 'CHF', 1)
    ]
    
    cursor.executemany("INSERT INTO _metadata_accounts VALUES (?, ?, ?)", accounts_data)
    conn.commit()
    print(f"✅ Table _metadata_accounts remplie avec {len(accounts_data)} comptes.")

    # 2. Traitement des fichiers Excel pour les tables de données
    files_in_dir = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    
    for file_name in files_in_dir:
        table_name = os.path.splitext(file_name)[0]
        print(f"--- Traitement de la table : {table_name} ---")
        
        try:
            df = pd.read_excel(file_name)
            # Conversion forcée de la colonne Valeur en nombre (REAL)
            if 'Valeur' in df.columns:
                df['Valeur'] = pd.to_numeric(df['Valeur'], errors='coerce')

            # Format de date propre (YYYY-MM-DD)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

            # Export vers la table correspondante
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ Table '{table_name}' ajoutée avec {len(df)} lignes.")

        except Exception as e:
            print(f"⚠️ Erreur lors de l'import de {file_name} : {e}")

    conn.close()
    print(f"\n🚀 Terminé ! Ta base '{db_name}' est maintenant prête et remplie.")

if __name__ == "__main__":
    create_perfect_db()