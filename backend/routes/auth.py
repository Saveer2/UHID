from datetime import datetime
import secrets

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_connection

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

latest_hardware_session = {"token": None, "user": None}

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    date_of_birth = data.get("date_of_birth") or None
    gender = str(data.get("gender", "")).strip() or None
    phone = str(data.get("phone", "")).strip() or None
    address = str(data.get("address", "")).strip() or None

    if not name or not email or not isinstance(password, str):
        return jsonify({
            "message": "Name, email and password are required"
        }), 400

    if len(name) > 100 or len(email) > 150:
        return jsonify({
            "message": "Name or email is too long"
        }), 400

    if len(password) < 8 or len(password) > 128:
        return jsonify({
            "message": "Password must be between 8 and 128 characters"
        }), 400

    password_hash = generate_password_hash(password)
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        uhid = (
            "UHID"
            + datetime.now().strftime("%Y%m%d")
            + secrets.token_hex(4).upper()
        )

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'patient')
            """,
            (name, email, password_hash)
        )

        user_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO patients
                (user_id, uhid, date_of_birth, gender, phone, address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, uhid, date_of_birth, gender, phone, address)
        )

        connection.commit()

        return jsonify({
            "message": "Patient registered successfully",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": "patient",
                "uhid": uhid
            }
        }), 201

    except IntegrityError as error:
        if connection is not None:
            connection.rollback()

        if error.errno == 1062:
            return jsonify({
                "message": "Email already exists or UHID conflict occurred"
            }), 409

        return jsonify({"message": "Registration failed"}), 500

    except Exception:
        if connection is not None:
            connection.rollback()

        return jsonify({"message": "Registration failed"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not isinstance(password, str) or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, name, email, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        access_token = create_access_token(
            identity=str(user["user_id"]),
            additional_claims={"role": user["role"]}
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        }), 200

    except Exception:
        return jsonify({"message": "Login failed"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@auth_bp.put("/change-password")
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    
    if not old_password or not new_password:
        return jsonify({"message": "Current and new passwords are required"}), 400
        
    if len(new_password) < 8 or len(new_password) > 128:
        return jsonify({"message": "New password must be between 8 and 128 characters"}), 400
        
    connection = None
    cursor = None
    
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user["password_hash"], old_password):
            return jsonify({"message": "Incorrect current password"}), 401
            
        new_password_hash = generate_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (new_password_hash, user_id)
        )
        connection.commit()
        
        return jsonify({"message": "Password updated successfully"}), 200

    except Exception:
        if connection is not None:
            connection.rollback()
        return jsonify({"message": "Failed to update password"}), 500
        
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@auth_bp.post("/register-doctor")
def register_doctor():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    
    license_number = str(data.get("license_number", "")).strip()
    specialization = str(data.get("specialization", "")).strip()
    hospital_id = data.get("hospital_id") or None

    if not name or not email or not password or not license_number:
        return jsonify({"success": False, "message": "Name, email, password, and license number are required"}), 400

    if len(password) < 8 or len(password) > 128:
        return jsonify({"success": False, "message": "Password must be between 8 and 128 characters"}), 400

    password_hash = generate_password_hash(password)
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'doctor')
            """,
            (name, email, password_hash)
        )
        user_id = cursor.lastrowid

        if hospital_id is not None and hospital_id != "":
            try:
                hospital_id = int(hospital_id)
            except ValueError:
                hospital_id = None
        else:
            hospital_id = None

        cursor.execute(
            """
            INSERT INTO doctors (user_id, hospital_id, specialization, license_number)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, hospital_id, specialization, license_number)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Doctor registered successfully",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": "doctor"
            }
        }), 201

    except IntegrityError as error:
        if connection:
            connection.rollback()
        if error.errno == 1062:
            return jsonify({"success": False, "message": "Email or license number already exists"}), 409
        return jsonify({"success": False, "message": "Registration failed"}), 500

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@auth_bp.post("/register-admin")
def register_admin():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    admin_key = data.get("admin_key", "")

    if admin_key != "UHID_ADMIN_SECRET_2026":
        return jsonify({"success": False, "message": "Invalid admin security key"}), 403

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email, and password are required"}), 400

    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400

    password_hash = generate_password_hash(password)
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'admin')
            """,
            (name, email, password_hash)
        )
        connection.commit()
        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Admin account created successfully",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": "admin"
            }
        }), 201

    except IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"success": False, "message": "Email already exists"}), 409

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@auth_bp.post("/rfid-login")
def rfid_login():
    data = request.get_json(silent=True) or {}
    rfid_uid = str(data.get("rfid_uid", "")).strip()

    if not rfid_uid:
        return jsonify({"success": False, "message": "RFID UID is required"}), 400

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT u.user_id, u.name, u.role, p.uhid 
            FROM patients p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.rfid_uid = %s
            """,
            (rfid_uid,)
        )
        patient = cursor.fetchone()

        if not patient:
            return jsonify({"success": False, "message": "Card not registered to any patient"}), 404

        access_token = create_access_token(
            identity=str(patient["user_id"]),
            additional_claims={"role": patient["role"]}
        )

        latest_hardware_session["token"] = access_token
        latest_hardware_session["user"] = patient

        return jsonify({
            "success": True,
            "message": "Hardware login authorized",
            "token": access_token,
            "user": patient
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()


@auth_bp.get("/check-rfid-login")
def check_rfid_login():
    # Called repeatedly by LoginPage.html while waiting for a hardware scan
    if latest_hardware_session["token"]:
        session_data = {
            "success": True,
            "token": latest_hardware_session["token"],
            "user": latest_hardware_session["user"]
        }
        # Clear it after consumption so it only logs in once per tap
        latest_hardware_session["token"] = None
        latest_hardware_session["user"] = None
        return jsonify(session_data), 200
    
    return jsonify({"success": False, "message": "No hardware login detected yet"}), 200