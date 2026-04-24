from flask import Blueprint, jsonify, request, current_app
from api.serializer.compte_serial import compte_serial

account_details_routes = Blueprint('account_details_routes', __name__)

# --- Route pour le menu déroulant ---
@account_details_routes.route('/api/account/list', methods=['GET'])
def list_accounts():
    db_manager = current_app.db_manager
    return jsonify([
        {"index": i, "name": acc.account_name} 
        for i, acc in enumerate(db_manager.comptabilite.liste_compte)
    ])

# --- Route pour charger les données du tableau ---
@account_details_routes.route('/api/account/<int:index>/data', methods=['GET'])
def get_account_data(index):
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    return jsonify({"rows": serial.get_df()})

# --- Route pour AJOUTER une ligne ---
@account_details_routes.route('/api/account/<int:index>/line', methods=['POST'])
def add_line(index):
    data = request.json 
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    # L'ajout génère maintenant un real_index dans le Core (via compte.py)
    serial.add_line(data)
    db_manager.save()
    
    # On renvoie "success". 
    # Ton JS actuel fait un `await loadAccountData()` juste après l'ajout, 
    # donc il récupérera le nouvel ID automatiquement.
    return jsonify({"status": "success"})

# --- Route pour MODIFIER une ligne (Double-clic + Entrée) ---
@account_details_routes.route('/api/account/<int:index>/line/<string:line_id>', methods=['PUT'])
def update_line(index, line_id):
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    # Récupère les données JSON du JS
    data = request.json
    
    try:
        # On passe line_id (le Hash) à la place de l'ancien index numérique
        serial.modify_line(line_id, data) 
        db_manager.save()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# Dans Account.py
@account_details_routes.route('/api/account/<int:index>/filter', methods=['POST'])
def filter_account(index):
    data = request.json
    column = data.get('column')
    keyword = data.get('keyword')
    
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    serial.filtrer(column, keyword)
    
    # On renvoie les données filtrées pour mettre à jour le tableau
    return jsonify({"rows": serial.get_df()})
# Dans Account.py
@account_details_routes.route('/api/account/<int:index>/sort', methods=['POST'])
def sort_account(index):
    data = request.json
    column = data.get('column')
    # On force True (croissant) si 'croissant' est None ou non défini
    croissant = data.get('croissant')
    if croissant is None:
        croissant = True 
    
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    serial.trier(column, croissant)
    return jsonify({"rows": serial.get_df()})

@account_details_routes.route('/api/account/<int:index>/line/<string:line_id>', methods=['DELETE'])
def delete_line(index, line_id):
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    try:
        # On utilise le Hash pour la suppression
        serial.delete_line(line_id)
        db_manager.save()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500