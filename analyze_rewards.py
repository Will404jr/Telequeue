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

# Load and parse the logs
log_file_path = 'training_logs.log'  # Update the path to your log file
log_df = parse_logs(log_file_path)

# Display the log data
print(log_df[['Action', 'Patient', 'Waiting Time', 'Reward']].head())

# Analyze the log data
print("Average Reward by Patient Category:")
print(log_df.groupby('Patient')['Reward'].mean())

# Additional analysis to understand reward distribution
print("Reward Distribution by Patient Category:")
print(log_df.groupby('Patient')['Reward'].describe())
