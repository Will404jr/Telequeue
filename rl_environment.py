import numpy as np
import gym
from gym import spaces
from datetime import datetime, timedelta
from database import insert_patient, get_next_ticket_number, create_connection
import logging
import random

# Set up logging to file
logging.basicConfig(level=logging.INFO, filename='training_logs.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PatientQueueEnv(gym.Env):
    def __init__(self):
        super(PatientQueueEnv, self).__init__()
        self.action_space = spaces.Discrete(3)  # 0: Mild, 1: Moderate, 2: Critical
        self.observation_space = spaces.Box(low=0, high=1000, shape=(1,), dtype=np.float32)
        self.queue = []

    def reset(self):
        self.queue = []
        # Add a random number of initial patients to the queue (between 1 and 30)
        num_patients = random.randint(1, 30)
        current_time = datetime.now()
        for i in range(num_patients):
            criticality = random.choice(['Critical', 'Moderate', 'Mild'])
            arrival_time_offset = random.randint(1, 30)
            patient = {
                'name': f'Patient {i+1}',
                'criticality': criticality,
                'time_of_arrival': (current_time - timedelta(minutes=arrival_time_offset)).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.add_patient(patient)

        self.state = np.array([len(self.queue)], dtype=np.float32)
        return self.state

    def step(self, action):
        critical_patients = [p for p in self.queue if p['criticality'] == 'Critical']
        moderate_patients = [p for p in self.queue if p['criticality'] == 'Moderate']
        mild_patients = [p for p in self.queue if p['criticality'] == 'Mild']

        patient = None
        if action == 2 and critical_patients:
            patient = critical_patients.pop(0)
        elif action == 1 and moderate_patients:
            patient = moderate_patients.pop(0)
        elif action == 0 and mild_patients:
            patient = mild_patients.pop(0)

        if patient is None:
            logging.info("No patients available to serve.")
            return self.state, 0, True, {}

        self.queue = critical_patients + moderate_patients + mild_patients

        current_time = datetime.now()
        waiting_time = (current_time - datetime.strptime(patient['time_of_arrival'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60.0

        # Refined Reward Function
        reward = 0
        if patient['criticality'] == 'Critical':
            reward = max(100 - waiting_time, 0)
        elif patient['criticality'] == 'Moderate':
            reward = max(50 - waiting_time, -50)
        else:
            reward = max(20 - waiting_time, -100)

        logging.info(f"Action: {action}, Patient: {patient['criticality']}, Waiting Time: {waiting_time:.2f}, Reward: {reward}, Queue Length: {len(self.queue)}")

        self.state = np.array([len(self.queue)], dtype=np.float32)
        done = self.state[0] == 0

        return self.state, reward, done, {}

    def render(self, mode='human'):
        pass

    def add_patient(self, patient):
        self.queue.append(patient)
