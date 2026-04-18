# api/blueprint/prediction.py

from flask import Blueprint, jsonify, request, current_app
from api.serializer.compte_serial import compte_serial
from core.services.analyser_compte import analyser_compte

prediction_routes = Blueprint('prediction_routes', __name__)

@prediction_routes.route('/api/prediction/<int:index>/full', methods=['GET'])
def get_prediction_analysis(index):
    db_manager = current_app.db_manager
    if not db_manager.comptabilite.check_index(index):
        return jsonify({"status": "error", "message": "Index de compte invalide"}), 404
        
    # RÉCUPÉRATION DU SEUIL : On récupère ?probabilite=XX dans l'URL
    seuil = request.args.get('probabilite', default=50, type=int)
        
    compte_obj = db_manager.comptabilite.liste_compte[index]
    serial = compte_serial(compte_obj)
    
    try:
        # On passe le seuil au serial
        data = serial.get_predictions_data(seuil)
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@prediction_routes.route('/api/prediction/<int:index>/derives', methods=['GET'])
def get_account_derives(index):
    """
    Route spécifique pour détecter si le rythme de dépense actuel 
    dépasse les prédictions (Analyse de dérive).
    """
    db_manager = current_app.db_manager
    if not db_manager.comptabilite.check_index(index):
        return jsonify({"status": "error", "message": "Compte introuvable"}), 404
        
    compte_obj = db_manager.comptabilite.liste_compte[index]
    analyseur = analyser_compte(compte_obj)
    
    try:
        # Calcul des dérives basé sur les données réelles vs prédictions
        preds_brutes = analyseur.Generer_prediction()
        df_derives = analyseur.detecter_derives(compte_obj.df, preds_brutes)
        
        return jsonify({
            "status": "success",
            "derives": df_derives.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500