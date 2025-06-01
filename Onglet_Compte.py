import os
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import openpyxl

class OngletCompte(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app =app
        self.dossier = '.'  # dossier des fichiers

        self.label_title = tk.Label(self, text="Comptes disponibles (dernière modification)", font=("Arial", 14))
        self.label_title.pack(pady=5)

        self.listbox = tk.Listbox(self, width=50)
        self.listbox.pack(pady=5)

        frame_suppr = tk.Frame(self)
        frame_suppr.pack(pady=10)
        tk.Label(frame_suppr, text="Compte à supprimer :").pack(side='left')
        self.combo_suppr = ttk.Combobox(frame_suppr, state="readonly", width=30)
        self.combo_suppr.pack(side='left', padx=5)
        btn_suppr = tk.Button(frame_suppr, text="Supprimer", command=self.supprimer_compte)
        btn_suppr.pack(side='left')

        frame_creer = tk.Frame(self)
        frame_creer.pack(pady=10)
        tk.Label(frame_creer, text="Nom nouveau compte :").pack(side='left')
        self.entry_creer = tk.Entry(frame_creer, width=30)
        self.entry_creer.pack(side='left', padx=5)
        btn_creer = tk.Button(frame_creer, text="Créer", command=self.creer_compte)
        btn_creer.pack(side='left')

        self.maj_liste_comptes()

    def maj_liste_comptes(self):
        self.app.Update()
        fichiers = self.app.liste_compte

        self.listbox.delete(0, tk.END)
        comptes = []
        for f in fichiers:
            chemin = os.path.join(self.dossier, f)
            date_modif = datetime.datetime.fromtimestamp(os.path.getmtime(chemin))
            date_str = date_modif.strftime("%Y-%m-%d %H:%M:%S")
            self.listbox.insert(tk.END, f"{f} - modifié le {date_str}")
            comptes.append(f)

        self.combo_suppr['values'] = comptes
        self.combo_suppr.set('')

    def creer_fichier_xlsx(self, nom_fichier):
        if not nom_fichier.endswith('.xlsx'):
            nom_fichier += '.xlsx'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Feuille1"
        colonnes = ["Date", "Intitule", "Categorie", "Classe", "Type", "Valeur"]
        ws.append(colonnes)
        wb.save(nom_fichier)
        print(f"Fichier créé : {nom_fichier}")

    def supprimer_fichier_xlsx(self, nom_fichier):
        if not nom_fichier.endswith('.xlsx'):
            nom_fichier += '.xlsx'

        if os.path.isfile(nom_fichier):
            os.remove(nom_fichier)
            print(f"Fichier supprimé : {nom_fichier}")
        else:
            print(f"Fichier non trouvé : {nom_fichier}")

    def supprimer_compte(self):
        compte = self.combo_suppr.get()
        if not compte:
            messagebox.showwarning("Attention", "Veuillez sélectionner un compte à supprimer.")
            return
        confirm = messagebox.askyesno("Confirmer", f"Supprimer le compte '{compte}' ?")
        if confirm:
            self.supprimer_fichier_xlsx(compte)
            self.maj_liste_comptes()

    def creer_compte(self):
        nom = self.entry_creer.get().strip()
        if not nom:
            messagebox.showwarning("Attention", "Veuillez entrer un nom de compte.")
            return
        if not nom.endswith('.xlsx'):
            nom += '.xlsx'
        if os.path.exists(nom):
            messagebox.showerror("Erreur", "Un compte avec ce nom existe déjà.")
            return
        self.creer_fichier_xlsx(nom)
        messagebox.showinfo("Succès", f"Compte '{nom}' créé.")
        self.entry_creer.delete(0, tk.END)
        self.maj_liste_comptes()