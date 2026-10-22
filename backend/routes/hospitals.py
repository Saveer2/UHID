
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import get_connection
from middleware.permissions import roles_required

hospitals_bp = Blueprint("hospitals", __name__, url_prefix="/api/hospitals")


@hospitals_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_hospital():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    address = data.get("address")
    phone = data.get("phone")
    email = data.get("email")

    if not isinstance(name, str) or not name.strip():
        return jsonify({
            "success": False,
            "message": "Hospital name is required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO hospitals (name, address, phone, email)
            VALUES (%s, %s, %s, %s)
            """,
            (name.strip(), address, phone, email)
        )

        connection.commit()
        hospital_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Hospital registered successfully",
            "hospital_id": hospital_id
        }), 201

    except Exception:
        if connection is not None:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to register hospital"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@hospitals_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("admin", "hospital_admin", "doctor")
def get_hospitals():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT hospital_id, name, address, phone, email, created_at
            FROM hospitals
            ORDER BY hospital_id DESC
            """
        )

        hospitals = cursor.fetchall()

        return jsonify({
            "success": True,
            "hospitals": hospitals
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to retrieve hospitals"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
