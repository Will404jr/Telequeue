import gym
from stable_baselines3 import PPO
from rl_environment import PatientQueueEnv
import pandas as pd

# Function to parse logs and create DataFrame
def parse_logs(log_file_path):
    log_data = []

    # Read the log file line by line
    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    # Parse the log data
    for line in lines:
        if 'Action' in line:
            parts = line.strip().split(', ')
            log_entry = {}
            for part in parts:
                if ': ' in part:
                    key, value = part.split(': ')
                    log_entry[key.strip()] = value.strip()
            log_data.append(log_entry)

    # Convert to DataFrame for analysis
    log_df = pd.DataFrame(log_data)

    # Save to a CSV file for further analysis
    log_df.to_csv('parsed_training_logs.csv', index=False)
    return log_df

# Create the environment
env = PatientQueueEnv()

# Define the model with hyperparameters
model = PPO('MlpPolicy', env, verbose=1,
            learning_rate=0.0003,  # Adjust learning rate
            clip_range=0.2,  # Adjust clip range
            ent_coef=0.01)  # Adjust entropy coefficient

# Train the model
model.learn(total_timesteps=50000)

# Save the model
model.save('ppo_patient_queue')

# Parse logs after training
log_file_path = 'training_logs.log'
log_df = parse_logs(log_file_path)

# Display the log data (optional)
print(log_df.head())

# You can also analyze the log_df further as needed
