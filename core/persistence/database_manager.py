# database_manager.py
import logging
from .database import Database
from .account_loader import load_comptabilite
from .account_saver import save_comptabilite

# Importation des nouveaux modules
from core.models.project import Projects
from core.services.project_management import ProjectManagement

class DatabaseManager:
    def __init__(self, db_name, projects_json_path=""):
        # 1. Initialise la DB SQLite
        self.db = Database(db_name)
        
        # 2. Charge la comptabilité (SQL)
        self.comptabilite = load_comptabilite(self.db)
        
        # 3. Charge les projets (JSON)
        self.projects = Projects(projects_json_path)
        
        # 4. Initialise le moteur de calcul (Project Management)
        # On lui passe les deux sources de données dont il a besoin
        self.project_management = ProjectManagement(self.projects, self.comptabilite)

    def save(self):
        # Sauvegarde de la compta
        for compte in self.comptabilite.liste_compte: 
            compte.triage("Date", True)
        save_comptabilite(self.db, self.comptabilite)
        
        # Sauvegarde des projets
        self.projects.save()
        print("Save successful (DB + Projects)")