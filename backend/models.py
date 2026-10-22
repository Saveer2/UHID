from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="patient")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)


class Hospital(db.Model):
    __tablename__ = "hospitals"

    hospital_id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)


class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True
    )
    uhid = db.Column(db.String(40), unique=True, nullable=False, index=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(30))
    contact_details = db.Column(db.String(30))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)


class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True,
        nullable=False
    )
    hospital_id = db.Column(
        db.Integer, db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )
    specialization = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)


class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    record_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.patient_id"),
        nullable=False, index=True
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctors.doctor_id"), nullable=False
    )
    hospital_id = db.Column(
        db.Integer, db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )
    record_type = db.Column(db.String(100), nullable=False)
    document_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)


class AccessLog(db.Model):
    __tablename__ = "access_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.patient_id"), nullable=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False
    )
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utc_now)
