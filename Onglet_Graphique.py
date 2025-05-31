# -*- coding: utf-8 -*-
"""
Created on Sat May 31 17:17:11 2025

@author: loube
"""


        
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

"""

Onglet Graphique : Cette onglet ajoute les graphique associé au compte afin d'avoir un appercut plus propre de ce que l'on fait 
    Deja il y auras un bouton switch qui permet d'acceder a deux mode : 
        1 - Mode Suivis temporel ou l'on affiche les diagramme cumulé de tout les compte disponible de l'application 
        2 - Mode Suivis Camembert ou cela divise l'onglet en 2. En haut les depense et en bas les revenu. Dans chacune des partie il y auras 2 Camembert au fonctionnalité similaire. le premier serat les pourcentage (avec leurs valeurs)
        dans le df sélectionné de chacune des Categorie. le second  nous donne les classes associé (avec leurs valeurs) si l'on clique sur une région du premier camembert. Et si on clique sur un zone de ce graphique 
        cela nous affiche l'Intitulé max de cette zone. 
"""
class OngletGraphique(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        