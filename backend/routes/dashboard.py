from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User
from backend.db.init_db import get_session

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    session = get_session()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    connected = bool(user.luno_api_key and user.luno_api_secret)
    # Trading history can be added here if available
    return jsonify({
        'name': user.name,
        'email': user.email,
        'luno_connected': connected,
        # 'trading_history': []
    })
