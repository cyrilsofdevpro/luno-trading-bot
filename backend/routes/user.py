from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User
from backend.db.init_db import get_session

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/luno/connect', methods=['POST'])
@jwt_required()
def connect_luno():
    user_id = get_jwt_identity()
    data = request.get_json()
    api_key = data.get('luno_api_key')
    api_secret = data.get('luno_api_secret')
    if not api_key or not api_secret:
        return jsonify({'error': 'Missing Luno API credentials'}), 400
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.luno_api_key = api_key
    user.luno_api_secret = api_secret
    session.commit()
    return jsonify({'message': 'Luno API keys saved'})

@user_bp.route('/luno/status', methods=['GET'])
@jwt_required()
def luno_status():
    user_id = get_jwt_identity()
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    connected = bool(user.luno_api_key and user.luno_api_secret)
    return jsonify({'connected': connected})

@user_bp.route('/luno/update', methods=['PUT'])
@jwt_required()
def update_luno():
    user_id = get_jwt_identity()
    data = request.get_json()
    api_key = data.get('luno_api_key')
    api_secret = data.get('luno_api_secret')
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.luno_api_key = api_key
    user.luno_api_secret = api_secret
    session.commit()
    return jsonify({'message': 'Luno API keys updated'})
