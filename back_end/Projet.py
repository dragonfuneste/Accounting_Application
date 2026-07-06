import json
import os
import uuid
from datetime import date, datetime
from typing import Optional


ETATS_VALIDES = ["non commencé", "En cours", "Terminé", "Annulé"]


class Projet:
    def __init__(self, data: dict):
        self.id       = data.get("id") or str(uuid.uuid4())
        self.nom      = data.get("nom_projet", "")
        self.emoji    = data.get("Emoji_logo_projet", "📁")
        self.objectif = data.get("objectif", "")
        self.priorite = int(data.get("priorite", 1))
        self.date_fin = data.get("date_fin")
        self.etapes   = [Etape(e) for e in data.get("etapes", [])]

    def cible_totale(self) -> float:
        return sum(e.cible for e in self.etapes)

    def montant_realise(self, cur) -> float:
        return sum(e.montant_realise(cur) for e in self.etapes)

    def progression(self, cur) -> float:
        cible = self.cible_totale()
        if cible == 0: return 100.0
        return min(100.0, round(self.montant_realise(cur) / cible * 100, 1))

    def etat_calcule(self) -> str:
        if not self.etapes: return "non commencé"
        if all(e.etat == "Terminé" for e in self.etapes): return "Terminé"
        if any(e.etat == "En cours" for e in self.etapes): return "En cours"
        return "non commencé"

    def est_en_retard(self) -> bool:
        if not self.date_fin: return False
        return date.today() > datetime.strptime(self.date_fin, "%Y-%m-%d").date()

    def priorite_dynamique(self) -> float:
        urgence = 0.0
        if self.date_fin:
            jours = (datetime.strptime(self.date_fin, "%Y-%m-%d").date() - date.today()).days
            if   jours <= 0:   urgence = 1.0
            elif jours <= 30:  urgence = 0.9
            elif jours <= 90:  urgence = 0.7
            elif jours <= 180: urgence = 0.5
            elif jours <= 365: urgence = 0.3
            else:              urgence = 0.1
        return round(0.5 * (1 / max(self.priorite, 1)) + 0.5 * urgence, 4)

    def to_dict(self, cur=None) -> dict:
        return {
            "id": self.id, "nom_projet": self.nom, "Emoji_logo_projet": self.emoji,
            "objectif": self.objectif, "priorite": self.priorite, "date_fin": self.date_fin,
            "priorite_dynamique": self.priorite_dynamique(),
            "cible_totale": self.cible_totale(),
            "montant_realise": self.montant_realise(cur) if cur else 0,
            "progression": self.progression(cur) if cur else 0,
            "etat_calcule": self.etat_calcule(),
            "est_en_retard": self.est_en_retard(),
            "etapes": [e.to_dict(cur) for e in self.etapes],
        }

    def raw_dict(self) -> dict:
        return {
            "id": self.id, "nom_projet": self.nom, "Emoji_logo_projet": self.emoji,
            "objectif": self.objectif, "priorite": self.priorite, "date_fin": self.date_fin,
            "etapes": [e.raw_dict() for e in self.etapes],
        }


