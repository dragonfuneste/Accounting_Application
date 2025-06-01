# -*- coding: utf-8 -*-
"""
Created on Sun Jun  1 18:37:21 2025

@author: loube
"""

import openpyxl
import os

def Detecter_Compte(self,directory):
    """
    Retourne une liste des fichiers .xlsx présents dans le dossier spécifié.

    :param directory: Chemin du dossier à explorer
    :return: Liste des noms de fichiers .xlsx
    """
    return [f for f in os.listdir(directory) if f.endswith('.xlsx') and os.path.isfile(os.path.join(directory, f))]


def creer_fichier_xlsx(self,nom_fichier):
    """
    Crée un fichier .xlsx avec des colonnes : Date, Intitule, Categorie, Classe, Type, Valeur.

    :param nom_fichier: Nom du fichier à créer (avec ou sans extension .xlsx)
    """
    if not nom_fichier.endswith('.xlsx'):
        nom_fichier += '.xlsx'
    
    # Créer un classeur et une feuille active
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Feuille1"

    # Ajouter les en-têtes de colonnes
    colonnes = ["Date", "Intitule", "Categorie", "Classe", "Type", "Valeur"]
    ws.append(colonnes)

    # Sauvegarder le fichier
    wb.save(nom_fichier)
    print(f"Fichier créé : {nom_fichier}")

def supprimer_fichier_xlsx(self,nom_fichier):
    """
    Supprime un fichier .xlsx donné s'il existe.

    :param nom_fichier: Nom du fichier à supprimer (avec ou sans extension .xlsx)
    """
    if not nom_fichier.endswith('.xlsx'):
        nom_fichier += '.xlsx'
    
    if os.path.isfile(nom_fichier):
        os.remove(nom_fichier)
        print(f"Fichier supprimé : {nom_fichier}")
    else:
        print(f"Fichier non trouvé : {nom_fichier}")

# Exemple d'utilisation :
chemin_dossier = "./"  # ou un chemin absolu comme "C:/Users/TonNom/Documents"
fichiers_xlsx = detect_xlsx_files(chemin_dossier)
print("Fichiers .xlsx trouvés :", fichiers_xlsx)




creer_fichier_xlsx("Test")
fichiers_xlsx = detect_xlsx_files(chemin_dossier)
print("Fichiers .xlsx trouvés :", fichiers_xlsx)



supprimer_fichier_xlsx(fichiers_xlsx[-1])
fichiers_xlsx = detect_xlsx_files(chemin_dossier)
print("Fichiers .xlsx trouvés :", fichiers_xlsx)
