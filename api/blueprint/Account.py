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
    """Ajoute une ligne vide dans le tableau du compte index."""
    # 1. Récupération des données envoyées par le JS (le dictionnaire de colonnes vides)
    data = request.json 
    
    # 2. Action sur le Core
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    # On appelle l'ajout
    serial.add_line(data)
    
    # 3. Persistance immédiate (Comme dans ton Dashboard !)
    db_manager.save()
    
    return jsonify({"status": "success", "message": "Ligne ajoutée avec succès."})

# --- Route pour MODIFIER une ligne (Double-clic + Entrée) ---
@account_details_routes.route('/api/account/<int:index>/line/<int:line_idx>', methods=['PUT'])
def update_line(index, line_idx):
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    # Récupère les données JSON du JS
    data = request.json
    
    try:
        serial.modify_line(line_idx, data) # Utilise la méthode de compte_serial
        db_manager.save()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error"}), 500
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
    # croissant sera True, False, ou None
    croissant = data.get('croissant')
    
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    serial.trier(column, croissant)
    return jsonify({"rows": serial.get_df()})

@account_details_routes.route('/api/account/<int:index>/line/<int:line_idx>', methods=['DELETE'])
def delete_line(index, line_idx):
    db_manager = current_app.db_manager
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    serial.delete_line(line_idx)
    db_manager.save()
    return jsonify({"status": "success"})