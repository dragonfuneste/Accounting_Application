# --- CONFIGURATION GLOBALE ---
DATA_DIRECTORY = "_data"
LOG_FILE_NAME = "log.log"
COLUMNS_STRUCTURE = ["Date", "Intitule", "Categorie", "Classe", "Type", "Valeur"]

# --- VARIABLES DE TYPE (CONSTANTES) ---
REVENU = "Revenu"
DEPENSE = "Depense"
ECART = "Ecart"  # Assure-toi que cette ligne existe exactement comme ça

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

EN_COURS = "En cours"
TERMINE  = "Terminé"
EN_PAUSE = "En pause"
MAX_KEYWORDS = 10
_STOPWORDS   = {"les", "des", "une", "par", "sur", "pour", "avec", "chez", "via",
                "dan", "son", "ses", "mon", "mes", "ton", "tes", "nos", "vos"}
