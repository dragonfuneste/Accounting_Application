from flask import Blueprint, jsonify, request, current_app
from core.models.objectif import Objective
from core.models.step import Step
from api.serializer.objective_serial import ProjectManagementSerial

projects_routes = Blueprint('projects_routes', __name__)

# ── GET ALL PROJECTS ──────────────────────────────────────────────────────────
@projects_routes.route('/api/projects', methods=['GET'])
def get_projects():
    db_manager = current_app.db_manager
    db_manager.project_management.compute()
    serial = ProjectManagementSerial(db_manager.projects, db_manager.project_management)
    return jsonify(serial.to_dict())


# ── POST create objective ─────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/add', methods=['POST'])
def add_objective():
    data = request.json
    db_manager = current_app.db_manager
    obj = Objective(
        name       = data.get('name', 'Nouvel objectif'),
        but        = data.get('but', ''),
        importance = int(data.get('importance', 1)),
        deadline   = data.get('deadline'),
        logo       = data.get('logo', '🎯'),
    )
    db_manager.projects.create_objective(obj)
    db_manager.save()
    return jsonify({"status": "success", "id": obj.id})


# ── POST create step ──────────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/step/add', methods=['POST'])
def add_step(oid):
    data = request.json
    db_manager = current_app.db_manager
    step = Step(
        name     = data.get('name', 'Nouvelle étape'),
        target   = float(data.get('target', 0)),
        but      = data.get('but', ''),
        deadline = data.get('deadline'),
    )
    result = db_manager.projects.create_step(oid, step)
    if result is not None:
        db_manager.save()
        return jsonify({"status": "success", "id": step.id})
    return jsonify({"status": "error", "message": "Objective not found"}), 404


# ── DELETE objective ──────────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/delete', methods=['DELETE'])
def delete_objective(oid):
    db_manager = current_app.db_manager
    if db_manager.projects.delete_objective(oid):
        db_manager.save()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Objective not found"}), 404


# ── DELETE step ───────────────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/step/<string:sid>/delete', methods=['DELETE'])
def delete_step(oid, sid):
    db_manager = current_app.db_manager
    if db_manager.projects.delete_step(oid, sid):
        db_manager.save()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Step not found"}), 404


# ── GET liste des comptes ─────────────────────────────────────────────────────
@projects_routes.route('/api/projects/accounts', methods=['GET'])
def get_accounts():
    """Retourne la liste des comptes actifs disponibles pour la liaison."""
    db_manager = current_app.db_manager
    accounts = [
        {"name": c.account_name, "devise": c.devise}
        for c in db_manager.comptabilite.liste_compte
        if c.state
    ]
    return jsonify(accounts)


