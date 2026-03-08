import mysql.connector
from mysql.connector import Error
import hashlib

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_connection():
    """Create a database connection to the MySQL database"""
    try:
        # First connect without database to create it if needed
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''  # Update with your MySQL password
        )
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS healthlink")
        cursor.close()
        connection.close()

        # Now connect to the specific database
        connection = mysql.connector.connect(
            host='localhost',
            database='healthlink',
            user='root',
            password=''  # Update with your MySQL password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Create necessary tables if they don't exist"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('patient', 'doctor', 'admin') DEFAULT 'patient',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    doctor_id INT NOT NULL,
                    appointment_date DATETIME NOT NULL,
                    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES users(id),
                    FOREIGN KEY (doctor_id) REFERENCES users(id)
                )
            """)

            # Vitals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vitals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    blood_pressure VARCHAR(20),
                    heart_rate INT,
                    temperature DECIMAL(4,1),
                    weight DECIMAL(5,2),
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES users(id)
                )
            """)

            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES users(id)
                )
            """)

            connection.commit()
            print("Tables created successfully")

            # Insert sample doctors if they don't exist
            insert_sample_doctors(connection)
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()
            connection.close()

def insert_sample_doctors(connection):
    """Insert sample doctors if they don't exist"""
    try:
        cursor = connection.cursor()
        # Check if any doctors exist
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'doctor'")
        result = cursor.fetchone()
        if result[0] == 0:
            # Insert sample doctors
            sample_doctors = [
                ('Dr. Sarah Johnson', 'sarah.johnson@healthlink.com', 'password123', 'doctor'),
                ('Dr. Michael Chen', 'michael.chen@healthlink.com', 'password123', 'doctor'),
                ('Dr. Emily Davis', 'emily.davis@healthlink.com', 'password123', 'doctor'),
                ('Dr. Robert Wilson', 'robert.wilson@healthlink.com', 'password123', 'doctor'),
                ('Dr. Lisa Brown', 'lisa.brown@healthlink.com', 'password123', 'doctor')
            ]

            for username, email, password, role in sample_doctors:
                hashed_password = hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, role)
                )

            connection.commit()
            print("Sample doctors inserted successfully")
        else:
            print("Doctors already exist in database")
        cursor.close()
    except Error as e:
        print(f"Error inserting sample doctors: {e}")

if __name__ == "__main__":
    create_tables()