
from database.db import get_connection


def log_action(user_id=None, patient_id=None, record_id=None, action=None, details=None):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO access_logs
                (user_id, patient_id, record_id, action, details)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, patient_id, record_id, action, details)
        )

        connection.commit()

    except Exception:
        if connection is not None:
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
