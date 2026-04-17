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


