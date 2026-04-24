from flask import Blueprint, jsonify, request, current_app
from api.serializer.comptabilite_serial import comptabilite_serial

stats_routes = Blueprint('stats_routes', __name__)

@stats_routes.route('/api/stats/repartition', methods=['GET'])
def get_repartition():
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    
    acc_idx = request.args.get('account', type=int)
    start = request.args.get('start') # Format YYYY-MM-DD
    end = request.args.get('end')     # Format YYYY-MM-DD
    
    if acc_idx is None:
        return jsonify({"error": "Compte non spécifié"}), 400
        
    # On passe les dates au serial
    data = serial.get_stats_repartition(acc_idx, start, end)
    return jsonify(data)
@stats_routes.route('/api/stats/sankey', methods=['GET'])
def get_sankey():
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    
    acc_idx = request.args.get('account', type=int)
    start = request.args.get('start') # Récupère la date de début
    end = request.args.get('end')     # Récupère la date de fin
    
    data = serial.get_sankey_data(acc_idx, start, end)
    return jsonify(data)