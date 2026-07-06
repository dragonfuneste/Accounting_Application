# Accounting Application

## Vue d'ensemble

Cette application est un outil de gestion comptable composé de deux parties :

- Backend Python/Flask
- Frontend React/Vite

L'application permet de gérer des comptes, visualiser des statistiques, effectuer des virements intercomptes et suivre des projets.

## Architecture du projet

### Fichiers racines

- `main.py` : point d’entrée du backend Flask.
- `index.jsx` : point d’entrée du frontend React.
- `package.json` : configuration frontend et scripts Vite.
- `index.html` : page HTML principale du frontend.
- `README.md` : documentation du projet.

### Backend

- `back_end/Comptabilite.py` : gestion des comptes, connexions SQLite et calculs statistiques.
- `back_end/Compte.py` : classe `Compte` pour charger un compte, ajouter/modifier/supprimer les transactions et récupérer des statistiques.
- `back_end/Projet.py` : gestion des projets et des étapes, stockage JSON.
- `blueprint_menu.py` : définition des routes Flask pour l’API, en particulier les opérations sur les comptes, les dettes, les virements et les projets.
- `_data/` : données persistantes du projet.
- `other_functions/migration_old_db.py` : utilitaire de migration d’anciennes bases de données.

### Frontend

- `frontend/jsx/` : composants React de l’interface utilisateur.
  - `menu/Menuaccounts.jsx` : composant principal de l’application.
  - `menu/CompteDetail.jsx` : affichage des détails d’un compte sélectionné.
  - `menu/Globalcumulmodal.jsx` : modal de cumul global.
  - `menu/Projetonglet.jsx` : onglet de gestion des projets.
  - `onglets/` : composants pour chaque onglet de la page (statistiques, prédictions, virements, tableau de bord, etc.).
- `frontend/css/` : styles spécifiques aux composants.
- `index.css` : styles globaux.

## Technologies utilisées

- Backend : Python, Flask, Flask-CORS, pandas, sqlite3
- Frontend : React, Vite, React Router DOM, Chart.js, react-chartjs-2

## Prérequis

- Python 3.x
- Node.js et npm

## Installation et exécution

1. Depuis le dossier racine du projet, installer les dépendances Python :

```bash
pip install flask flask-cors pandas
```

2. Installer les dépendances frontend :

```bash
npm install
```

3. Démarrer le backend Flask :

```bash
python main.py
```

Le backend écoute par défaut sur `http://127.0.0.1:5000`.

4. Démarrer le frontend Vite :

```bash
npm run dev
```

Le frontend sera normalement accessible sur `http://127.0.0.1:5173`.

## Configuration

- Le frontend communique avec l’API backend via l’URL `http://127.0.0.1:5000/api`.
- La base de données SQLite se trouve dans `_data/Compte_rework.db`.
- Les projets sont stockés dans `_data/projects.json`.

## Commandes utiles

- `npm run build` : construit le frontend pour la production.
- `npm run preview` : prévisualise la version de production du frontend.
