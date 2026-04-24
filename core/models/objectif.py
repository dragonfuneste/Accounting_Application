
from core.variables.variable import MAX_KEYWORDS,EN_COURS,EN_PAUSE,TERMINE
from core.models.step import Step
from typing import Optional
import uuid
class Objective:
    def __init__(self, name: str, but: str = "", importance: int = 1,
                 deadline: str = None, logo: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name       = name
        self.but        = but
        self.importance = importance
        self.deadline   = deadline
        self.logo       = logo
        self.steps      : list[Step] = []

    @property
    def total_target(self)   -> float: return sum(s.target        for s in self.steps)
    @property
    def total_saved(self)    -> float: return sum(s.current_total for s in self.steps)
    @property
    def total_expenses(self) -> float: return sum(s.expenses_only for s in self.steps)
    @property
    def progress_percent(self) -> float:
        return round(self.total_saved / self.total_target * 100, 1) if self.total_target else 0.0

    def add_step(self, step: Step) -> None:
        self.steps.append(step)

    def next_open_step(self, after: Step) -> Optional[Step]:
        """Retourne la prochaine étape EN_COURS après `after`."""
        found = False
        for s in self.steps:
            if found and s.status == EN_COURS and not s.is_complete:
                return s
            if s is after:
                found = True
        return None

    @classmethod
    def from_dict(cls, data: dict) -> "Objective":
        obj = cls(
            name       = data["nom"],
            but        = data.get("but", ""),
            importance = data.get("note_importance", 1),
            deadline   = data.get("echance maximal"),
            logo       = data.get("Emoji_logo_projet", ""),
        )
        for s in data.get("steps", []):
            obj.steps.append(Step.from_dict(s))
        return obj

    def to_dict(self) -> dict:
        return {
            "nom"              : self.name,
            "Emoji_logo_projet": self.logo,
            "but"              : self.but,
            "note_importance"  : self.importance,
            "echance maximal"  : self.deadline,
            "steps"            : [s.to_dict() for s in self.steps],
        }
