from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from database.db import get_connection
from middleware.permissions import roles_required

doctors_bp = Blueprint("doctors", __name__, url_prefix="/api/doctors")


@doctors_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("admin")
def create_doctor():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    hospital_id = data.get("hospital_id")
    specialization = data.get("specialization")
    license_number = data.get("license_number")

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        return jsonify({
            "success": False,
            "message": "A valid user_id is required"
        }), 400

    if hospital_id is not None and (
        not isinstance(hospital_id, int)
        or isinstance(hospital_id, bool)
        or hospital_id <= 0
    ):
        return jsonify({
            "success": False,
            "message": "hospital_id must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, role FROM users WHERE user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if user is None or user["role"] != "doctor":
            return jsonify({
                "success": False,
                "message": "A registered doctor user is required"
            }), 400

        if hospital_id is not None:
            cursor.execute(
                "SELECT hospital_id FROM hospitals WHERE hospital_id = %s",
                (hospital_id,)
            )
            if cursor.fetchone() is None:
                return jsonify({
                    "success": False,
                    "message": "Hospital not found"
                }), 404

        cursor.execute(
            "SELECT doctor_id FROM doctors WHERE user_id = %s",
            (user_id,)
        )
        if cursor.fetchone() is not None:
            return jsonify({
                "success": False,
                "message": "Doctor profile already exists"
            }), 409

        cursor.execute(
            """
            INSERT INTO doctors
                (user_id, hospital_id, specialization, license_number)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, hospital_id, specialization, license_number)
        )

        connection.commit()
        doctor_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Doctor registered successfully",
            "doctor_id": doctor_id
        }), 201

    except Exception as e:
        if connection is not None:
            connection.rollback()
        print("Error in create_doctor:", str(e))
        return jsonify({
            "success": False,
            "message": "Unable to register doctor"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@doctors_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("admin", "hospital_admin", "doctor")
def get_doctors():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                d.doctor_id,
                u.user_id,
                u.name,
                u.email,
                d.hospital_id,
                h.name AS hospital_name,
                d.specialization,
                d.license_number,
                d.created_at
            FROM doctors d
            JOIN users u ON u.user_id = d.user_id
            LEFT JOIN hospitals h ON h.hospital_id = d.hospital_id
            ORDER BY d.doctor_id DESC
            """
        )

        doctors = cursor.fetchall()

        # Format timestamps to avoid JSON serialization issues
        for doc in doctors:
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "success": True,
            "doctors": doctors
        }), 200

    except Exception as e:
        print("Error in get_doctors:", str(e))
        return jsonify({
            "success": False,
            "message": "Unable to retrieve doctors"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@doctors_bp.post("/search-patient")
@jwt_required()
@roles_required("doctor")
def search_patient_by_uhid():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    uhid = str(data.get("uhid", "")).strip()

    if not uhid:
        return jsonify({"success": False, "message": "UHID is required"}), 400

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Verify the patient exists
        cursor.execute("SELECT patient_id, user_id FROM patients WHERE uhid = %s", (uhid,))
        patient = cursor.fetchone()

        if not patient:
            return jsonify({"success": False, "message": "Patient not found with this UHID"}), 404

        # 2. Get the doctor_id for the logged-in user
        cursor.execute("SELECT doctor_id FROM doctors WHERE user_id = %s", (user_id,))
        doctor = cursor.fetchone()

        if not doctor:
            return jsonify({"success": False, "message": "Unauthorized: Doctor profile not found"}), 403

        doctor_id = doctor["doctor_id"]

        # 3. Insert or update the access request (status defaults to 'pending')
        cursor.execute(
            """
            INSERT INTO access_requests (doctor_id, uhid, status)
            VALUES (%s, %s, 'pending')
            ON DUPLICATE KEY UPDATE status = 'pending', created_at = CURRENT_TIMESTAMP
            """,
            (doctor_id, uhid)
        )
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Access requested successfully! Awaiting patient approval."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error in search_patient_by_uhid:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: 
            cursor.close()
        if connection and connection.is_connected(): 
            connection.close()


@doctors_bp.get("/patient-records/<string:uhid>")
@jwt_required()
@roles_required("doctor")
def get_patient_records(uhid):
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Get the doctor_id for the logged-in user
        cursor.execute("SELECT doctor_id FROM doctors WHERE user_id = %s", (user_id,))
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify({"success": False, "message": "Doctor profile not found"}), 403

        doctor_id = doctor["doctor_id"]

        # 2. SECURITY CHECK: Verify if there is an approved access request for this doctor and patient UHID
        cursor.execute(
            """
            SELECT status FROM access_requests 
            WHERE doctor_id = %s AND uhid = %s AND status = 'approved'
            """,
            (doctor_id, uhid)
        )
        access = cursor.fetchone()

        if not access:
            return jsonify({
                "success": False, 
                "message": "Access denied: Patient has not approved access to these medical records."
            }), 403

        # 3. Fetch the patient ID
        cursor.execute("SELECT patient_id FROM patients WHERE uhid = %s", (uhid,))
        patient = cursor.fetchone()
        if not patient:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        # 4. Fetch the medical records
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

        # Format timestamps safely to strings
        for rec in records:
            if rec.get("created_at"):
                rec["created_at"] = str(rec["created_at"])

        return jsonify({"success": True, "records": records}), 200

    except Exception as e:
        print("Error fetching patient records:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if cursor: 
            cursor.close()
        if connection and connection.is_connected(): 
            connection.close()