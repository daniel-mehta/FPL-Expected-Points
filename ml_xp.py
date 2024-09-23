import requests
import pandas as pd

# Function to get FPL player data using the FPL API
def get_fpl_data():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url)
    json_data = response.json()

    # Extract players' data
    players = json_data['elements']
    players_df = pd.DataFrame(players)

    return players_df

# Fetch FPL player data
fpl_data = get_fpl_data()

# Fetch fixture data from the FPL API
def get_fixtures_data():
    url = 'https://fantasy.premierleague.com/api/fixtures/'
    response = requests.get(url)
    json_data = response.json()

    # Convert the JSON data to a Pandas DataFrame
    fixtures_df = pd.DataFrame(json_data)

    return fixtures_df

# Fetch fixture data
fixtures_df = get_fixtures_data()

# Load the fixture data from the CSV file
fixtures_df = get_fixtures_data()

# Filter for fixtures that haven't finished yet
upcoming_fixtures = fixtures_df[fixtures_df['finished'] == False]

# Automatically get the next gameweek by finding the minimum event ID
next_gameweek = upcoming_fixtures['event'].min()

print(f"The next gameweek is: {next_gameweek}")

# Filter for fixtures for the next gameweek only
fixtures_next_gameweek = fixtures_df[fixtures_df['event'] == next_gameweek]

# Create a dictionary to hold the difficulty of each team for the next gameweek
team_difficulty_dict = {}
for _, row in fixtures_next_gameweek.iterrows():
    team_h = row['team_h']
    team_a = row['team_a']
    team_h_difficulty = row['team_h_difficulty']
    team_a_difficulty = row['team_a_difficulty']

    team_difficulty_dict[team_h] = team_h_difficulty
    team_difficulty_dict[team_a] = team_a_difficulty

# Difficulty multiplier for fixture difficulty
difficulty_multiplier = {
    1: 1.2,  # easiest
    2: 1.1,
    3: 1.0,  # neutral
    4: 0.9,
    5: 0.8   # hardest
}

# Create a function to calculate expected points based on team and fixture difficulty
def calculate_expected_points(player_row):
    player_team = player_row['team']

    # Find the fixture difficulty for the player's team
    if player_team in team_difficulty_dict:
        fixture_difficulty = team_difficulty_dict[player_team]
    else:
        fixture_difficulty = 3  # Default to neutral if not found

    difficulty_factor = difficulty_multiplier.get(fixture_difficulty, 1.0)

    # Positional Points
    if player_row['element_type'] == 1:  # Goalkeeper
        goal_points = 10
        assist_points = 3
        clean_sheet_points = 4
    elif player_row['element_type'] == 2:  # Defender
        goal_points = 6
        assist_points = 3
        clean_sheet_points = 4
    elif player_row['element_type'] == 3:  # Midfielder
        goal_points = 5
        assist_points = 3
        clean_sheet_points = 1
    elif player_row['element_type'] == 4:  # Forward
        goal_points = 4
        assist_points = 3
        clean_sheet_points = 0
    else:
        goal_points = 0
        assist_points = 0
        clean_sheet_points = 0

    # Approximate games played only if minutes are above a threshold
    min_minutes = 200  # Example threshold
    games_played = player_row['minutes'] / 90 if player_row['minutes'] > 0 else 1

    # Expected Points based on Goals, Assists, Clean Sheets
    expected_points = (
        (player_row['goals_scored'] / games_played) * goal_points +
        (player_row['assists'] / games_played) * assist_points +
        (player_row['clean_sheets'] / games_played) * clean_sheet_points +
        (player_row['minutes'] / games_played) * 0.01  # Basic playing time contribution
    )

    # Adjust for fixture difficulty
    expected_points = expected_points * difficulty_factor

    # Add points for playing 60+ minutes
    if player_row['minutes'] >= 60:
        expected_points += 1

    return expected_points

# Apply the expected points function to each player for the next gameweek
fpl_data['expected_points'] = fpl_data.apply(calculate_expected_points, axis=1)

# Verify expected points calculated
print(fpl_data[['web_name', 'expected_points']].head())

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Features for the model (we'll use form, goals, assists, clean sheets, minutes, etc.)
features = ['now_cost', 'form', 'goals_scored', 'assists', 'clean_sheets', 'minutes']
target = 'expected_points'

# Prepare the feature matrix (X) and target vector (y)
X = fpl_data[features]
y = fpl_data[target]

# Split the data into training and testing sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Predict on the test data
y_pred = rf_model.predict(X_test)

# Evaluate the model's performance
mse = mean_squared_error(y_test, y_pred)
print(f'Mean Squared Error: {mse}')

# Predict expected points for all players
fpl_data['predicted_points'] = rf_model.predict(fpl_data[features])

# Sort players by predicted points in descending order
top_players = fpl_data.sort_values(by='predicted_points', ascending=False)

# Print the top 5 players by predicted points
print("Top 5 players by predicted points for Gameweek 5:")
print(top_players[['web_name', 'team', 'predicted_points']].head(5))


# Create a new DataFrame with only web_name and expected_points
top_players_df = fpl_data[['web_name', 'expected_points']]

# Construct the filename using the gameweek number
filename = f"MLxPoint_{next_gameweek}.csv"

# Save the DataFrame to a CSV file
top_players_df.to_csv(filename, index=False)

print(f"CSV file '{filename}' created successfully!")