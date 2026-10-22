
import uuid

from database.db import get_connection


def generate_uhid():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        while True:
            uhid = f"UHID-{uuid.uuid4().hex[:12].upper()}"

            cursor.execute(
                "SELECT patient_id FROM patients WHERE uhid = %s",
                (uhid,)
            )

            if cursor.fetchone() is None:
                return uhid

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