class Etape:
    def __init__(self, data: dict):
        self.id           = data.get("id") or str(uuid.uuid4())
        self.nom          = data.get("nom_etape", "")
        self.objectif     = data.get("objectif", "")
        self.cible        = float(data.get("cible", 0))
        self.date_fin     = data.get("date_fin")
        self.etat         = data.get("etat", "non commencé")
        self.priorite     = int(data.get("priorite", 1))
        self.transactions = [
            {"id_transaction": t["id_transaction"],
             "pourcentage_lie": float(t.get("pourcentage_lié_au_projet", 100))}
            for t in data.get("transactions", [])
        ]
        self.keywords = data.get("keywords_pour_propose_transactions", [])

    def montant_realise(self, cur) -> float:
        total = 0.0
        for t in self.transactions:
            cur.execute("SELECT valeur FROM transactions WHERE id=?", (t["id_transaction"],))
            row = cur.fetchone()
            if row:
                total += row[0] * (t["pourcentage_lie"] / 100)
        return round(total, 2)

    def progression(self, cur) -> float:
        if self.cible == 0: return 100.0
        return min(100.0, round(self.montant_realise(cur) / self.cible * 100, 1))

    def est_en_retard(self) -> bool:
        if self.etat in ("Terminé", "Annulé") or not self.date_fin: return False
        return date.today() > datetime.strptime(self.date_fin, "%Y-%m-%d").date()

    def to_dict(self, cur=None) -> dict:
        return {
            "id": self.id, "nom_etape": self.nom, "objectif": self.objectif,
            "cible": self.cible, "date_fin": self.date_fin, "etat": self.etat,
            "priorite": self.priorite, "transactions": self.transactions,
            "keywords": self.keywords,
            "montant_realise": self.montant_realise(cur) if cur else 0,
            "progression": self.progression(cur) if cur else 0,
            "est_en_retard": self.est_en_retard(),
        }

    def raw_dict(self) -> dict:
        return {
            "id": self.id, "nom_etape": self.nom, "objectif": self.objectif,
            "cible": self.cible, "date_fin": self.date_fin, "etat": self.etat,
            "priorite": self.priorite,
            "transactions": [{"id_transaction": t["id_transaction"],
                               "pourcentage_lié_au_projet": t["pourcentage_lie"]}
                             for t in self.transactions],
            "keywords_pour_propose_transactions": self.keywords,
        }


