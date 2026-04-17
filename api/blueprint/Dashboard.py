from flask import Blueprint, jsonify, request, current_app
from api.serializer.comptabilite_serial import comptabilite_serial

compta_routes = Blueprint('compta_routes', __name__)

# --- ROUTES EXISTANTES ---

@compta_routes.route('/api/dashboard/accounts', methods=['GET'])
def get_accounts_table():
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    return jsonify(serial.get_account_information())

@compta_routes.route('/api/dashboard/stats', methods=['GET'])
def get_global_stats():
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    return jsonify(serial.get_account_information_all())

@compta_routes.route('/api/dashboard/account/add', methods=['POST'])
def add_account():
    data = request.json
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    serial.create_account(data.get('name'), data.get('devise'))
    db_manager.save()
    return jsonify({"status": "success"})

@compta_routes.route('/api/dashboard/account/<int:index>/delete', methods=['DELETE'])
def remove_account(index):
    db_manager = current_app.db_manager
    if not db_manager.comptabilite.check_index(index):
        return jsonify({"status": "error", "message": "Index invalide"}), 404
    serial = comptabilite_serial(db_manager.comptabilite)
    serial.delete_account(index)
    db_manager.save()
    return jsonify({"status": "success"})
# Dans ton fichier api/blueprint/Dashboard.py

@compta_routes.route('/api/dashboard/account/<int:index>/modify', methods=['PUT'])
def modify_account(index):
    data = request.json
    name = data.get('name')
    devise = data.get('devise')
    
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    try:
        # On appelle la méthode du serial (que tu as déjà dans ton fichier)
        serial.modify_account(index, name, devise)
        db_manager.save() # Très important pour sauvegarder dans le Excel/CSV
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    

@compta_routes.route('/api/dashboard/account/<int:index>/toggle-status', methods=['POST'])
def toggle_status(index):
    db_manager = current_app.db_manager
    if db_manager.comptabilite.check_index(index):
        compte_obj = db_manager.comptabilite.liste_compte[index]
        compte_obj.state = not compte_obj.state 
        db_manager.save()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# --- NOUVELLE ROUTE POUR LE GRAPHIQUE ---

import pandas as pd  # <--- Assure-toi que c'est bien présent en haut

@compta_routes.route('/api/dashboard/evolution', methods=['GET'])
def get_global_evolution():
    db_manager = current_app.db_manager
    period = request.args.get('period', 'all')
    
    names, datasets = db_manager.comptabilite.compute_statistic_temporel(period=period)
    
    # 1. Créer un index global avec toutes les dates uniques de TOUS les comptes
    all_dates = pd.Index([])
    valid_datasets = []
    
    for ds in datasets:
        if ds is not None and not ds.empty:
            # On s'assure que l'index est bien en datetime pour l'union
            if not isinstance(ds.index, pd.DatetimeIndex):
                ds.index = pd.to_datetime(ds.index)
            all_dates = all_dates.union(ds.index)
            valid_datasets.append(ds)
        else:
            valid_datasets.append(None)
    
    # Si aucun compte n'a de données, on renvoie du vide propre
    if all_dates.empty:
        return jsonify({"labels": [], "datasets": []})

   # On trie l'axe final
    all_dates = all_dates.sort_values()
    
    # FORCE la conversion en DatetimeIndex pour débloquer strftime
    if not all_dates.empty:
        all_dates = pd.to_datetime(all_dates) # Cette ligne répare l'AttributeError

    output_datasets = []
    for i in range(len(names)):
        if datasets[i] is not None and not datasets[i].empty:
            # Reindex et alignement (ffill propage le solde, fillna(0) gère le début)
            series_aligned = datasets[i].reindex(all_dates).ffill().fillna(0)
            
            output_datasets.append({
                "account": names[i],
                "values": series_aligned.tolist()
            })
    
    # Maintenant strftime fonctionnera car all_dates est un DatetimeIndex
    return jsonify({
        "labels": all_dates.strftime('%d/%m/%Y').tolist() if not all_dates.empty else [],
        "datasets": output_datasets
    })