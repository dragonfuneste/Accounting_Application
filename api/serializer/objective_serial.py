from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime
from core.models.objectif import Objective
from core.models.step import Step
from core.models.project import Projects
from core.services.project_management import ProjectManagement


# ─────────────────────────────────────────────────────────────────────────────
# Structures de données sérialisées
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BarData:
    """Représente une barre de progression."""
    value   : float   # montant actuel
    target  : float   # montant cible
    percent : float   # 0.0 → 100.0


@dataclass
class StepSerial:
    """Données sérialisées d'une étape pour la vue détaillée."""
    id              : str
    name            : str
    but             : str
    status          : str
    date_debut      : Optional[str]   # toujours None (Step ne stocke pas de date de création)
    date_fin        : Optional[str]   # deadline
    deadline_depasse: bool

    bar_global      : BarData         # accompli  = current_total / target
    bar_revenu      : BarData         # revenus   = (current_total - expenses_only) / target
    bar_depense     : BarData         # dépenses  = expenses_only / target


@dataclass
class ObjectiveSerial:
    """Données sérialisées d'un objectif pour la sticky note."""
    id               : str
    name             : str
    logo             : str
    but              : str
    importance       : int
    deadline         : Optional[str]
    deadline_depasse : bool
    priority_rank    : int            # position dans le tri priorité (0 = le plus urgent)

    bar_global       : BarData        # achievement globale sticky note
    montant_epargne  : float          # total_saved
    montant_objectif : float          # total_target

    steps            : list[StepSerial]


@dataclass
class ProjectsSerial:
    """Payload complet envoyé à l'API."""
    objectifs : list[ObjectiveSerial]
    summary   : dict                   # global_summary()


# ─────────────────────────────────────────────────────────────────────────────
# Serializer
# ─────────────────────────────────────────────────────────────────────────────

class ProjectManagementSerial:
    """
    Transforme l'état de Projects + ProjectManagement
    en structures prêtes à être envoyées à l'API / front.
    """

    def __init__(self, projects: Projects, management: ProjectManagement):
        self.projects   = projects
        self.management = management

    # ── Point d'entrée principal ──────────────────────────────────────────────

    def serialize(self) -> ProjectsSerial:
        """Retourne le payload complet trié par priorité."""
        priority_ids = self.management.project_priority()

        objectifs_serialized = []
        for rank, oid in enumerate(priority_ids):
            obj = self.projects.get_objectif(oid)
            if obj:
                objectifs_serialized.append(self._serialize_objective(obj, rank))

        # Objectifs sans steps EN_COURS (non présents dans priority_ids) — ajoutés à la fin
        ranked_ids = set(priority_ids)
        for obj in self.projects.objectifs:
            if obj.id not in ranked_ids:
                objectifs_serialized.append(
                    self._serialize_objective(obj, len(objectifs_serialized))
                )

        return ProjectsSerial(
            objectifs = objectifs_serialized,
            summary   = self.management.global_summary(),
        )

    # ── Sérialisation objectif ────────────────────────────────────────────────

    def _serialize_objective(self, obj: Objective, rank: int) -> ObjectiveSerial:
        today            = date.today()
        deadline_depasse = self._is_deadline_passed(obj.deadline, today)

        bar_global = BarData(
            value   = round(obj.total_saved, 2),
            target  = round(obj.total_target, 2),
            percent = obj.progress_percent,
        )

        return ObjectiveSerial(
            id               = obj.id,
            name             = obj.name,
            logo             = obj.logo,
            but              = obj.but,
            importance       = obj.importance,
            deadline         = obj.deadline,
            deadline_depasse = deadline_depasse,
            priority_rank    = rank,
            bar_global       = bar_global,
            montant_epargne  = round(obj.total_saved, 2),
            montant_objectif = round(obj.total_target, 2),
            steps            = [self._serialize_step(s, obj) for s in obj.steps],
        )

    # ── Sérialisation step ────────────────────────────────────────────────────

    def _serialize_step(self, step: Step, obj: Objective) -> StepSerial:
        today            = date.today()
        deadline_depasse = self._is_deadline_passed(step.deadline or obj.deadline, today)

        # Barre globale : tout ce qui a été mis de côté (revenus + dépenses absorbées)
        bar_global = BarData(
            value   = round(step.current_total, 2),
            target  = round(step.target, 2),
            percent = step.progress_percent,
        )

        # Barre revenus : argent mis de côté non encore dépensé
        revenu_value = round(step.current_total - step.expenses_only, 2)
        bar_revenu = BarData(
            value   = max(revenu_value, 0),
            target  = round(step.target, 2),
            percent = round(max(revenu_value, 0) / step.target * 100, 1) if step.target else 0.0,
        )

        # Barre dépenses : ce qui a déjà été acheté/dépensé
        bar_depense = BarData(
            value   = round(step.expenses_only, 2),
            target  = round(step.target, 2),
            percent = round(step.expenses_only / step.target * 100, 1) if step.target else 0.0,
        )

        return StepSerial(
            id               = step.id,
            name             = step.name,
            but              = step.but,
            status           = step.status,
            date_debut       = None,           # FIX : Step n'a pas de date de création
            date_fin         = step.deadline,  # FIX : date_fin = deadline uniquement
            deadline_depasse = deadline_depasse,
            bar_global       = bar_global,
            bar_revenu       = bar_revenu,
            bar_depense      = bar_depense,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _is_deadline_passed(deadline_str: Optional[str], today: date) -> bool:
        if not deadline_str:
            return False
        try:
            return datetime.strptime(deadline_str, "%Y-%m-%d").date() < today
        except ValueError:
            return False

    # ── Sérialisation JSON-ready ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Convertit le payload en dict pur pour jsonify() Flask."""
        payload = self.serialize()
        return {
            "summary"  : payload.summary,
            "objectifs": [self._obj_to_dict(o) for o in payload.objectifs],
        }

    @staticmethod
    def _bar_to_dict(bar: BarData) -> dict:
        return {"value": bar.value, "target": bar.target, "percent": bar.percent}

    def _step_to_dict(self, s: StepSerial) -> dict:
        return {
            "id"              : s.id,
            "name"            : s.name,
            "but"             : s.but,
            "status"          : s.status,
            "date_debut"      : s.date_debut,
            "date_fin"        : s.date_fin,
            "deadline_depasse": s.deadline_depasse,
            "bar_global"      : self._bar_to_dict(s.bar_global),
            "bar_revenu"      : self._bar_to_dict(s.bar_revenu),
            "bar_depense"     : self._bar_to_dict(s.bar_depense),
        }

    def _obj_to_dict(self, o: ObjectiveSerial) -> dict:
        return {
            "id"              : o.id,
            "name"            : o.name,
            "logo"            : o.logo,
            "but"             : o.but,
            "importance"      : o.importance,
            "deadline"        : o.deadline,
            "deadline_depasse": o.deadline_depasse,
            "priority_rank"   : o.priority_rank,
            "bar_global"      : self._bar_to_dict(o.bar_global),
            "montant_epargne" : o.montant_epargne,
            "montant_objectif": o.montant_objectif,
            "steps"           : [self._step_to_dict(s) for s in o.steps],
        }