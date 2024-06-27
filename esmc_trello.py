import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt

# Load the JSON file
file_path = 'esmc_trello.json'
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

# Filter for actions that moved cards to "Bugs"
bugs_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'Bugs'
]

# Filter for actions that moved cards to "PM Requests"
pm_actions = [
    action for action in actions 
    if action['type'] == 'updateCard' 
    and action['data'].get('listAfter', {}).get('name') == 'PM Requests'
]

# Create DataFrames
done_df = pd.DataFrame(done_actions)
bugs_df = pd.DataFrame(bugs_actions)
pm_df = pd.DataFrame(pm_actions)

# Convert date string to datetime object
done_df['date'] = pd.to_datetime(done_df['date'], utc=True)
bugs_df['date'] = pd.to_datetime(bugs_df['date'], utc=True)
pm_df['date'] = pd.to_datetime(pm_df['date'], utc=True)

# Function to count unique cards in a given period
def count_unique_cards_in_period(start_date, end_date, df):
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    unique_cards = filtered_df['data'].apply(lambda x: x['card']['id'] if 'card' in x else None).nunique()
    return unique_cards

# Function to count matching cards in a given period
def count_matching_cards_in_period(start_date, end_date, actions, condition):
    filtered_actions = [action for action in actions if 'date' in action and start_date <= pd.to_datetime(action['date'], utc=True, errors='coerce') <= end_date]
    matching_actions = [action for action in filtered_actions if 'data' in action and condition(action['data'])]
    unique_matching_cards = len(set(action['data']['card']['id'] for action in matching_actions if 'card' in action['data']))
    return unique_matching_cards

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
    bugs_count = count_unique_cards_in_period(start_date, end_date, bugs_df)
    squashed_bugs_count = len([
        action for action in done_actions
        if 'data' in action and action['data'].get('listBefore', {}).get('name') == 'Bugs'
        and start_date <= pd.to_datetime(action['date'], utc=True, errors='coerce') <= end_date
    ])
    soil_tickets_count = count_matching_cards_in_period(
        start_date, end_date, actions, 
        lambda x: 'card' in x and 'name' in x['card'] and 'soil' in x['card']['name'].lower()
    )
    api_tickets_count = count_matching_cards_in_period(
        start_date, end_date, actions, 
        lambda x: 'card' in x and 'name' in x['card'] and 'api' in x['card']['name'].lower()
    )
    pm_tickets_count = count_unique_cards_in_period(start_date, end_date, pm_df)
    pm_tickets_completed_count = len([
        action for action in done_actions
        if 'data' in action and action['data'].get('listBefore', {}).get('name') == 'PM Requests'
        and start_date <= pd.to_datetime(action['date'], utc=True, errors='coerce') <= end_date
    ])
    
    results.append({
        'Start Date': start_date.strftime('%Y-%m-%d'),
        'End Date': end_date.strftime('%Y-%m-%d'),
        'Unique Cards Moved to Done': unique_done_cards,
        'Bugs': bugs_count,
        'Squashed Bugs': squashed_bugs_count,
        'Soil Tickets': soil_tickets_count,
        'API Tickets': api_tickets_count,
        'PM Tickets': pm_tickets_count,
        'PM Tickets Completed': pm_tickets_completed_count
    })

# Create a DataFrame for the results
results_df = pd.DataFrame(results)

# Export the results to a CSV file
output_file_path = 'trello_done_cards_report.csv'
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

plot_and_save(results_df, 'Unique Cards Moved to Done', 'Unique Cards Moved to Done Over Time', 'unique_cards_moved_to_done')
plot_and_save(results_df, 'Bugs', 'Bugs Over Time', 'bugs_over_time')
plot_and_save(results_df, 'Squashed Bugs', 'Squashed Bugs Over Time', 'squashed_bugs_over_time')
plot_and_save(results_df, 'Soil Tickets', 'Soil Tickets Over Time', 'soil_tickets_over_time')
plot_and_save(results_df, 'API Tickets', 'API Tickets Over Time', 'api_tickets_over_time')
plot_and_save(results_df, 'PM Tickets', 'PM Tickets Over Time', 'pm_tickets_over_time')
plot_and_save(results_df, 'PM Tickets Completed', 'PM Tickets Completed Over Time', 'pm_tickets_completed_over_time')
