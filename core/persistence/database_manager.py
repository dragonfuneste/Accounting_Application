import logging
from .database import Database
from .account_loader import load_comptabilite
from .account_saver import save_comptabilite

class DatabaseManager:
    def __init__(self, db_name):
        self.db = Database(db_name)
        self.comptabilite = load_comptabilite(self.db)

    def save(self):
        for compte in self.comptabilite.liste_compte : 
            compte.triage("Date",True)
        save_comptabilite(self.db, self.comptabilite)
