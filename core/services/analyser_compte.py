# analyser_compte.py

from ..models.compte import compte

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# variables/variable.py (ajouter ces constantes)

STATUT_LABELS = {
    "a_venir":     "⏳ À venir",
    "en_retard":   "⚠️ En retard",
    "cycle_rompu": "🧊 Cycle rompu",
    "irregulier":  "🔀 Irrégulier",
}

FIABILITE_LABELS = {
    "critique":  "🔥 Critique",
    "fiable":    "✅ Fiable",
    "incertain": "⚖️ Incertain",
}
class analyser_compte:
    def __init__(self, compte: compte):
        self.compte = compte

    def Generer_prediction(self) -> pd.DataFrame:
        """
        Retourne un DataFrame avec des colonnes typées :
          - Date_Prevue   : datetime
          - Probabilite   : float  (0–100)
          - Statut        : str    clé parmi STATUT_LABELS
          - Fiabilite     : str    clé parmi FIABILITE_LABELS
          - Frequence     : float  (transactions / mois)
        """
        _, _, self.solde_actuel, _ = self.compte.statistic()
        df = self.compte.df.copy()
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
        df['Mois'] = df['Date'].dt.to_period('M')

        aujourdhui      = datetime.now()
        nb_mois_total   = len(df['Mois'].unique())
        tous_les_mois   = sorted(df['Mois'].unique())
        mois_max        = tous_les_mois[-1]

        # Poids croissants vers le présent (index 0 → poids faible)
        poids_par_mois = {
            m: 1 + (i / len(tous_les_mois))
            for i, m in enumerate(tous_les_mois)
        }

        resultats = []

        for (t, classe, cat), group in df.groupby(['Type', 'Classe', 'Categorie']):
            group  = group.sort_values('Date')
            mensuel = group.groupby('Mois')['Valeur'].sum().abs()

            if mensuel.empty:
                continue

            # ── A. MOYENNE PONDÉRÉE (mois récents > anciens) ──────────────
            poids_groupe = np.array([poids_par_mois.get(m, 1) for m in mensuel.index])
            moyenne      = float(np.average(mensuel.values, weights=poids_groupe))
            std_valeur   = float(mensuel.std()) if len(mensuel) > 1 else 0.0

            marge = max(moyenne * 0.10, std_valeur * 0.5)
            f_min = round(max(0.0, moyenne - marge), 2)
            f_max = round(moyenne + marge, 2)

            # ── B. CYCLE (jour du mois) ────────────────────────────────────
            jours_du_mois = group['Date'].dt.day
            jour_moyen    = float(jours_du_mois.mean())
            std_jour      = float(jours_du_mois.std()) if len(jours_du_mois) > 1 else 0.0

            # ── C. FRÉQUENCE ───────────────────────────────────────────────
            ratio_freq    = len(group) / nb_mois_total   # ~1 = mensuel
            est_mensuel   = 0.5 <= ratio_freq <= 1.5
            est_irregulier = ratio_freq < 0.4

            # ── D. SCORES ─────────────────────────────────────────────────
            nb_mois_presence  = len(mensuel)
            score_presence    = (nb_mois_presence / nb_mois_total) * 100

            mois_recents  = sorted(mensuel.index)[-2:]
            bonus_recence = 10.0 if any(m >= mois_max - 1 for m in mois_recents) else -15.0

            score_regularite = max(0.0, 100.0 - (std_jour * 10)) if len(group) > 1 else 40.0

            coeff_var     = std_valeur / moyenne if moyenne > 0 else 0.0
            score_montant = max(0.0, 100.0 - (coeff_var * 80))

            score_final = (
                score_presence   * 0.50
                + score_regularite * 0.25
                + score_montant    * 0.15
                + bonus_recence    * 0.10
            )
            score_final = float(np.clip(score_final, 0, 100))

            # ── E. DATE ESTIMÉE ────────────────────────────────────────────
            derniere_date  = group['Date'].max()
            prochain_mois  = (derniere_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            mois_courant   = aujourdhui.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if prochain_mois < mois_courant:
                prochain_mois = mois_courant

            jour_cible = int(round(jour_moyen))
            try:
                date_estimee = prochain_mois.replace(day=jour_cible)
            except ValueError:
                # Jour invalide pour ce mois → dernier jour du mois
                date_estimee = (prochain_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # ── F. STATUT ──────────────────────────────────────────────────
            if est_irregulier:
                statut_code = "irregulier"
                score_final = min(score_final, 40.0)

            elif date_estimee.date() < aujourdhui.date():
                jours_retard = (aujourdhui.date() - date_estimee.date()).days
                penalite     = min(score_final, jours_retard * 5.0)
                score_final  = max(0.0, score_final - penalite)
                statut_code  = "cycle_rompu" if score_final == 0 else "en_retard"

            else:
                statut_code = "a_venir"

            # ── G. FIABILITÉ ───────────────────────────────────────────────
            if score_final > 80:
                fiabilite_code = "critique"
            elif score_final > 45:
                fiabilite_code = "fiable"
            else:
                fiabilite_code = "incertain"

            # ── H. COMPILATION ─────────────────────────────────────────────
            resultats.append({
                "Type":           t,
                "Classe":         classe,
                "Categorie":      cat,
                "Montant_Moyen":  round(moyenne, 2),       # float
                "Fourchette_Min": f_min,                   # float
                "Fourchette_Max": f_max,                   # float
                "Date_Prevue":    date_estimee,            # datetime
                "Probabilite":    round(score_final, 1),   # float 0–100
                "Statut":         statut_code,             # clé str
                "Fiabilite":      fiabilite_code,          # clé str
                "Frequence":      round(ratio_freq, 2),    # float
            })

        return (
            pd.DataFrame(resultats)
            .sort_values(['Type', 'Probabilite'], ascending=[True, False])
            .reset_index(drop=True)
        )

    # ------------------------------------------------------------------
    # MÉTHODE D'AFFICHAGE (traduction uniquement ici)
    # ------------------------------------------------------------------

    @staticmethod
    def afficher_predictions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prend le DataFrame brut de Generer_prediction()
        et retourne une copie prête à l'affichage (strings + emojis).
        Ne jamais utiliser cette copie pour de la logique.
        """
        out = df.copy()
        out['Date_Prevue'] = out['Date_Prevue'].apply(
            lambda d: d.strftime('%d/%m/%Y') if pd.notna(d) else ''
        )
        out['Statut']    = out['Statut'].map(STATUT_LABELS)
        out['Fiabilite'] = out['Fiabilite'].map(FIABILITE_LABELS)
        out['Frequence'] = out['Frequence'].apply(
            lambda r: "📅 Mensuel"    if 0.5 <= r <= 1.5
                 else "🔀 Irrégulier" if r < 0.4
                 else f"~{r:.1f}x/mois"
        )
        return out
    

    def simuler_scenario_stress(self,predictions: pd.DataFrame,probabilite = 10) -> pd.DataFrame:
        """
        Simule le pire scénario possible à partir des prédictions fiables.

        Filtres appliqués :
        - Probabilite > 50
        - Statut dans ['a_venir', 'en_retard']  (cycles actifs uniquement)

        Retourne
        --------
        DataFrame cumulatif trié chronologiquement :
        - Date_Prevue   : datetime
        - Type          : str
        - Classe        : str
        - Categorie     : str
        - Valeur        : float  (signée : + revenu, - dépense)
        - Solde_Cumule  : float  (solde après cette opération)
        """
        STATUTS_ACTIFS = {'a_venir', 'en_retard'}
        _, _, self.solde_actuel, _ = self.compte.statistic()
        futures = predictions[
            (predictions['Probabilite'] > probabilite) &
            (predictions['Statut'].isin(STATUTS_ACTIFS))
        ].copy()

        futures = futures.sort_values('Date_Prevue').reset_index(drop=True)

        # Scénario pire cas
        futures['Valeur'] = futures.apply(
            lambda row: row['Fourchette_Min'] if row['Type'] == 'Revenu'
                        else -row['Fourchette_Max'],
            axis=1
        )

        futures['Solde_Cumule'] = self.solde_actuel + futures['Valeur'].cumsum()
        futures['Solde_Cumule'] = futures['Solde_Cumule'].round(2)

        return futures[['Date_Prevue', 'Type', 'Classe', 'Categorie', 'Valeur', 'Solde_Cumule']]