class ProjetManager:
    def __init__(self, filepath: str, db_connection):
        self.filepath = filepath
        self.db       = db_connection
        self._projets = []
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._projets = [Projet(p) for p in data]
        else:
            self._projets = []

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([p.raw_dict() for p in self._projets], f, ensure_ascii=False, indent=2)

    def _cur(self):
        return self.db.cursor()

    # ── Projets ────────────────────────────────────────────────────
    def list_projets(self) -> list:
        result = [p.to_dict(self._cur()) for p in self._projets]
        result.sort(key=lambda x: -x["priorite_dynamique"])
        return result

    def get_projet(self, pid: str) -> Optional[Projet]:
        return next((p for p in self._projets if p.id == pid), None)

    def add_projet(self, data: dict) -> dict:
        data["id"] = str(uuid.uuid4())
        p = Projet(data)
        self._projets.append(p)
        self._save()
        return p.to_dict(self._cur())

    def update_projet(self, pid: str, data: dict) -> Optional[dict]:
        p = self.get_projet(pid)
        if not p: return None
        p.nom      = data.get("nom_projet", p.nom)
        p.emoji    = data.get("Emoji_logo_projet", p.emoji)
        p.objectif = data.get("objectif", p.objectif)
        p.priorite = int(data.get("priorite", p.priorite))
        p.date_fin = data.get("date_fin", p.date_fin)
        self._save()
        return p.to_dict(self._cur())

    def delete_projet(self, pid: str) -> bool:
        before = len(self._projets)
        self._projets = [p for p in self._projets if p.id != pid]
        changed = len(self._projets) < before
        if changed: self._save()
        return changed

    # ── Étapes ────────────────────────────────────────────────────
    def add_etape(self, pid: str, data: dict) -> Optional[dict]:
        p = self.get_projet(pid)
        if not p: return None
        data["id"] = str(uuid.uuid4())
        e = Etape(data)
        p.etapes.append(e)
        self._save()
        return e.to_dict(self._cur())

    def update_etape(self, pid: str, eid: str, data: dict) -> Optional[dict]:
        p = self.get_projet(pid)
        if not p: return None
        e = next((e for e in p.etapes if e.id == eid), None)
        if not e: return None
        e.nom      = data.get("nom_etape", e.nom)
        e.objectif = data.get("objectif", e.objectif)
        e.cible    = float(data.get("cible", e.cible))
        e.date_fin = data.get("date_fin", e.date_fin)
        e.etat     = data.get("etat", e.etat)
        e.priorite = int(data.get("priorite", e.priorite))
        self._save()
        return e.to_dict(self._cur())

    def delete_etape(self, pid: str, eid: str) -> bool:
        p = self.get_projet(pid)
        if not p: return False
        before = len(p.etapes)
        p.etapes = [e for e in p.etapes if e.id != eid]
        changed = len(p.etapes) < before
        if changed: self._save()
        return changed

    # ── Transactions ───────────────────────────────────────────────
    def pct_utilise(self, tx_id: int) -> float:
        return sum(
            t["pourcentage_lie"]
            for p in self._projets for e in p.etapes
            for t in e.transactions if t["id_transaction"] == tx_id
        )

    def add_transaction_etape(self, pid: str, eid: str, tx_id: int, pct: float) -> dict:
        p = self.get_projet(pid)
        if not p: return {"error": "Projet introuvable"}
        e = next((e for e in p.etapes if e.id == eid), None)
        if not e: return {"error": "Étape introuvable"}
        dispo = 100.0 - self.pct_utilise(tx_id)
        if pct > dispo:
            return {"error": f"Seulement {dispo:.1f}% disponible pour cette transaction"}
        existing = next((t for t in e.transactions if t["id_transaction"] == tx_id), None)
        if existing:
            existing["pourcentage_lie"] = min(100.0, existing["pourcentage_lie"] + pct)
        else:
            e.transactions.append({"id_transaction": tx_id, "pourcentage_lie": pct})
        # Refresh keywords
        cur = self._cur()
        classes = []
        for t in e.transactions:
            cur.execute("SELECT classe FROM transactions WHERE id=?", (t["id_transaction"],))
            row = cur.fetchone()
            if row and row[0] and row[0] not in classes:
                classes.append(row[0])
        e.keywords = classes
        self._save()
        return e.to_dict(self._cur())

    def remove_transaction_etape(self, pid: str, eid: str, tx_id: int) -> dict:
        p = self.get_projet(pid)
        if not p: return {"error": "Projet introuvable"}
        e = next((e for e in p.etapes if e.id == eid), None)
        if not e: return {"error": "Étape introuvable"}
        e.transactions = [t for t in e.transactions if t["id_transaction"] != tx_id]
        self._save()
        return e.to_dict(self._cur())

    def tx_disponibilite(self, tx_id: int) -> dict:
        utilise = self.pct_utilise(tx_id)
        return {"tx_id": tx_id, "utilise": round(utilise, 1), "restant": round(max(0.0, 100 - utilise), 1)}

    def search_transactions(self, keywords: list, compte_id: int = None) -> list:
        cur = self._cur()
        # Si aucun keyword → retourner toutes les transactions
        if not keywords or all(k.strip() == '' for k in keywords):
            q = "SELECT id,compte_id,date,intitule,categorie,classe,est_revenu,valeur FROM transactions"
            params = []
            if compte_id:
                q += " WHERE compte_id=?"
                params.append(compte_id)
            q += " ORDER BY date DESC LIMIT 200"
            cur.execute(q, params)
            cols = ['id','compte_id','date','intitule','categorie','classe','est_revenu','valeur']
            return [dict(zip(cols, r)) for r in cur.fetchall()]

        # Sinon filtrer par keywords
        conds  = " OR ".join("classe LIKE ? OR categorie LIKE ? OR intitule LIKE ?" for _ in keywords)
        params = []
        for kw in keywords:
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
        q = f"SELECT id,compte_id,date,intitule,categorie,classe,est_revenu,valeur FROM transactions WHERE ({conds})"
        if compte_id:
            q += " AND compte_id=?"
            params.append(compte_id)
        q += " ORDER BY date DESC LIMIT 200"
        cur.execute(q, params)
        cols = ['id','compte_id','date','intitule','categorie','classe','est_revenu','valeur']
        return [dict(zip(cols, r)) for r in cur.fetchall()]