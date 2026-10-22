
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from database.db import get_connection
from middleware.permissions import roles_required
from services.audit_service import log_action

medical_records_bp = Blueprint(
    "medical_records",
    __name__,
    url_prefix="/api/medical-records"
)


@medical_records_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("doctor", "admin")
def create_medical_record():
    data = request.get_json(silent=True) or {}

    patient_id = data.get("patient_id")
    hospital_id = data.get("hospital_id")
    record_type = data.get("record_type")
    description = data.get("description")
    document_path = data.get("document_path")

    if not isinstance(patient_id, int) or isinstance(patient_id, bool) or patient_id <= 0:
        return jsonify({
            "success": False,
            "message": "A valid patient_id is required"
        }), 400

    if not isinstance(record_type, str) or not record_type.strip():
        return jsonify({
            "success": False,
            "message": "record_type is required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        user_id = get_jwt_identity()
        role = get_jwt().get("role")

        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = %s",
            (patient_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "message": "Patient not found"
            }), 404

        doctor_id = None

        if role == "doctor":
            cursor.execute(
                "SELECT doctor_id, hospital_id FROM doctors WHERE user_id = %s",
                (user_id,)
            )
            doctor = cursor.fetchone()

            if doctor is None:
                return jsonify({
                    "success": False,
                    "message": "Doctor profile not found"
                }), 403

            doctor_id = doctor["doctor_id"]

            if hospital_id is None:
                hospital_id = doctor["hospital_id"]

        if hospital_id is not None:
            if not isinstance(hospital_id, int) or isinstance(hospital_id, bool) or hospital_id <= 0:
                return jsonify({
                    "success": False,
                    "message": "Invalid hospital_id"
                }), 400

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
            """
            INSERT INTO medical_records
                (patient_id, doctor_id, hospital_id, record_type, description, document_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                doctor_id,
                hospital_id,
                record_type.strip(),
                description,
                document_path
            )
        )

        record_id = cursor.lastrowid
        connection.commit()

    except Exception:
        if connection is not None:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to create medical record"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    log_action(
        user_id=user_id,
        patient_id=patient_id,
        record_id=record_id,
        action="CREATE_MEDICAL_RECORD",
        details="Medical record created"
    )

    return jsonify({
        "success": True,
        "message": "Medical record created successfully",
        "record_id": record_id
    }), 201


@medical_records_bp.route("/", methods=["GET"])
@jwt_required()
def get_medical_records():
    connection = None
    cursor = None

    try:
        user_id = get_jwt_identity()
        role = get_jwt().get("role")

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if role == "patient":
            cursor.execute(
                """
                SELECT patient_id
                FROM patients
                WHERE user_id = %s
                """,
                (user_id,)
            )
            patient = cursor.fetchone()

            if patient is None:
                return jsonify({
                    "success": False,
                    "message": "Patient profile not found"
                }), 404

            cursor.execute(
                """
                SELECT record_id, patient_id, doctor_id, hospital_id,
                       record_type, description, document_path, created_at
                FROM medical_records
                WHERE patient_id = %s
                ORDER BY created_at DESC
                """,
                (patient["patient_id"],)
            )

        elif role == "doctor":
            cursor.execute(
                "SELECT doctor_id FROM doctors WHERE user_id = %s",
                (user_id,)
            )
            doctor = cursor.fetchone()

            if doctor is None:
                return jsonify({
                    "success": False,
                    "message": "Doctor profile not found"
                }), 403

            cursor.execute(
                """
                SELECT record_id, patient_id, doctor_id, hospital_id,
                       record_type, description, document_path, created_at
                FROM medical_records
                WHERE doctor_id = %s
                ORDER BY created_at DESC
                """,
                (doctor["doctor_id"],)
            )

        elif role in ("admin", "hospital_admin"):
            if role == "hospital_admin":
                cursor.execute(
                    """
                    SELECT hospital_id
                    FROM doctors
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                hospital = cursor.fetchone()

                if hospital is None or hospital["hospital_id"] is None:
                    return jsonify({
                        "success": False,
                        "message": "Hospital association not found"
                    }), 403

                cursor.execute(
                    """
                    SELECT record_id, patient_id, doctor_id, hospital_id,
                           record_type, description, document_path, created_at
                    FROM medical_records
                    WHERE hospital_id = %s
                    ORDER BY created_at DESC
                    """,
                    (hospital["hospital_id"],)
                )
            else:
                cursor.execute(
                    """
                    SELECT record_id, patient_id, doctor_id, hospital_id,
                           record_type, description, document_path, created_at
                    FROM medical_records
                    ORDER BY created_at DESC
                    """
                )

        else:
            return jsonify({
                "success": False,
                "message": "Access forbidden"
            }), 403

        records = cursor.fetchall()

        return jsonify({
            "success": True,
            "medical_records": records
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Unable to retrieve medical records"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
