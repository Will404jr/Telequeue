import sqlite3
from datetime import datetime

def create_connection():
    conn = sqlite3.connect('patient_data.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            disease TEXT,
            criticality TEXT,
            time_of_arrival TEXT NOT NULL,
            status_of_service TEXT NOT NULL,
            ticket_number INTEGER NOT NULL,
            predicted_waiting_time REAL
        )
    ''')
    conn.commit()
    conn.close()

def insert_patient(name, symptoms, disease, criticality, status_of_service, ticket_number):
    conn = create_connection()
    cursor = conn.cursor()
    time_of_arrival = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO patients (name, symptoms, disease, criticality, time_of_arrival, status_of_service, ticket_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, symptoms, disease, criticality, time_of_arrival, status_of_service, ticket_number))
    conn.commit()
    conn.close()

def get_next_ticket_number():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(ticket_number) FROM patients')
    result = cursor.fetchone()
    conn.close()
    return result[0] + 1 if result[0] else 1

def update_waiting_time(ticket_number, waiting_time):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patients
        SET predicted_waiting_time = ?
        WHERE ticket_number = ?
    ''', (waiting_time, ticket_number))
    conn.commit()
    conn.close()
    
def update_patient_status(ticket_number):
    conn = create_connection()
    cursor = conn.cursor()
    
    # Update the patient's status to 'served'
    cursor.execute(
        "UPDATE patients SET status_of_service = 'served' WHERE ticket_number = ?", 
        (ticket_number,)
    )
    conn.commit()
    conn.close()


def get_patients_not_served():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM patients WHERE status_of_service = 'Not served'
        ORDER BY time_of_arrival ASC
    ''')
    patients = cursor.fetchall()
    conn.close()
    return patients
