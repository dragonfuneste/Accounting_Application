from __future__ import annotations
import json
import os
import uuid
import pandas as pd
from datetime import datetime, date
from typing import Optional
from core.variables.variable import COLUMNS_STRUCTURE, _STOPWORDS, MAX_KEYWORDS, EN_COURS, TERMINE
from core.models.objectif import Objective
from core.models.step import Step


# ─────────────────────────────────────────────────────────────────────────────
# LinkResult
# ─────────────────────────────────────────────────────────────────────────────

class LinkResult:
    def __init__(self):
        self.attributed : dict[str, float] = {}
        self.overflow   : float = 0.0
        self.overflowed : bool  = False

    def __repr__(self):
        return (f"LinkResult(attributed={self.attributed}, "
                f"overflow={self.overflow}, overflowed={self.overflowed})")



# ─────────────────────────────────────────────────────────────────────────────
# ProjectManagement — logique métier
# ─────────────────────────────────────────────────────────────────────────────

class ProjectManagement:
    """
    Cerveau analytique.
    A accès à Projects (structure) et compta (données financières).
    """

    def __init__(self, projects: Projects, compta):
        self.projects = projects
        self.compta   = compta

    # ── Helpers privés ────────────────────────────────────────────────────────

    def _get_account(self, account_name: str):
        return next((c for c in self.compta.liste_compte
                     if c.account_name == account_name), None)

    def _get_transaction_amount(self, account_name: str, tid: str) -> Optional[float]:
        """Retourne le montant d'une transaction depuis compta."""
        account = self._get_account(account_name)
        if account is None:
            return None
        row = account.df[account.df["real_index"] == tid]
        if row.empty:
            return None
        return float(row.iloc[0].get(COLUMNS_STRUCTURE[5], 0))

    def _get_transaction(self, account_name: str, tid: str) -> Optional[dict]:
        account = self._get_account(account_name)
        if account is None:
            return None
        row = account.df[account.df["real_index"] == tid]
        return row.iloc[0].to_dict() if not row.empty else None

    # ── Compute ───────────────────────────────────────────────────────────────

    def compute(self) -> None:
        """
        Relit tous les IDs depuis compta et recalcule from scratch :
        - current_total  : somme des revenus liés
        - expenses_only  : somme des dépenses liées
        - status         : TERMINE si current_total >= target
        - overflow       : surplus redistribué vers la prochaine step EN_COURS

        Appelé automatiquement par apply_transaction.
        Peut aussi être appelé manuellement après un import ou une modif externe.
        """
        for obj in self.projects.objectifs:
            overflow = 0.0  # surplus de la step précédente à cascader

            for step in obj.steps:
                # ── Reset ────────────────────────────────────────────────────
                step.current_total = 0.0
                step.expenses_only = 0.0

                # ── Revenus ──────────────────────────────────────────────────
                for account_name, tids in step.income_links.items():
                    for tid in tids:
                        amount = self._get_transaction_amount(account_name, tid)
                        if amount is not None:
                            step.current_total += amount

                # ── Dépenses ─────────────────────────────────────────────────
                for account_name, tids in step.expense_links.items():
                    for tid in tids:
                        amount = self._get_transaction_amount(account_name, tid)
                        if amount is not None:
                            step.expenses_only  += amount
                            step.current_total  += amount

                # ── Absorption du surplus de la step précédente ───────────────
                if overflow > 0 and step.status == EN_COURS:
                    absorbable      = min(overflow, step.remaining_to_find)
                    step.current_total += absorbable
                    overflow        -= absorbable

                # ── Statut ───────────────────────────────────────────────────
                if step.current_total >= step.target and step.target > 0:
                    overflow      += step.current_total - step.target
                    step.current_total = step.target
                    step.status   = TERMINE
                elif step.status == TERMINE and step.current_total < step.target:
                    step.status   = EN_COURS  # rétrogradation si on unlink

    # ── apply_transaction ─────────────────────────────────────────────────────

    def apply_transaction(self, id_objectif: str, id_step: str,
                          account_name: str, tid: str,
                          depense: bool) -> LinkResult:
        """
        Link + compute en une seule opération.
        Retourne un LinkResult avec la distribution finale.
        """
        result = LinkResult()

        # 1. Enregistre le lien
        linked = self.projects.link_transaction(
            id_objectif, id_step, account_name, tid, depense
        )
        if not linked:
            return result

        # 2. Recalcule tout from scratch
        self.compute()

        # 3. Construit le LinkResult depuis l'état post-compute
        obj = self.projects.get_objectif(id_objectif)
        if obj is None:
            return result

        total_remaining = 0.0
        for step in obj.steps:
            if step.current_total > 0:
                result.attributed[step.name] = step.current_total
            total_remaining += step.remaining_to_find

        # Overflow = ce qui dépasse tous les steps de l'objectif
        tx_amount = self._get_transaction_amount(account_name, tid) or 0.0
        total_absorbed = sum(result.attributed.values())
        if tx_amount > total_absorbed:
            result.overflow   = tx_amount - total_absorbed
            result.overflowed = True

        return result

    # ── Recommandation ────────────────────────────────────────────────────────

    def recommendation(self, id_objectif: str, id_step: str,
                       account_name: str,
                       max_results: int = 10) -> list[dict]:
        """
        Pour chaque transaction non liée du compte, calcule un score
        basé sur les keywords de la step.
        Enrichit aussi les keywords depuis les transactions déjà liées.
        """
        step = self.projects.get_step(id_objectif, id_step)
        account = self._get_account(account_name)
        if step is None or account is None:
            return []

        # Enrichissement depuis les transactions déjà liées
        all_links = {**step.income_links, **step.expense_links}
        for acc_name, tids in all_links.items():
            for tid in tids:
                tx = self._get_transaction(acc_name, tid)
                if tx:
                    self._enrich_keywords(step, tx)

        if not step.keywords:
            return []

        keywords = [k.lower() for k in step.keywords]
        already_linked = set(
            tid for links in (step.income_links, step.expense_links)
            for ids in links.values() for tid in ids
        )

        results = []
        for _, row in account.df.iterrows():
            tid = row.get("real_index", "")
            if tid in already_linked:
                continue
            haystack = " ".join([
                str(row.get(COLUMNS_STRUCTURE[1], "")),
                str(row.get(COLUMNS_STRUCTURE[2], "")),
                str(row.get(COLUMNS_STRUCTURE[3], "")),
            ]).lower()
            score = sum(1 for kw in keywords if kw in haystack)
            if score > 0:
                results.append({"score": score, "transaction": row.to_dict()})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def _enrich_keywords(self, step: Step, tx: dict) -> None:
        sources = [tx.get(COLUMNS_STRUCTURE[1], ""),
                   tx.get(COLUMNS_STRUCTURE[2], ""),
                   tx.get(COLUMNS_STRUCTURE[3], "")]
        for raw in sources:
            for word in str(raw).lower().split():
                if len(word) > 2 and word not in _STOPWORDS and word not in step.keywords:
                    step.keywords.append(word)
        if len(step.keywords) > step.max_keywords:
            step.keywords = step.keywords[-step.max_keywords:]

    # ── Priorité ─────────────────────────────────────────────────────────────

    def project_priority(self, window_months: int = 3) -> list[str]:
        """
        Calcule une priorité pour chaque objectif et retourne
        les ids triés du plus urgent au moins urgent.

        score = importance × retard × urgence_deadline × activité
        """
        scores = []
        for obj in self.projects.objectifs:
            obj_score = max(
                (self._step_score(obj, step, window_months)
                 for step in obj.steps if step.status == EN_COURS),
                default=0.0
            )
            scores.append((obj.id, obj_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [oid for oid, _ in scores]

    def _step_score(self, obj: Objective, step: Step,
                    window_months: int) -> float:
        retard = 1 - (step.current_total / step.target) if step.target else 0

        urgence      = 1.0
        deadline_str = step.deadline or obj.deadline
        if deadline_str:
            try:
                deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                mois_restants = max(
                    (deadline_date - date.today()).days / 30.44, 0.1
                )
                urgence = 1 + (1 / mois_restants)
            except ValueError:
                pass

        return obj.importance * retard * urgence * self._activity(step, window_months)

    def _activity(self, step: Step, window_months: int) -> float:
        cutoff       = datetime.now().timestamp() - (window_months * 30.44 * 86400)
        total_recent = 0.0
        nb_tx_recent = 0
        has_any_tx   = False

        for account_name, tids in {**step.income_links, **step.expense_links}.items():
            account = self._get_account(account_name)
            if account is None:
                continue
            for tid in tids:
                row = account.df[account.df["real_index"] == tid]
                if row.empty:
                    continue
                has_any_tx = True
                tx_date = pd.to_datetime(
                    row.iloc[0].get(COLUMNS_STRUCTURE[0], ""),
                    dayfirst=True, errors="coerce"
                )
                if pd.isna(tx_date):
                    continue
                if tx_date.timestamp() >= cutoff:
                    nb_tx_recent += 1
                    total_recent += float(row.iloc[0].get(COLUMNS_STRUCTURE[5], 0))

        if not has_any_tx:
            return 1.0
        bonus = 0.5 * min(total_recent / step.target, 1.0) if step.target else 0
        malus = 0.5 if nb_tx_recent == 0 else 0.0
        return 1.0 + bonus - malus

    # ── Résumé global ─────────────────────────────────────────────────────────

    def global_summary(self) -> dict:
        objs = self.projects.objectifs
        return {
            "nb_objectifs"  : len(objs),
            "épargné_total" : sum(o.total_saved    for o in objs),
            "dépensé_total" : sum(o.total_expenses for o in objs),
            "objectif_total": sum(o.total_target   for o in objs),
            "restant_total" : sum(max(o.total_target - o.total_saved, 0) for o in objs),
        }