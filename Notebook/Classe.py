# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 21:01:08 2025

@author: loube
"""
import os
import shutil
import pandas as pd

from Fonction import *

class Compte:
    """
    Classe qui gère un compte :
     - chemin du tableau de compte
     - un nom
     - un état : ouvert/clos/pending
     - un nombre de backup
     - un tableau de compte actif
     - un tableau de compte prévisionnel.
    """
    def __init__(self, chemin_,state_="open", back_up_=0):
        # ERROR HANDLER
        if not os.path.exists(chemin_):
            raise FileNotFoundError(f"❌ Le chemin '{chemin_}' n'existe pas.")
        if not os.path.isfile(chemin_):
            raise ValueError(f"❌ Le chemin '{chemin_}' n'est pas un fichier valide.")
        if not (chemin_.lower().endswith(".xlsx") or chemin_.lower().endswith(".xls")):
            raise ValueError(f"❌ Le fichier '{chemin_}' n'est pas un fichier Excel (.xlsx ou .xls).")

        self.chemin = chemin_
        self.name = os.path.splitext(os.path.basename(chemin_))[0]
        self.state = state_
        self.back_up = back_up_

        # Tableaux de comptes
        self.compte_actif = pd.DataFrame()
        self.compte_previsionnel = pd.DataFrame()

        # --- Chemin du prévisionnel dans ./prev/
        dossier_parent = os.path.dirname(self.chemin)               # D:/Fichier/GitHub/Python_Budget/Notebook/CSV
        dossier_prev = os.path.join(dossier_parent, "prev")         # D:/.../CSV/prev
        os.makedirs(dossier_prev, exist_ok=True)                    # crée le dossier si nécessaire
        
        self.chemin_previsionnel = os.path.join(
            dossier_prev,
            f"{self.name}_prev.xlsx"                                # Livret_Bleu_prev.xlsx
        )

        
        # Chargement Excel actif
        self.load_compte()

    




    def load_compte(self):
        """Charge le compte actif + le compte prévisionnel associé (création si nécessaire)."""
        try:
            self.compte_actif = pd.read_excel(self.chemin)
        except Exception as e:
            raise RuntimeError(f"❌ Erreur lors du chargement du compte actif : {e}")
    
        if os.path.exists(self.chemin_previsionnel):
            try:
                self.compte_previsionnel = pd.read_excel(self.chemin_previsionnel)
            except Exception as e:
                raise RuntimeError(f"❌ Erreur lors du chargement du prévisionnel : {e}")
        else:
            if self.state == "open":
                # Si actif a des colonnes -> on copie, sinon colonnes par défaut
                if not self.compte_actif.empty:
                    self.compte_previsionnel = pd.DataFrame(columns=self.compte_actif.columns)
                else:
                    self.compte_previsionnel = pd.DataFrame(
                        columns=["Date", "Type", "Categorie", "Description", "Montant"]
                    )
                self.save_previsionnel()
            else:
                self.compte_previsionnel = pd.DataFrame(
                    columns=["Date", "Type", "Categorie", "Description", "Montant"]
                )

    def save_compte_actif(self):
        """
        Sauvegarde le compte actif :
         - fait un backup des versions précédentes
         - écrit l'état actuel dans le fichier original
        """
        if self.state == "open":
            backup_dir = "./backup"
            os.makedirs(backup_dir, exist_ok=True)

            # Décaler les backups existants
            for i in range(self.back_up, 0, -1):
                old_file = os.path.join(backup_dir, f"{self.name}_backup{i}.xlsx")
                new_file = os.path.join(backup_dir, f"{self.name}_backup{i+1}.xlsx")
                if os.path.exists(old_file):
                    shutil.move(old_file, new_file)

            # Sauvegarde actuelle en backup1
            shutil.copy2(self.chemin, os.path.join(backup_dir, f"{self.name}_backup1.xlsx"))

            # Réécrire le fichier courant avec l’état actuel
            try:
                self.compte_actif = trier_tableau(self.compte_actif, "Date", croissant=False)
                self.compte_actif.to_excel(self.chemin, index=False)
            except Exception as e:
                raise RuntimeError(f"❌ Erreur lors de la sauvegarde Excel : {e}")

            return "✅ Sauvegarde effectuée avec succès"
        else:
            return f"⚠️ Impossible de sauvegarder : compte en état '{self.state}'"

    def save_previsionnel(self):
        """
        Sauvegarde le compte prévisionnel dans le fichier associé.
        """
        if self.state == "open":
            try:
                self.compte_previsionnel = trier_tableau(self.compte_previsionnel, "Date", croissant=False)
                self.compte_previsionnel.to_excel(self.chemin_previsionnel, index=False)
                return "✅ Prévisionnel sauvegardé avec succès"
            except Exception as e:
                raise RuntimeError(f"❌ Erreur lors de la sauvegarde du prévisionnel : {e}")
        else:
            return f"⚠️ Impossible de sauvegarder : compte en état '{self.state}'"

    def __repr__(self):
        infos = f"<Compte name={self.name}, state={self.state}, lignes={len(self.compte_actif)}"
    
        if not self.compte_actif.empty:
            infos += f", colonnes={list(self.compte_actif.columns)}"
            if "Date" in self.compte_actif.columns:
                try:
                    dates = pd.to_datetime(self.compte_actif["Date"], errors="coerce").dropna()
                    if not dates.empty:
                        first_date = dates.min().date()
                        last_date = dates.max().date()
                        infos += f", première_date={first_date}, dernière_date={last_date}"
                except Exception:
                    infos += ", ⚠️ erreur conversion dates"
            else: 
                infos += ", ⚠️ aucune colonne 'Date'"
        infos += ">"
        return infos




class Comptabilité:
    def __init__(self, chemin_txt):
        if not os.path.exists(chemin_txt):
            raise FileNotFoundError(f"❌ Le fichier '{chemin_txt}' n'existe pas.")
        if not os.path.isfile(chemin_txt):
            raise ValueError(f"❌ Le chemin '{chemin_txt}' n'est pas un fichier valide.")

        self.chemin_txt = chemin_txt
        self.comptes = []
        self.erreurs = []  # liste pour stocker les erreurs

        self._load_comptes()

    def _load_comptes(self):
        """Charge tous les comptes depuis le fichier texte"""
        self.comptes.clear()
        self.erreurs.clear()

        with open(self.chemin_txt, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    chemin, etat = line.split(maxsplit=1)
                except ValueError:
                    self.erreurs.append((line, "Format invalide"))
                    continue

                try:
                    c = Compte(chemin)
                    c.state = etat
                    self.comptes.append(c)
                except Exception as e:
                    self.erreurs.append((chemin, str(e)))

    def ajouter_compte(self, chemin_compte, etat="open"):
        """
        Ajoute un compte dans le fichier txt et crée l'Excel si nécessaire.
        Vérifie qu'aucun compte existant n'a déjà le même nom.
        """
        # Extraire juste le nom du fichier (sans extension)
        nouveau_nom = os.path.splitext(os.path.basename(chemin_compte))[0]
    
        # Vérifier si ce nom existe déjà dans les comptes chargés
        for c in self.comptes:
            if c.name == nouveau_nom:
                raise ValueError(f"❌ Le compte '{nouveau_nom}' existe déjà (lié à {c.chemin})")
    
        # Création du fichier Excel si inexistant
        if not os.path.exists(chemin_compte):
            print(f"⚠️ Le fichier {chemin_compte} n'existe pas → création.")
            df = pd.DataFrame(columns=["Date", "Description", "Débit", "Crédit"])
            try:
                df.to_excel(chemin_compte, index=False)
            except Exception as e:
                raise RuntimeError(f"❌ Impossible de créer le fichier Excel '{chemin_compte}' : {e}")
    
        # Ajout dans le .txt
        with open(self.chemin_txt, "a", encoding="utf-8") as f:
            f.write(f"{chemin_compte} {etat}\n")
    
        # Recharge les comptes
        self._load_comptes()

    def supprimer_compte(self, identifiant, supprimer_fichier=True):
        """
        Supprime un compte du fichier txt et (optionnellement) son Excel associé
        + son prévisionnel situé dans ./prev/.
    
        Args:
            identifiant (str): nom du compte (ex: "Compte_Epargne")
                               ou chemin complet (ex: "D:/.../Compte_Epargne.xlsx")
            supprimer_fichier (bool): True = supprime aussi les fichiers Excel (actif + prévisionnel),
                                      False = garde les fichiers sur disque
        """
        lignes_modifiees = []
        chemin_excel = None
        trouve = False
    
        # Normaliser si identifiant est un chemin
        ident_nom = os.path.splitext(os.path.basename(identifiant))[0]
    
        # Lire le fichier txt et supprimer la ligne correspondante
        with open(self.chemin_txt, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    lignes_modifiees.append(line)
                    continue
    
                chemin, etat = line.strip().split(maxsplit=1)
                name = os.path.splitext(os.path.basename(chemin))[0]
    
                if name == ident_nom or chemin == identifiant:
                    trouve = True
                    chemin_excel = chemin
                    continue  # on ne réécrit pas cette ligne
                else:
                    lignes_modifiees.append(line)
    
        if not trouve:
            raise ValueError(f"❌ Aucun compte trouvé avec '{identifiant}'")
    
        # Réécriture du fichier txt (sans le compte supprimé)
        with open(self.chemin_txt, "w", encoding="utf-8") as f:
            f.writelines(lignes_modifiees)
    
        # Suppression fichiers si demandé
        if supprimer_fichier and chemin_excel:
            try:
                # Supprime le fichier Excel actif
                if os.path.exists(chemin_excel):
                    os.remove(chemin_excel)
    
                # Supprime le prévisionnel associé
                dossier_prev = os.path.join(os.path.dirname(chemin_excel), "prev")
                chemin_prev = os.path.join(
                    dossier_prev,
                    f"{os.path.splitext(os.path.basename(chemin_excel))[0]}_prev.xlsx"
                )
                if os.path.exists(chemin_prev):
                    os.remove(chemin_prev)
    
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression des fichiers : {e}")
    
        # Recharge les comptes
        self._load_comptes()



    def changer_etat(self, nom_compte, nouvel_etat):
        """Change l'état d’un compte existant (et dans le fichier txt)"""
        trouve = False
        lignes_modifiees = []
        with open(self.chemin_txt, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    lignes_modifiees.append(line)
                    continue

                chemin, etat = line.strip().split(maxsplit=1)
                name = os.path.splitext(os.path.basename(chemin))[0]

                if name == nom_compte:
                    lignes_modifiees.append(f"{chemin} {nouvel_etat}\n")
                    trouve = True
                else:
                    lignes_modifiees.append(line)

        if not trouve:
            raise ValueError(f"❌ Aucun compte trouvé avec le nom '{nom_compte}'")

        # Réécriture du fichier txt
        with open(self.chemin_txt, "w", encoding="utf-8") as f:
            f.writelines(lignes_modifiees)

        # Recharge la liste des comptes
        self._load_comptes()

    def __repr__(self):
        return (f"<Comptabilité: {len(self.comptes)} comptes valides, "
                f"{len(self.erreurs)} erreurs>")

    def lister_comptes(self):
        return [f"{c.name} ({c.state})" for c in self.comptes]

    def lister_erreurs(self):
        return [f"{chemin} -> {err}" for chemin, err in self.erreurs]
