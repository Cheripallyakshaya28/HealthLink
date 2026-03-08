from flask import Flask, render_template, request, redirect, url_for, session, flash
import database
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    """Check if password matches hashed password"""
    return hash_password(password) == hashed

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'patient')

        connection = database.create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                hashed_password = hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, role)
                )
                connection.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Registration failed: {str(e)}', 'error')
            finally:
                cursor.close()
                connection.close()

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    connection = database.create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and check_password(password, user['password']):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    connection = database.create_connection()
    appointments = []
    vitals = []
    alerts = []

    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Get upcoming appointments
            if session['role'] == 'patient':
                cursor.execute("""
                    SELECT a.*, u.username as doctor_name
                    FROM appointments a
                    JOIN users u ON a.doctor_id = u.id
                    WHERE a.patient_id = %s AND a.appointment_date > NOW()
                    ORDER BY a.appointment_date ASC
                """, (session['user_id'],))
            else:  # doctor or admin
                cursor.execute("""
                    SELECT a.*, u.username as patient_name
                    FROM appointments a
                    JOIN users u ON a.patient_id = u.id
                    WHERE a.doctor_id = %s AND a.appointment_date > NOW()
                    ORDER BY a.appointment_date ASC
                """, (session['user_id'],))

            appointments = cursor.fetchall()

            # Get recent vitals (for patients)
            if session['role'] == 'patient':
                cursor.execute("""
                    SELECT * FROM vitals
                    WHERE patient_id = %s
                    ORDER BY recorded_at DESC LIMIT 5
                """, (session['user_id'],))
                vitals = cursor.fetchall()

            # Get unread alerts
            cursor.execute("""
                SELECT * FROM alerts
                WHERE patient_id = %s AND is_read = FALSE
                ORDER BY created_at DESC
            """, (session['user_id'],))
            alerts = cursor.fetchall()

        except Exception as e:
            flash(f'Error loading dashboard: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template('dashboard.html', appointments=appointments, vitals=vitals, alerts=alerts)

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        notes = request.form.get('notes', '')

        connection = database.create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO appointments (patient_id, doctor_id, appointment_date, notes) VALUES (%s, %s, %s, %s)",
                    (session['user_id'], doctor_id, appointment_date, notes)
                )
                connection.commit()
                flash('Appointment booked successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Failed to book appointment: {str(e)}', 'error')
            finally:
                cursor.close()
                connection.close()

    # Get list of doctors
    connection = database.create_connection()
    doctors = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, username FROM users WHERE role = 'doctor'")
            doctors = cursor.fetchall()
        except Exception as e:
            flash(f'Error loading doctors: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template('appointment.html', doctors=doctors)

@app.route('/vitals', methods=['GET', 'POST'])
def vitals():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('index'))

    if request.method == 'POST':
        blood_pressure = request.form.get('blood_pressure')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        weight = request.form.get('weight')

        connection = database.create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO vitals (patient_id, blood_pressure, heart_rate, temperature, weight) VALUES (%s, %s, %s, %s, %s)",
                    (session['user_id'], blood_pressure, heart_rate, temperature, weight)
                )
                connection.commit()

                # Check for alerts based on vitals
                check_vital_alerts(cursor, session['user_id'], blood_pressure, heart_rate, temperature, weight)

                flash('Vitals recorded successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Failed to record vitals: {str(e)}', 'error')
            finally:
                cursor.close()
                connection.close()

    return render_template('vitals.html')

def check_vital_alerts(cursor, patient_id, bp, hr, temp, weight):
    """Check vitals and create alerts if necessary"""
    alerts = []

    if bp:
        systolic, diastolic = map(int, bp.split('/'))
        if systolic > 140 or diastolic > 90:
            alerts.append(('High Blood Pressure', f'Your blood pressure is {bp}, which is high. Please consult your doctor.'))

    if hr and (int(hr) < 60 or int(hr) > 100):
        alerts.append(('Abnormal Heart Rate', f'Your heart rate is {hr} bpm, which is abnormal.'))

    if temp and float(temp) > 100.4:
        alerts.append(('High Temperature', f'Your temperature is {temp}°F, indicating a fever.'))

    for alert_type, message in alerts:
        cursor.execute(
            "INSERT INTO alerts (patient_id, alert_type, message) VALUES (%s, %s, %s)",
            (patient_id, alert_type, message)
        )

if __name__ == '__main__':
    database.create_tables()  # Ensure tables exist
    app.run(debug=True)