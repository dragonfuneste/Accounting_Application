from Fonction import *
from Compte import Compte
from Librairie import *
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import os
from datetime import datetime


class Onglet_Comptes(tk.Frame):
    """Onglet pour afficher et gérer la liste des comptes."""
    
    def __init__(self, parent, comptes, info_file, csv_dir):
        super().__init__(parent)
        self.parent = parent
        self.comptes = comptes
        self.info_file = info_file
        self.csv_dir = csv_dir
        
        self.create_ui()
    
    def create_ui(self):
        """Crée l'interface de l'onglet Comptes."""
        # Treeview pour afficher les comptes
        self.tree = ttk.Treeview(self, columns=("Nom", "Revenu Total", "Dépense", "Total", "Debut", "État", "Monnaie"), show="headings")
        self.tree.heading("Nom", text="Nom")
        self.tree.heading("Revenu Total", text="Revenu Total")
        self.tree.heading("Dépense", text="Dépense")
        self.tree.heading("Total", text="Total")
        self.tree.heading("Debut", text="Debut")
        self.tree.heading("État", text="État")
        self.tree.heading("Monnaie", text="Monnaie")
        self.tree.column("Nom", width=150, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configurer le grid pour que le treeview soit redimensionnable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Frame pour les boutons
        button_frame = tk.Frame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        add_button = tk.Button(button_frame, text="Ajouter un Compte", command=self.add_account)
        add_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(button_frame, text="Supprimer le Compte", command=self.delete_account)
        delete_button.pack(side=tk.LEFT, padx=5)

        status_button = tk.Button(button_frame, text="Changer l'État", command=self.change_status)
        status_button.pack(side=tk.LEFT, padx=5)

        # Remplir le Treeview
        self.populate_treeview()

        # Lier l'événement de double-clic pour renommer un compte
        self.tree.bind("<Double-1>", self.rename_account)

    def populate_treeview(self):
        """Remplit le Treeview avec les données des comptes."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for name, compte in self.comptes.items():
            revenue = compte.revenus
            expense = compte.depenses
            total = compte.total
            self.tree.insert("", "end", values=(name, revenue, expense, total, compte.date_debut, compte.etat, compte.currency))

    def add_account(self):
        """Ajoute un nouveau compte."""
        name = simpledialog.askstring("Ajouter un Compte", "Nom du Compte:")
        if name:
            if name in self.comptes:
                messagebox.showerror("Erreur", "Un compte avec ce nom existe déjà.")
                return

            # Demander la monnaie
            currencies = list(set(compte.currency for compte in self.comptes.values()))
            currency = simpledialog.askstring("Ajouter un Compte", f"Monnaie (par défaut: Euros):", initialvalue="Euros") or "Euros"

            # Créer un nouveau fichier Excel pour le compte
            df = pd.DataFrame(columns=["Date", "Intitulé", "Catégorie", "Classe", "Type", "Valeur"])
            df.to_excel(f"{self.csv_dir}/{name}.xlsx", index=False)

            # Ajouter le compte au dictionnaire
            compte = Compte(f"{self.csv_dir}/{name}.xlsx", "ouvert", currency)
            self.comptes[name] = compte

            # Sauvegarder et rafraîchir
            self.parent.save_accounts()
            self.parent.refresh_all()

    def delete_account(self):
        """Supprime le compte sélectionné."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Aucun compte sélectionné.")
            return

        name = self.parent.combo_var.get()
        if name in self.comptes:
            # Supprimer le fichier Excel
            os.remove(f"{self.csv_dir}/{name}.xlsx")

            # Supprimer le compte du dictionnaire
            del self.comptes[name]

            # Sauvegarder et rafraîchir
            self.parent.save_accounts()
            self.parent.refresh_all()

    def change_status(self):
        """Change l'état du compte sélectionné."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Aucun compte sélectionné.")
            return

        name = self.parent.combo_var.get()
        if name in self.comptes:
            current_status = self.comptes[name].status
            new_status = 'fermé' if current_status == 'ouvert' else 'ouvert'
            self.comptes[name].status = new_status

            # Sauvegarder et rafraîchir
            self.parent.save_accounts()
            self.parent.refresh_all()

    def rename_account(self, event):
        """Renomme le compte sélectionné."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Aucun compte sélectionné.")
            return

        old_name = self.parent.combo_var.get()
        if old_name in self.comptes:
            new_name = simpledialog.askstring("Renommer le Compte", "Nouveau Nom:", initialvalue=old_name)
            if new_name and new_name != old_name:
                if new_name in self.comptes:
                    messagebox.showerror("Erreur", "Un compte avec ce nom existe déjà.")
                    return

                # Renommer le fichier Excel
                os.rename(f"{self.csv_dir}/{old_name}.xlsx", f"{self.csv_dir}/{new_name}.xlsx")

                # Mettre à jour le dictionnaire
                compte = self.comptes.pop(old_name)
                compte.nom = new_name
                self.comptes[new_name] = compte

                # Sauvegarder et rafraîchir
                self.parent.save_accounts()
                self.parent.refresh_all()

    def refresh(self):
        """Rafraîchit l'affichage de l'onglet."""
        self.populate_treeview()