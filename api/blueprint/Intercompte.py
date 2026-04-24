from flask import Blueprint, jsonify, request, current_app
from api.serializer.comptabilite_serial import comptabilite_serial

intercompte_routes = Blueprint('intercompte_routes', __name__)

@intercompte_routes.route('/api/intercompte/transfer', methods=['POST'])
def transfer():
    data = request.json
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    
    try:
        serial.virement_intercompte(
            idx_src=int(data['from_idx']),
            idx_dst=int(data['to_idx']),
            date_str=data['date'],
            raison=data['label'],
            montant_out=float(data['amount_out']), # Montant débité
            montant_in=float(data['amount_in'])    # Montant crédité
        )
        db_manager.save()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@intercompte_routes.route('/api/intercompte/chart-data', methods=['GET'])
def chart_data():
    src = request.args.get('src', type=int)
    dst = request.args.get('dst', type=int)
    db_manager = current_app.db_manager
    serial = comptabilite_serial(db_manager.comptabilite)
    
    # Récupération via le serial qui appelle cumulatif_intercompte
    stats = serial.get_intercompte_stats(src, dst)
    return jsonify(stats)