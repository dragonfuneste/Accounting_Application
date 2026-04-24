
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

class Projects:
    """
    Registre des objectifs et étapes.
    Aucune logique métier — juste du CRUD et de la persistence.
    """

    def __init__(self, json_path: str):
        self.objectifs : list[Objective] = []
        self.json_path = json_path
        self.read_json(json_path)

    # ── Persistence ───────────────────────────────────────────────────────────

    def read_json(self, json_path: str) -> None:
        if not os.path.exists(json_path):
            return
        with open(json_path, encoding="utf-8") as f:
            self.objectifs = [Objective.from_dict(d) for d in json.load(f)]

    def save(self, json_path: str = None) -> None:
        target = json_path or self.json_path
        with open(target, "w", encoding="utf-8") as f:
            json.dump([o.to_dict() for o in self.objectifs],
                      f, ensure_ascii=False, indent=2)

    # ── Objectifs ─────────────────────────────────────────────────────────────

    def create_objective(self, objectif: Objective) -> Objective:
        self.objectifs.append(objectif)
        return objectif

    def delete_objective(self, id_objectif: str) -> bool:
        obj = self.get_objectif(id_objectif)
        if obj is None:
            return False
        self.objectifs.remove(obj)
        return True

    def modify_objective(self, id_objectif: str, **kwargs) -> bool:
        """
        Met à jour les champs d'un objectif.
        Champs modifiables : name, but, importance, deadline, logo
        """
        obj = self.get_objectif(id_objectif)
        if obj is None:
            return False
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return True

    def get_objectif(self, id_objectif: str) -> Optional[Objective]:
        return next((o for o in self.objectifs if o.id == id_objectif), None)

    # ── Steps ─────────────────────────────────────────────────────────────────

    def create_step(self, id_objectif: str, step: Step) -> Optional[Step]:
        obj = self.get_objectif(id_objectif)
        if obj is None:
            return None
        obj.add_step(step)
        return step

    def delete_step(self, id_objectif: str, id_step: str) -> bool:
        obj = self.get_objectif(id_objectif)
        if obj is None:
            return False
        step = self.get_step(id_objectif, id_step)
        if step is None:
            return False
        obj.steps.remove(step)
        return True

    def modify_step(self, id_objectif: str, id_step: str, **kwargs) -> bool:
        """
        Met à jour les champs d'une étape.
        Champs modifiables : name, but, target, deadline, status, max_keywords
        Note : current_total et expenses_only sont gérés par compute(), pas ici.
        """
        step = self.get_step(id_objectif, id_step)
        if step is None:
            return False
        for key, value in kwargs.items():
            if hasattr(step, key):
                setattr(step, key, value)
        return True

    def get_step(self, id_objectif: str, id_step: str) -> Optional[Step]:
        obj = self.get_objectif(id_objectif)
        if obj is None:
            return None
        return next((s for s in obj.steps if s.id == id_step), None)

    # ── Liens transactions ────────────────────────────────────────────────────

    def link_transaction(self, id_objectif: str, id_step: str,
                         account_name: str, tid: str, depense: bool) -> bool:
        """Enregistre l'ID de transaction dans la step. Pas de calcul."""
        step = self.get_step(id_objectif, id_step)
        if step is None:
            return False
        links = step.expense_links if depense else step.income_links
        links.setdefault(account_name, [])
        if tid not in links[account_name]:
            links[account_name].append(tid)
        return True

    def unlink_transaction(self, id_objectif: str, id_step: str,
                           account_name: str, tid: str, depense: bool) -> bool:
        """Retire l'ID de transaction de la step."""
        step = self.get_step(id_objectif, id_step)
        if step is None:
            return False
        links = step.expense_links if depense else step.income_links
        if account_name in links and tid in links[account_name]:
            links[account_name].remove(tid)
            if not links[account_name]:
                del links[account_name]
            return True
        return False