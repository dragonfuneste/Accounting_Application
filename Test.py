import sqlite3
from Comptabilite import Comptabilite
compta = Comptabilite("_data/Compte_rework.db")
account = compta.list_all_accounts()

print(account[1].get_account_stats())


