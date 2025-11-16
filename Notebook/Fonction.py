# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 19:33:12 2025

@author: loube

LA ou se trouve tout un tas de fonction utile réutiliseable 
"""
import pandas as pd
import numpy as np
from datetime import datetime
"""
Filtrage
"""
# Par date

def filtrer_par_date(tab, date_debut, date_fin):
    """
    Filtrer entre deux dates précises (jour/mois/année)
    """
    tab["Date"] = pd.to_datetime(tab["Date"])
    date_debut = pd.to_datetime(date_debut)
    date_fin = pd.to_datetime(date_fin)

    min_date = tab["Date"].min()
    max_date = tab["Date"].max()

    if date_debut < min_date:
        date_debut = min_date
    if date_fin > max_date:
        date_fin = max_date

    return tab[(tab["Date"] >= date_debut) & (tab["Date"] <= date_fin)].reset_index(drop=True)


def filtrer_par_mois(tab, mois_debut, mois_fin):
    """
    Filtrer entre deux mois (ignorer les jours, mais prendre l'année en compte)
    Paramètres : datetime avec jour ignoré
    """
    tab["Date"] = pd.to_datetime(tab["Date"])
    mois_debut = pd.to_datetime(mois_debut).to_period("M")
    mois_fin = pd.to_datetime(mois_fin).to_period("M")

    min_mois = tab["Date"].min().to_period("M")
    max_mois = tab["Date"].max().to_period("M")

    if mois_debut < min_mois:
        mois_debut = min_mois
    if mois_fin > max_mois:
        mois_fin = max_mois

    return tab[(tab["Date"].dt.to_period("M") >= mois_debut) & (tab["Date"].dt.to_period("M") <= mois_fin)].reset_index(drop=True)


def filtrer_par_annee(tab, annee_debut, annee_fin):
    """
    Filtrer entre deux années (ignorer mois et jours)
    Paramètres : datetime (seule l'année est utilisée)
    """
    tab["Date"] = pd.to_datetime(tab["Date"])
    annee_debut = pd.to_datetime(annee_debut).year
    annee_fin = pd.to_datetime(annee_fin).year

    min_annee = tab["Date"].dt.year.min()
    max_annee = tab["Date"].dt.year.max()

    if annee_debut < min_annee:
        annee_debut = min_annee
    if annee_fin > max_annee:
        annee_fin = max_annee

    return tab[
        (tab["Date"].dt.year >= annee_debut) &
        (tab["Date"].dt.year <= annee_fin)
    ].reset_index(drop=True)

# Filtre 
def filtrer(tab1, colonne, valeur):
    """
    Filtre le DataFrame selon une colonne et une valeur,
    avec tolérance (insensible à la casse + recherche partielle).
    
    Paramètres
    ----------
    tab : pd.DataFrame
        Le tableau à filtrer
    colonne : str
        Le nom de la colonne ("Intitule", "Categorie", "Classe", "Type")
    valeur : str ou liste
        La valeur ou liste de valeurs à rechercher (partiellement tolérant)
    
    Retour
    ------
    pd.DataFrame filtré
    """
    # Normaliser en texte minuscule
    tab = tab1.copy()
    tab.loc[:, colonne] = tab[colonne].astype(str)   # ✅ plus de warning
    
    if colonne not in tab.columns:
        raise ValueError(f"Colonne '{colonne}' inexistante. Colonnes dispo : {list(tab.columns)}")
    

    
    if isinstance(valeur, str):
        masque = tab[colonne].str.lower().str.contains(valeur.lower(), na=False)
        return tab[masque].reset_index(drop=True)
    
    elif isinstance(valeur, (list, tuple, set)):
        masque = False
        for v in valeur:
            masque |= tab[colonne].str.lower().str.contains(str(v).lower(), na=False)
        return tab[masque].reset_index(drop=True)
    
    else:
        raise ValueError("Le paramètre 'valeur' doit être une chaîne ou une liste de chaînes")


"""
Trier
"""
def trier_tableau(tab, colonnes, croissant=True):

    if isinstance(colonnes, str):
        colonnes = [colonnes]
    for col in colonnes:
        if col not in tab.columns:
            raise ValueError(f"Colonne '{col}' inexistante. Colonnes dispo : {list(tab.columns)}")

    if isinstance(croissant, bool):
        croissant = [croissant] * len(colonnes)

    return tab.sort_values(by=colonnes, ascending=croissant).reset_index(drop=True)


"""
Calculer la somme cumulé 
"""

def Cummuler_Name(tab, colonne=None, valeurs=None):
    """
    Cumule Revenu / Dépense / Ecart soit globalement,
    soit par valeur d'une colonne donnée.
    Ajoute aussi les moyennes mensuelles.

    Paramètres
    ----------
    tab : pd.DataFrame
        Tableau contenant les données
    colonne : str ou None
        Nom de la colonne pour regrouper (ex: "Categorie", "Classe", "Intitule")
        Si None → calcule uniquement le global.
    valeurs : list ou None
        Liste des valeurs à prendre en compte (si colonne spécifiée).
        Si None → toutes les valeurs uniques de la colonne.

    Retour
    ------
    pd.DataFrame avec colonnes 
    ["Nom", "Revenu", "Depense", "Ecart", "Revenu_moy", "Depense_moy", "Ecart_moy"]
    """
    tab["Type"] = tab["Type"].str.lower()
    tab["Date"] = pd.to_datetime(tab["Date"])

    # Nombre de mois distincts dans les données
    nb_mois = tab["Date"].dt.to_period("M").nunique()

    resultats = []

    if colonne is None:
        revenu = round(tab[tab["Type"] == "revenu"]["Valeur"].sum(),2)
        depense = round(tab[tab["Type"] == "depense"]["Valeur"].sum(),2)
        ecart = round(revenu - depense,2)

        resultats.append({
            "Nom": "GLOBAL",
            "Revenu": revenu,
            "Depense": depense,
            "Ecart": ecart,
            "Revenu_moy": revenu / nb_mois,
            "Depense_moy": depense / nb_mois,
            "Ecart_moy": ecart / nb_mois
        })

    else:
        if valeurs is None:
            valeurs = tab[colonne].unique()

        for v in valeurs:
            sous_tab = tab[tab[colonne] == v]
            revenu = sous_tab[sous_tab["Type"] == "revenu"]["Valeur"].sum()
            depense = sous_tab[sous_tab["Type"] == "depense"]["Valeur"].sum()
            ecart = revenu - depense

            resultats.append({
                f"{colonne}": v,
                "Revenu": revenu,
                "Depense": depense,
                "Ecart": ecart,
                "Revenu_moy": revenu / nb_mois,
                "Depense_moy": depense / nb_mois,
                "Ecart_moy": ecart / nb_mois
            })
    return pd.DataFrame(resultats)


"""
AJOUT SUPRESSION LIGNE 
"""
def supprimer_entree(tab, index):
    """
    Supprime une entrée du DataFrame selon l'index avec gestion des erreurs.
    """
    try:
        if not isinstance(index, int):
            raise TypeError("L'index doit être un entier")

        if index not in tab.index:
            raise IndexError(f"Index {index} inexistant. Index valides : {tab.index.min()} → {tab.index.max()}")

        return tab.drop(index).reset_index(drop=True)

    except Exception as e:
        print(f"[ERREUR] Impossible de supprimer l'entrée : {e}")
        return tab  # retourner le tableau inchangé
def ajouter_entree(tab, date, intitule, categorie, classe, type_, valeur):
    """
    Ajoute une nouvelle entrée au DataFrame avec gestion des erreurs.
    """
    try:
        # Vérif type_ correct
        if str(type_).lower() not in ["revenu", "depense"]:
            raise ValueError("Le champ 'Type' doit être 'Revenu' ou 'Depense'")

        # Vérif valeur numérique
        try:
            valeur = float(valeur)
        except Exception:
            raise ValueError("Le champ 'Valeur' doit être un nombre")

        # Vérif date
        try:
            date = pd.to_datetime(date, dayfirst=True)
        except Exception:
            raise ValueError("Le champ 'Date' doit être convertible en datetime (ex: '2025-09-01')")

        # Construction de la nouvelle ligne
        nouvelle_ligne = {
            "Date": date,
            "Intitule": str(intitule),
            "Categorie": str(categorie),
            "Classe": str(classe),
            "Type": str(type_).capitalize(),  # standardiser
            "Valeur": valeur
        }

        return pd.concat([tab, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

    except Exception as e:
        print(f"[ERREUR] Impossible d'ajouter l'entrée : {e}")
        return tab  # retourner le tableau inchangé
