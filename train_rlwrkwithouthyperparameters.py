# train_rl.py

import gym
from stable_baselines3 import PPO
from rl_environment import PatientQueueEnv

env = PatientQueueEnv()
model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=10000)
model.save('ppo_patient_queue')
