import re
import pandas as pd
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier
import warnings
from database import insert_patient, get_next_ticket_number, create_connection
from stable_baselines3 import PPO
from rl_environment import PatientQueueEnv
from datetime import datetime
from sklearn.model_selection import train_test_split


warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load data
training = pd.read_csv('Data/Training.csv')
testing = pd.read_csv('Data/Testing.csv')
cols = training.columns[:-1]
x = training[cols]
y = training['prognosis']
reduced_data = training.groupby(training['prognosis']).max()

# Preprocessing
le = preprocessing.LabelEncoder()
le.fit(y)
y = le.transform(y)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)
testx = testing[cols]
testy = le.transform(testing['prognosis'])


# Train model
clf = DecisionTreeClassifier().fit(x_train, y_train)

# Load RL model
env = PatientQueueEnv()
model = PPO.load('ppo_patient_queue')

def predict_disease(symptoms):
    input_data = pd.DataFrame([symptoms], columns=cols)
    prediction = clf.predict(input_data)[0]
    disease = le.inverse_transform([prediction])[0]
    return disease

def get_criticality(disease):
    critical_diseases = ['disease1', 'disease2']  # List of critical diseases
    moderate_diseases = ['disease3', 'disease4']  # List of moderate diseases
    if disease in critical_diseases:
        return 'Critical'
    elif disease in moderate_diseases:
        return 'Moderate'
    else:
        return 'Mild'

def process_patient(name, symptoms):
    disease = predict_disease(symptoms)
    criticality = get_criticality(disease)
    ticket_number = get_next_ticket_number()
    insert_patient(name, str(symptoms), disease, criticality, 'Not served', ticket_number)

    # Predict waiting time using RL model
    patient = {
        'name': name,
        'symptoms': str(symptoms),
        'disease': disease,
        'criticality': criticality,
        'time_of_arrival': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status_of_service': 'Not served',
        'ticket_number': ticket_number
    }
    env.add_patient(patient)
    obs = env.reset()
    done = False
    total_reward = 0
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        total_reward += reward

    predicted_waiting_time = 100 - total_reward  # Adjust based on reward function
    update_waiting_time(ticket_number, predicted_waiting_time)

    return disease, criticality, ticket_number, predicted_waiting_time

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
