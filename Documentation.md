# 📖 Documentation des fonctions

## Fichiers : `Compte.py` et `Fonction.py`

---

# 🧾 **Compte.py**

## Classe `Compte`

### Attributs principaux

- `nom` : Nom du compte (extrait automatiquement du fichier, ex. `Compte_Courant`)  
- `chemin` : Chemin vers le fichier Excel chargé  
- `df` : Tableau principal (`pandas.DataFrame`)  
- `date_debut` : Date minimale trouvée dans la colonne *Date*  
- `date_fin` : Date maximale trouvée dans la colonne *Date*  
- `categories` : Liste des valeurs uniques de la colonne *Categorie*  
- `classes` : Liste des valeurs uniques de la colonne *Classe*  
- `types` : Liste des valeurs uniques de la colonne *Type*  
- `depenses` : Somme totale recalculée automatiquement des revenus  
- `revenus` : Somme totale recalculée automatiquement  des depenses  
- `total` : Somme totale recalculée automatiquement (signé)  
---

### Méthodes

#### `__init__(self, chemin: str)`

Charge le fichier Excel et initialise le compte.

- **Paramètres** :  
  - `chemin` : chemin du fichier `.xlsx`  
- **Effet** : initialise le tableau, les dates min/max, les listes uniques et la somme totale.

---

#### `ajouter_ligne(self, date, intitule, categorie, classe, type_operation, valeur)`

Ajoute une ligne au tableau.

- **Paramètres** :  
  - `date` : date de l'opération  
  - `intitule` : description  
  - `categorie` : catégorie de l'opération  
  - `classe` : classe de l'opération  
  - `type_operation` : type (`Dépense` ou autre)  
  - `valeur` : montant  
- **Effets** :  
  - ajoute la ligne dans `df`  
  - recalcul des statistiques et du total  

---

#### `supprimer_ligne(self, index: int)`

Supprime une ligne selon son index.

- **Paramètres** :  
  - `index` : index de la ligne  
- **Effets** : recalcul automatique des statistiques et du total  

---

#### `modifier_ligne(self, index: int, **champs)`

Modifie les champs d’une ligne existante.

- **Paramètres** :  
  - `index` : index de la ligne  
  - `champs` : dictionnaire des colonnes à modifier (`Intitule`, `Categorie`, `Classe`, `Type`, `Valeur`, `Date`)  
- **Effets** : recalcul automatique des statistiques et du total  

---

#### `trier(self, colonne: str, croissant: bool = True)`

Trie le tableau selon une colonne.

- **Paramètres** :  
  - `colonne` : nom de la colonne (`Date`, `Intitule`, `Categorie`, `Classe`, `Type`, `Valeur`)  
  - `croissant` : `True` pour ordre croissant, `False` pour décroissant  

---

#### `sauvegarder(self)`

Sauvegarde le tableau.

- **Effets** :  
  - crée une copie de l’ancien fichier dans `./backup/backup_<nom>.xlsx`  
  - remplace le fichier original par le tableau actuel  

---

#### `categories_uniques(self)` / `classes_uniques(self)` / `types_uniques(self)`

- **Retour** : liste des valeurs uniques respectivement dans *Categorie*, *Classe*, *Type*

---

# 🧾 **Fonction.py**

## Classe `FonctionFiltre`

Permet de filtrer une copie du tableau d’un compte sans modifier l’original.

### Attributs principaux

- `df` : copie du tableau du compte  
- `date_debut`, `date_fin` : dates min/max  
- `categories`, `classes`, `types` : valeurs uniques  

---

### Méthodes

#### `__init__(self, compte)`

- **Paramètres** :  
  - `compte` : instance de `Compte`  
- **Effets** : initialise la copie du tableau et récupère les valeurs uniques et les dates min/max  

---

#### `filtrer(self, **conditions) -> DataFrame`

Filtre le tableau selon plusieurs critères.

- **Paramètres** :  
  - `conditions` : colonnes et valeurs à filtrer  
    - ex : `Categorie="Achat"`, `Classe="Maison"`, `Type=["Dépense","Recette"]`, `Date_debut="2024-01-01"`, `Date_fin="2024-12-31"`  
- **Retour** : DataFrame filtré  

---

#### `bornes_dates(self) -> tuple`

- **Retour** : `(date_min, date_max)`  

---

#### `get_categories(self)`, `get_classes(self)`, `get_types(self)`

- **Retour** : liste des valeurs uniques de la colonne correspondante  

---

#### `valeurs_uniques(self, colonne: str)`

- **Paramètres** :  
  - `colonne` : nom de la colonne  
- **Retour** : liste des valeurs uniques de cette colonne  

---

#### `dataframe(self)`

- **Retour** : copie locale du DataFrame  

---