# ── GET transactions d'un compte ─────────────────────────────────────────────
@projects_routes.route('/api/projects/accounts/<string:account_name>/transactions', methods=['GET'])
def get_transactions(account_name):
    """
    Retourne les transactions d'un compte avec flag is_linked.
    Query params : oid, sid, search, type (Revenu|Depense)
    """
    from core.variables.variable import COLUMNS_STRUCTURE, DEPENSE, REVENU
    import pandas as pd

    db_manager  = current_app.db_manager
    oid         = request.args.get('oid', '')
    sid         = request.args.get('sid', '')
    search      = request.args.get('search', '').strip().lower()
    type_filter = request.args.get('type', '')

    account = next(
        (c for c in db_manager.comptabilite.liste_compte if c.account_name == account_name),
        None
    )
    if account is None:
        return jsonify({"status": "error", "message": "Compte introuvable"}), 404

    # Récupérer les IDs déjà liés à cette step
    linked_income  = set()
    linked_expense = set()
    if oid and sid:
        step = db_manager.projects.get_step(oid, sid)
        if step:
            for ids in step.income_links.get(account_name, []):
                linked_income.add(ids)
            for ids in step.expense_links.get(account_name, []):
                linked_expense.add(ids)

    col_date      = COLUMNS_STRUCTURE[0]
    col_intitule  = COLUMNS_STRUCTURE[1]
    col_categorie = COLUMNS_STRUCTURE[2]
    col_classe    = COLUMNS_STRUCTURE[3]
    col_type      = COLUMNS_STRUCTURE[4]
    col_montant   = COLUMNS_STRUCTURE[5]

    df = account.df.copy()

    # Filtre type
    if type_filter in (REVENU, DEPENSE):
        df = df[df[col_type] == type_filter]

    # Filtre recherche
    if search:
        mask = (
            df[col_intitule].astype(str).str.lower().str.contains(search, na=False) |
            df[col_categorie].astype(str).str.lower().str.contains(search, na=False) |
            df[col_classe].astype(str).str.lower().str.contains(search, na=False)
        )
        df = df[mask]

    # Tri par date décroissante
    try:
        df['_sort'] = pd.to_datetime(df[col_date].astype(str), dayfirst=True, errors='coerce')
        df = df.sort_values('_sort', ascending=False).drop(columns=['_sort'])
    except Exception:
        pass

    transactions = []
    for _, row in df.iterrows():
        tid      = str(row.get('real_index', ''))
        tx_type  = str(row.get(col_type, ''))
        is_depense = tx_type == DEPENSE
        transactions.append({
            "tid"      : tid,
            "date"     : str(row.get(col_date, '')),
            "intitule" : str(row.get(col_intitule, '')),
            "categorie": str(row.get(col_categorie, '')),
            "classe"   : str(row.get(col_classe, '')),
            "type"     : tx_type,
            "montant"  : float(row.get(col_montant, 0) or 0),
            "depense"  : is_depense,
            "is_linked": tid in (linked_expense if is_depense else linked_income),
        })

    return jsonify(transactions)


# ── POST link transaction ─────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/step/<string:sid>/link', methods=['POST'])
def link_transaction(oid, sid):
    """
    Body JSON : { account_name, tid, depense: bool }
    Lie la transaction et recalcule (via apply_transaction).
    """
    data         = request.json
    account_name = data.get('account_name')
    tid          = data.get('tid')
    depense      = bool(data.get('depense', False))

    if not account_name or not tid:
        return jsonify({"status": "error", "message": "account_name et tid requis"}), 400

    db_manager = current_app.db_manager
    result = db_manager.project_management.apply_transaction(oid, sid, account_name, tid, depense)
    db_manager.save()

    return jsonify({
        "status"    : "success",
        "attributed": result.attributed,
        "overflow"  : result.overflow,
        "overflowed": result.overflowed,
    })


# ── DELETE unlink transaction ─────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/step/<string:sid>/link', methods=['DELETE'])
def unlink_transaction(oid, sid):
    """
    Body JSON : { account_name, tid, depense: bool }
    Délie la transaction et recalcule.
    """
    data         = request.json
    account_name = data.get('account_name')
    tid          = data.get('tid')
    depense      = bool(data.get('depense', False))

    if not account_name or not tid:
        return jsonify({"status": "error", "message": "account_name et tid requis"}), 400

    db_manager = current_app.db_manager
    ok = db_manager.projects.unlink_transaction(oid, sid, account_name, tid, depense)
    if ok:
        db_manager.project_management.compute()
        db_manager.save()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Lien introuvable"}), 404


# ── GET recommendations ───────────────────────────────────────────────────────
@projects_routes.route('/api/projects/objective/<string:oid>/step/<string:sid>/recommend', methods=['GET'])
def recommend(oid, sid):
    account_name = request.args.get('account_name')
    max_results  = int(request.args.get('max', 10))
    management   = current_app.db_manager.project_management
    results      = management.recommendation(oid, sid, account_name, max_results)

    return jsonify([{
        "score"   : r["score"],
        "tid"     : r["transaction"].get("real_index"),
        "intitule": r["transaction"].get("Intitule"),
        "montant" : r["transaction"].get("Montant"),
        "date"    : r["transaction"].get("Date"),
    } for r in results])