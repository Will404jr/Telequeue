import streamlit as st
import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from fuzzywuzzy import process
import csv
import re
from chat_bot import process_patient
from database import update_patient_status, create_connection
from gtts import gTTS
import os

# Function to load data
#@st.cache_resource
@st.cache
def load_data():
    training = pd.read_csv('Data/Training.csv')
    return training

# Function to train the model
def train_model(training):
    cols = training.columns[:-1]
    x = training[cols]
    y = training['prognosis']
    le = preprocessing.LabelEncoder()
    y_encoded = le.fit_transform(y)
    x_train, x_test, y_train, y_test = train_test_split(x, y_encoded, test_size=0.33, random_state=42)
    clf = DecisionTreeClassifier()
    clf.fit(x_train, y_train)
    return clf, le, cols

# Function to call next patient
def call_next_patient():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE status_of_service = 'Not served' ORDER BY time_of_arrival ASC LIMIT 1")
    patient = cursor.fetchone()
    if patient:
        ticket_number = patient[7]
        update_patient_status(ticket_number)
        text = f"Patient with ticket number {ticket_number}, please proceed to the doctor's office."
        tts = gTTS(text)
        tts.save("next_patient.mp3")
        os.system("mpg321 next_patient.mp3")
        return patient
    return None

# Main Streamlit App
st.title('Patient Diagnosis and Queue Management System')

# Patient interface
name = st.text_input('Enter your name')
symptoms = st.text_input('Enter your symptoms (comma separated)')

if st.button('Submit'):
    symptoms_list = [symptom.strip() for symptom in symptoms.split(',')]
    disease, criticality, ticket_number, predicted_waiting_time = process_patient(name, symptoms_list)
    st.write(f'Disease: {disease}')
    st.write(f'Criticality: {criticality}')
    st.write(f'Ticket Number: {ticket_number}')
    st.write(f'Predicted Waiting Time: {predicted_waiting_time:.2f} minutes')

    # Optionally, you could implement email notification here
    # send_email_notification(name, ticket_number, predicted_waiting_time)

# Doctor interface
if st.button('Call Next Patient'):
    patient = call_next_patient()
    if patient:
        st.write(f"Next patient: {patient[1]} with ticket number {patient[7]}")
    else:
        st.write("No patients in the queue.")
