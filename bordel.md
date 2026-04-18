# STRUCTURE du core (./core)
- Compte.py :  Fichier qui gere le compte 
    * __init__      (account_name: str, devise: str, state: bool, df: pd.DataFrame)
    * actualize_df  ()
    * add_lines     (champs: dict)
    * delete_lines  (index: int)
    * modify_lines  (index: int, nouveaux_champs: dict)
    * triage        (column: str, croissant: bool = True)
    * Filtrage      (id : int, keyword: str)
    * Tri_Period    (start_date: datetime, end_date: datetime)
    * uniques       ()
    * statistic     ()


- Comptabilite.py : Fichier qui gere toute la logique entre les compte
    * __init__      (liste_compte: list[Compte])
    * compute_full  ()
    * creer_nouveau_compte(nom: str, devise: str = "EUR") 
    * virement_intercompte(date: datetime, idx_src: int, idx_dst: int, montant: float, raison: str)
    * change_state  (index: int)


- Database.py : Fichier qui gere avec la dabase 
    * __init__          (db_name: str)
    * _create_empty_db  ()
    * read_all_accounts ()
    * save_all_accounts (liste_comptes: list)
# STRUCTURE API 
    (./api)
    - Api_compta : qui transforme les data de compta en json 
    - API_compte : qui transforme les data de compte en JSOn $
    (./route)
    * Blueprint : 
        - accounts_routes.py
        - compta_routes.py

# STRUCTURE front end (./front_end)
    - Compte.css , .js , .html : la ou on peut changer/ajouter/supprimer les donnée interne d'un compte (les transactions à l'interieur)
    - Index.css , .js , .html : la ou affiche les different compte qu'on peut en rajouter , supprimer et changer leurs noms, leurs état et leurs devise

    - lvl1  API de gestion du compte
        * Au niveau de Comptabilite :  Pouvoir ajouter, supprimer, editer des compte
        * Au niveau de Compte : Pouvoir voir le tableau d un compte selection avec tout sur ce compte , pouvoir modifier des lignes en supprimer ou bien en ajouter, pouvoir filtrer pour rechercher, pouvoir trier
        * Faire les calculs statistic simple pour revenu/depense/ecart 
    - lvl2 : API de la gestion des interface temporel 
    - lvl3 : le truc plus poussé

# STRUCTURE front end 


# TASK repartition
- Faire le backend python 
    - Compte
    - Comptabilite
    - Database

- Faire une API de gestion facile 
    - lvl1 : API de gestion du compte
    - lvl2 : API de la gestion des interface temporel 
    - lvl3 : le truc plus poussé

- faire le front end en html,css,js :
    * Menu_1  * Gestion des compte *                    = lvl1 
    * Menu_2  * Gestion du compte  *                    = lvl1 
    * Menu_3  * Interface virement intercompte *        = lvl2
    * Menu_4  * Graphique temporel des comptes *        = lvl2 
    * Menu_5  * Reppartititon des Depenses *            = lvl3 
    * Menu_6  * Analyse futur *                         = lvl3


### Objectif onglet 
C'est parfait, on a maintenant un concept solide de "tri intelligent" sans pollution de données. Voici le résumé des fonctionnalités que nous avons validées pour l'onglet Objectifs :
1. Structure de l'Objectif (Le JSON)
Chaque objectif est indépendant et possède sa propre identité temporelle :

Identité : Nom, montant cible (enveloppe), et compte bancaire de référence.

Temporalité : Une date de création (début du suivi) et une date de fin prévue.

Mémoire (Apprentissage) : * transactions_validees : Liste des real_index que tu as confirmés.

transactions_refusees : Liste des real_index que tu as explicitement exclus.

empreintes : Liste des libellés et catégories appris lors de tes validations.

2. Le Système de "Matching" Semi-Automatique
Au lieu de règles rigides, le code travaille pour toi de manière dynamique :

Détection : Le Python scanne les transactions entre les dates de l'objectif.

Catégorisation visuelle :

Confirmé (Vert) : Déjà comptabilisé dans ta barre de progression.

Suggéré (Orange) : Le code a trouvé une transaction qui ressemble à tes "empreintes" (ex: même magasin) mais attend ton clic pour l'inclure.

Ignoré (Masqué) : Les transactions que tu as refusées une fois n'apparaissent plus.

3. Indicateurs de Performance (KPIs)
Pour chaque objectif, l'interface calcule en temps réel :

Le Réalisé : Somme des transactions validées.

Le Potentiel : Somme des transactions validées + suggestions en attente.

Le Reste à Financer : La différence entre ta cible et ton réalisé.

L'Effort Mensuel : Combien tu dois mettre de côté par mois jusqu'à la date de fin pour atteindre ta cible.