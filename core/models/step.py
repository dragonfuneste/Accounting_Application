from core.variables.variable import MAX_KEYWORDS,EN_COURS,EN_PAUSE,TERMINE
import uuid
from typing import Optional
class Step:
    def __init__(self, name: str, target: float, current_total: float = 0,
                 expenses_only: float = 0, deadline: str = None,
                 but: str = "", status: str = EN_COURS,
                 keywords: list[str] = None , max_keywords : int = MAX_KEYWORDS):
        self.id = str(uuid.uuid4())[:8]
        self.name          = name
        self.but           = but
        self.target        = target
        self.current_total = current_total
        self.expenses_only = expenses_only
        self.deadline      = deadline
        self.status        = status
        self.income_links  : dict[str, list[str]] = {}
        self.expense_links : dict[str, list[str]] = {}
        self.keywords      : list[str] = keywords or []   # ← manuels
        self.max_keywords = max_keywords

    @property
    def progress_percent(self) -> float:
        return round(self.current_total / self.target * 100, 1) if self.target else 0.0

    @property
    def net_balance(self) -> float:
        return self.current_total - self.expenses_only

    @property
    def remaining_to_find(self) -> float:
        return max(self.target - self.current_total, 0)

    @property
    def is_complete(self) -> bool:
        return self.current_total >= self.target

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        step = cls(
            name          = data["nom"],
            but           = data.get("but", ""),
            target        = data.get("argent_cible", 0),
            current_total = data.get("argent_actuel", 0),
            expenses_only = data.get("depenses_reelles", 0),
            deadline      = data.get("date_fin"),
            status        = data.get("etat", EN_COURS),
            keywords      = data.get("keywords", []),
            max_keywords = data.get("max_keywords", MAX_KEYWORDS),
        )
        step.income_links  = {e["nom"]: e["ids"] for e in data.get("ids_revenus", [])}
        step.expense_links = {e["nom"]: e["ids"] for e in data.get("ids_depenses", [])}
        return step

    def to_dict(self) -> dict:
        return {
            "nom"             : self.name,
            "but"             : self.but,
            "argent_cible"    : self.target,
            "argent_actuel"   : self.current_total,
            "depenses_reelles": self.expenses_only,
            "date_fin"        : self.deadline,
            "etat"            : self.status,
            "keywords"        : self.keywords,
            "max_keywords" : self.max_keywords,
            "ids_revenus"     : [{"nom": k, "ids": v} for k, v in self.income_links.items()],
            "ids_depenses"    : [{"nom": k, "ids": v} for k, v in self.expense_links.items()],
        }