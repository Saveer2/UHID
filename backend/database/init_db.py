from database.db import get_connection

def create_tables():
    connection = None
    cursor = None

    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM(
                'patient',
                'doctor',
                'hospital_admin',
                'admin'
            ) NOT NULL DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            address VARCHAR(255),
            phone VARCHAR(20),
            email VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE,
            uhid VARCHAR(30) NOT NULL UNIQUE,
            date_of_birth DATE,
            gender VARCHAR(20),
            phone VARCHAR(20),
            address VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            hospital_id INT,
            specialization VARCHAR(100),
            license_number VARCHAR(100) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE,

            FOREIGN KEY (hospital_id)
                REFERENCES hospitals(hospital_id)
                ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS medical_records (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            doctor_id INT,
            hospital_id INT,
            record_type VARCHAR(100) NOT NULL,
            description TEXT,
            document_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id),

            FOREIGN KEY (doctor_id)
                REFERENCES doctors(doctor_id)
                ON DELETE SET NULL,

            FOREIGN KEY (hospital_id)
                REFERENCES hospitals(hospital_id)
                ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS access_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            patient_id INT,
            record_id INT,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL,

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id)
                ON DELETE SET NULL,

            FOREIGN KEY (record_id)
                REFERENCES medical_records(record_id)
                ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS access_requests (
            request_id INT AUTO_INCREMENT PRIMARY KEY,
            doctor_id INT NOT NULL,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uhid VARCHAR(50) NOT NULL,
            
            -- Ensures a doctor can only have one active/pending request per patient UHID
            UNIQUE KEY unique_doctor_uhid (doctor_id, uhid),

            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
        )
        """,
    ]

    try:
        connection = get_connection()
        cursor = connection.cursor()

        for table_sql in tables:
            cursor.execute(table_sql)

        connection.commit()
        print("All six database tables created successfully!")

    except Exception as error:
        if connection is not None:
            connection.rollback()

        print("Error creating database tables:", error)

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    create_tables()
