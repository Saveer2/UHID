from flask import Blueprint, jsonify, request
from database.db import get_connection
# Import your JWT or authentication middleware decorator if you use one
# from middleware.permissions import token_required, roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.get("/users")
def get_all_system_users():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Fetch all users with their roles
        cursor.execute("SELECT user_id, name, email, role, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()

        # Fetch detailed patient & doctor stats/records
        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()

        cursor.execute("SELECT * FROM doctors")
        doctors = cursor.fetchall()

        return jsonify({
            "success": True,
            "users": users,
            "patients": patients,
            "doctors": doctors
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()