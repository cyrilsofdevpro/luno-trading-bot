from flask import Flask
from flask_jwt_extended import JWTManager
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
jwt = JWTManager(app)

# Import routes (to be implemented)
from backend.routes.auth import auth_bp
from backend.routes.user import user_bp
from backend.routes.dashboard import dashboard_bp
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(dashboard_bp)

@app.route('/')
def index():
    return {'status': 'ok', 'message': 'Luno Bot Platform Backend'}

if __name__ == '__main__':
    app.run(debug=True)
