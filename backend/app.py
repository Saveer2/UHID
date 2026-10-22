
from datetime import datetime
import secrets
from pathlib import Path
from functools import wraps
from routes.auth import auth_bp
#crucial for building custom decorators without losing function metadata
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request
)
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database.db import get_connection
from routes.patients import patients_bp
from routes.hospitals import hospitals_bp
from routes.doctors import doctors_bp
from routes.medical_records import medical_records_bp
from routes.admin import admin_bp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:5173"]
        }
    }
)

app.register_blueprint(auth_bp)
app.register_blueprint(patients_bp)
app.register_blueprint(hospitals_bp)
app.register_blueprint(doctors_bp)
app.register_blueprint(medical_records_bp)
app.register_blueprint(admin_bp)

def role_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            if get_jwt().get("role") not in allowed_roles:
                return jsonify({
                    "message": "Access forbidden"
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/frontend/<path:filename>")
def serve_frontend(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.get("/api/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    return jsonify({
        "message": "Admin access granted"
    }), 200


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "UHID backend is running"
    }), 200


@app.get("/api/health/database")
def database_health():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        return jsonify({
            "status": "ok",
            "database": "connected"
        }), 200

    except Exception:
        app.logger.exception("Database connection failed")

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 503

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "API endpoint not found"
    }), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)