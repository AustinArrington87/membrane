import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt

# Load the JSON file
file_path = 'star_trello.json'
with open(file_path, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Extract actions
actions = data['actions']

# Filter for actions that moved cards to "Done 🎉"
done_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Done 🎉'
]

# Filter for actions that moved cards to "Hotfixes"
hotfixes_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Hotfixes'
]

# Filter for actions that moved cards to "Doing"
doing_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Doing'
]

# Filter for actions that moved cards to "Testing"
testing_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Testing'
]

# Filter for actions that moved cards to "Backlog"
backlog_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Backlog'
]

# Create DataFrames
done_df = pd.DataFrame(done_actions)
hotfixes_df = pd.DataFrame(hotfixes_actions)
doing_df = pd.DataFrame(doing_actions)
testing_df = pd.DataFrame(testing_actions)
backlog_df = pd.DataFrame(backlog_actions)

# Convert date string to datetime object
done_df['date'] = pd.to_datetime(done_df['date'], utc=True)
hotfixes_df['date'] = pd.to_datetime(hotfixes_df['date'], utc=True)
doing_df['date'] = pd.to_datetime(doing_df['date'], utc=True)
testing_df['date'] = pd.to_datetime(testing_df['date'], utc=True)
backlog_df['date'] = pd.to_datetime(backlog_df['date'], utc=True)

# Function to count unique cards in a given period
def count_unique_cards_in_period(start_date, end_date, df):
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    unique_cards = filtered_df['data'].apply(lambda x: x['card']['id'] if 'card' in x else None).nunique()
    return unique_cards

# Initialize the current end date
current_end_date = datetime.now(pytz.utc)

# Define the periods (e.g., last 5 months, each 30 days period)
periods = []
for i in range(6):
    current_start_date = current_end_date - timedelta(days=30)
    periods.append((current_start_date, current_end_date))
    current_end_date = current_start_date

# Count unique cards for each period
results = []
for start_date, end_date in periods:
    unique_done_cards = count_unique_cards_in_period(start_date, end_date, done_df)
    hotfixes_count = count_unique_cards_in_period(start_date, end_date, hotfixes_df)
    in_progress_count = count_unique_cards_in_period(start_date, end_date, doing_df)
    features_tested_count = count_unique_cards_in_period(start_date, end_date, testing_df)
    in_backlog_count = count_unique_cards_in_period(start_date, end_date, backlog_df)
    
    results.append({
        'Start Date': start_date.strftime('%Y-%m-%d'),
        'End Date': end_date.strftime('%Y-%m-%d'),
        'Tickets Completed': unique_done_cards,
        'Hotfixes Requested': hotfixes_count,
        'In Progress': in_progress_count,
        'Features Tested': features_tested_count,
        'In Backlog': in_backlog_count
    })

# Create a DataFrame for the results
results_df = pd.DataFrame(results)

# Export the results to a CSV file
output_file_path = 'star_trello_report.csv'
results_df.to_csv(output_file_path, index=False)

# Display the results
print(results_df)

# Plotting the results
def plot_and_save(df, column, title, filename):
    plt.figure(figsize=(10, 6))
    plt.plot(df['End Date'], df[column], marker='o')
    plt.title(title)
    plt.xlabel('End Date')
    plt.ylabel(column)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{filename}.png')
    plt.close()

plot_and_save(results_df, 'Tickets Completed', 'Tickets Completed Over Time', 'tickets_completed')
plot_and_save(results_df, 'Hotfixes Requested', 'Hotfixes Requested Over Time', 'hotfixes_requested')
plot_and_save(results_df, 'In Progress', 'In Progress Over Time', 'in_progress')
plot_and_save(results_df, 'Features Tested', 'Features Tested Over Time', 'features_tested')
plot_and_save(results_df, 'In Backlog', 'In Backlog Over Time', 'in_backlog')
