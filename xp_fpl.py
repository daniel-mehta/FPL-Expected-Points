import requests # import the requests module
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

# Fetch FPL data
fpl_data = get_fpl_data()

# Save FPL data to CSV
fpl_data.to_csv('fpl_player_data.csv', index=False)

print('Data saved to fpl_player_data.csv')



# Load the FPL data from the CSV file
fpl_data = pd.read_csv('fpl_player_data.csv')

# Fetch fixture data from the FPL API
url = 'https://fantasy.premierleague.com/api/fixtures/'
response = requests.get(url)
json_data = response.json()

# Convert the JSON data to a Pandas DataFrame
fixtures_df = pd.DataFrame(json_data)

# Save the DataFrame to a CSV file
fixtures_df.to_csv('fixture_info.csv', index=False)

print('Fixture data saved to fixture_info.csv')


# Load the fixture data from the CSV file
fixtures_df = pd.read_csv('fixture_info.csv')

# Filter for fixtures that haven't finished yet
upcoming_fixtures = fixtures_df[fixtures_df['finished'] == False]

# Find the next gameweek by getting the minimum event ID
next_gameweek = upcoming_fixtures['event'].min()

print(f"The next gameweek is: {next_gameweek}")


# Filter fixtures for the next gameweek only
fixtures_next_gameweek = fixtures_df[fixtures_df['event'] == next_gameweek]

# Save the filtered DataFrame to a CSV file (optional)
fixtures_next_gameweek.to_csv('fixtures_next_gameweek.csv', index=False)

print('Fixture data for next gameweek saved to fixtures_next_gameweek.csv')

"""now starting to make the fixture difficulty modifier"""


team_difficulty_dict = {}
for index, row in fixtures_next_gameweek.iterrows():
  team_h = row['team_h']
  team_a = row['team_a']
  team_h_difficulty = row['team_h_difficulty']
  team_a_difficulty = row['team_a_difficulty']

  if team_h not in team_difficulty_dict:
    team_difficulty_dict[team_h] = team_h_difficulty
  if team_a not in team_difficulty_dict:
    team_difficulty_dict[team_a] = team_a_difficulty

print(team_difficulty_dict)

difficulty_multiplier = {
    1: 1.2,  # easiest
    2: 1.1,
    3: 1.0,  # neutral
    4: 0.9,
    5: 0.8   # hardest
}



def calculate_expected_points(player_row):
  """Calculates expected points based on various factors."""

  # Get the player's team
  player_team = player_row['team']

  # Find the fixture difficulty for the player's team
  if player_team in team_difficulty_dict:
    fixture_difficulty = team_difficulty_dict[player_team]
  else:
    fixture_difficulty = 3  # Default to neutral if team not found

  # Use the difficulty multiplier based on the fixture difficulty
  if fixture_difficulty in difficulty_multiplier:
    difficulty_factor = difficulty_multiplier[fixture_difficulty]
  else:
    difficulty_factor = 1.0  # Default to neutral if difficulty not found

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

  # Calculate games played (approximation) only if minutes are above a threshold
  min_minutes = 200 # Example threshold - adjust as needed
  if player_row['minutes'] > min_minutes:
    games_played = player_row['minutes'] / 90
  else:
    games_played = 1  # Avoid division by zero and prevent skewing

  # Expected Points based on Goals, Assists, Clean Sheets, etc.
  expected_points = (
      (player_row['goals_scored'] / games_played) * goal_points +
      (player_row['assists'] / games_played) * assist_points +
      (player_row['clean_sheets'] / games_played) * clean_sheet_points +
      player_row['minutes'] * 0.01  # Basic playing time contribution
  )

  # Adjust for fixture difficulty
  expected_points = expected_points * difficulty_factor

  # Add points for playing 60+ minutes
  if player_row['minutes'] >= 60:
    expected_points += 1

  return expected_points

# Apply the function to calculate expected points for each player
fpl_data['expected_points'] = fpl_data.apply(calculate_expected_points, axis=1)

# Sort players by expected points
sorted_by_expected_points = fpl_data.sort_values('expected_points', ascending=False)

# Get all players by expected points
all_players_expected_points = sorted_by_expected_points

print("All Players by Expected Points:")
print(all_players_expected_points[['web_name', 'expected_points']].to_string())



# Filter players based on chance_of_playing_this_round
filtered_players = fpl_data[(fpl_data['chance_of_playing_this_round'] >= 75) | (fpl_data['chance_of_playing_this_round'].isnull())]

# Sort the filtered players by expected points
sorted_filtered_players = filtered_players.sort_values('expected_points', ascending=False)

# Print the filtered and sorted players
print("Players with chance_of_playing_this_round >= 75 or NULL, sorted by expected points:")
print(sorted_filtered_players[['web_name', 'expected_points', 'chance_of_playing_this_round']].to_string())



import matplotlib.pyplot as plt

# Filter players based on chance_of_playing_this_round
filtered_players = fpl_data[(fpl_data['chance_of_playing_this_round'] >= 75) ]

# Sort the filtered players by expected points
sorted_filtered_players = filtered_players.sort_values('expected_points', ascending=False)

# Get the top 5 players
top_5_players = sorted_filtered_players.head(5)

# Create a bar graph
plt.figure(figsize=(10, 6))
plt.bar(top_5_players['web_name'], top_5_players['expected_points'])
plt.xlabel('Player Name')
plt.ylabel('Expected Points')
plt.title('Top 5 Players with >= 75% Chance of Starting =')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()





# Get the top 5 players based on expected points
top_5_players = all_players_expected_points.nlargest(5, 'expected_points')

# Create a bar chart
plt.figure(figsize=(10, 6))
plt.bar(top_5_players['web_name'], top_5_players['expected_points'])
plt.xlabel('Player Name')
plt.ylabel('Expected Points')
plt.title('Top 5 Players for Next Gameweek')
plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
plt.tight_layout()
plt.show()