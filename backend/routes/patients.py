import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from database.db import get_connection

patients_bp = Blueprint("patients", __name__, url_prefix="/api/patients")

# Configure upload folder path
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@patients_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_patient_profile():
    connection = None
    cursor = None

    try:
        user_id = get_jwt_identity()

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                u.user_id,
                u.name,
                u.email,
                u.role,
                p.patient_id,
                p.uhid,
                p.date_of_birth,
                p.gender,
                p.phone,
                p.address,
                p.created_at
            FROM users u
            LEFT JOIN patients p ON p.user_id = u.user_id
            WHERE u.user_id = %s
            """,
            (user_id,)
        )

        patient = cursor.fetchone()

        if patient is None:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if patient["role"] != "patient" or patient["patient_id"] is None:
            return jsonify({
                "success": False,
                "message": "Patient profile not found"
            }), 404

        if patient.get("date_of_birth"):
            patient["date_of_birth"] = patient["date_of_birth"].strftime("%Y-%m-%d")

        if patient.get("created_at"):
            patient["created_at"] = patient["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify(patient), 200

    except Exception as e:
        print("Error in get_patient_profile:", str(e))
        return jsonify({
            "success": False,
            "message": "Unable to retrieve patient profile"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@patients_bp.route("/access-requests", methods=["GET"])
@jwt_required()
def get_access_requests():
    connection = None
    cursor = None

    try:
        user_id = get_jwt_identity()

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT uhid FROM patients WHERE user_id = %s", (user_id,))
        patient_row = cursor.fetchone()

        if not patient_row or not patient_row["uhid"]:
            return jsonify({"success": False, "message": "Patient UHID profile not found"}), 404

        patient_uhid = patient_row["uhid"]

        cursor.execute(
            """
            SELECT 
                ar.request_id, 
                ar.doctor_id, 
                u.name as doctor_name, 
                d.specialization, 
                h.name as hospital_name, 
                ar.status, 
                ar.created_at
            FROM access_requests ar
            JOIN doctors d ON ar.doctor_id = d.doctor_id
            JOIN users u ON d.user_id = u.user_id
            LEFT JOIN hospitals h ON d.hospital_id = h.hospital_id
            WHERE ar.uhid = %s AND ar.status = 'pending'
            """,
            (patient_uhid,)
        )
        requests_list = cursor.fetchall()

        for req in requests_list:
            if req.get("created_at"):
                req["created_at"] = str(req["created_at"])

        return jsonify({"success": True, "requests": requests_list}), 200

    except Exception as e:
        print("Error in get_access_requests:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@patients_bp.route("/access-requests/handle", methods=["POST"])
@jwt_required()
def handle_access_request():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    request_id = data.get("request_id")
    action = data.get("action")

    if not request_id or action not in ["approved", "rejected"]:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT uhid FROM patients WHERE user_id = %s", (user_id,))
        patient = cursor.fetchone()

        if not patient or not patient["uhid"]:
            return jsonify({"success": False, "message": "Unauthorized patient profile"}), 403

        patient_uhid = patient["uhid"]

        cursor.execute(
            """
            UPDATE access_requests 
            SET status = %s 
            WHERE request_id = %s AND uhid = %s
            """,
            (action, request_id, patient_uhid)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Request not found or unauthorized"}), 404

        return jsonify({"success": True, "message": f"Request {action} successfully"}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error in handle_access_request:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@patients_bp.route("/upload-record", methods=["POST"])
@jwt_required()
def upload_patient_record():
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT patient_id FROM patients WHERE user_id = %s", (user_id,))
        patient = cursor.fetchone()

        if not patient:
            return jsonify({"success": False, "message": "Patient profile not found"}), 404

        patient_id = patient["patient_id"]

        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file part provided"}), 400

        file = request.files['file']
        record_type = request.form.get("record_type", "General Report")
        description = request.form.get("description", "")

        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        cursor.execute(
            """
            INSERT INTO medical_records (patient_id, record_type, description, document_path)
            VALUES (%s, %s, %s, %s)
            """,
            (patient_id, record_type, description, file_path)
        )
        connection.commit()

        return jsonify({
            "success": True, 
            "message": "Medical record uploaded successfully!"
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error uploading record:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@patients_bp.route("/my-records", methods=["GET"])
@jwt_required()
def get_my_medical_records():
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT patient_id FROM patients WHERE user_id = %s", (user_id,))
        patient = cursor.fetchone()

        if not patient:
            return jsonify({"success": False, "message": "Patient profile not found"}), 404

        cursor.execute(
            """
            SELECT record_id, record_type, description, document_path, created_at 
            FROM medical_records 
            WHERE patient_id = %s 
            ORDER BY created_at DESC
            """,
            (patient["patient_id"],)
        )
        records = cursor.fetchall()

        for rec in records:
            if rec.get("created_at"):
                rec["created_at"] = str(rec["created_at"])

        return jsonify({"success": True, "records": records}), 200

    except Exception as e:
        print("Error fetching own records:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()