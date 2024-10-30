import requests
import pandas as pd

class FPLDataFetcher:
    """Class to fetch and manage FPL player and fixture data."""
    
    PLAYER_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    FIXTURE_URL = 'https://fantasy.premierleague.com/api/fixtures/'

    def fetch_player_data(self):
        """Fetches player data from the FPL API and returns it as a DataFrame."""
        response = requests.get(self.PLAYER_URL)
        player_data = response.json()['elements']
        return pd.DataFrame(player_data)

    def fetch_fixture_data(self):
        """Fetches fixture data from the FPL API and returns it as a DataFrame."""
        response = requests.get(self.FIXTURE_URL)
        fixture_data = response.json()
        return pd.DataFrame(fixture_data)


class FixtureAnalyzer:
    """Class to analyze fixture data and calculate fixture difficulties."""
    
    def __init__(self, fixtures_df):
        self.fixtures_df = fixtures_df
        self.team_difficulty_dict = self._build_team_difficulty_dict()

    def _build_team_difficulty_dict(self):
        """Builds a dictionary of team fixture difficulties for the next gameweek."""
        team_difficulty = {}
        upcoming_fixtures = self.fixtures_df[self.fixtures_df['finished'] == False]
        next_gameweek = upcoming_fixtures['event'].min()
        fixtures_next_gameweek = self.fixtures_df[self.fixtures_df['event'] == next_gameweek]

        for _, row in fixtures_next_gameweek.iterrows():
            team_difficulty[row['team_h']] = row['team_h_difficulty']
            team_difficulty[row['team_a']] = row['team_a_difficulty']

        return team_difficulty

    def get_difficulty_for_team(self, team_id):
        """Returns the difficulty for a team based on the fixture."""
        return self.team_difficulty_dict.get(team_id, 3)  # Defaults to 3 (neutral)


class PlayerAnalyzer:
    """Class to analyze player data and calculate expected points, including position information."""
    
    difficulty_multiplier = {1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.8}
    position_map = {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}

    def __init__(self, player_df, fixture_analyzer):
        self.player_df = player_df
        self.fixture_analyzer = fixture_analyzer
        self.player_df['position'] = self.player_df['element_type'].map(self.position_map)  # Map position
        self.player_df['expected_points'] = self.player_df.apply(self.calculate_expected_points, axis=1)

    def calculate_expected_points(self, player_row):
        """Calculates expected points for a player based on performance and fixture difficulty."""
        team_id = player_row['team']
        fixture_difficulty = self.fixture_analyzer.get_difficulty_for_team(team_id)
        difficulty_factor = self.difficulty_multiplier.get(fixture_difficulty, 1.0)

        # Position-based points
        pos_points = {
            'goal': 0, 'assist': 0, 'clean_sheet': 0
        }
        if player_row['element_type'] in self.position_map:
            pos_type = self.position_map[player_row['element_type']]
            pos_points = {
                'Goalkeeper': {'goal': 10, 'assist': 3, 'clean_sheet': 4},
                'Defender': {'goal': 6, 'assist': 3, 'clean_sheet': 4},
                'Midfielder': {'goal': 5, 'assist': 3, 'clean_sheet': 1},
                'Forward': {'goal': 4, 'assist': 3, 'clean_sheet': 0}
            }.get(pos_type, pos_points)

        # Approximate games played and expected points
        games_played = max(player_row['minutes'] / 90, 1)  # Prevent division by zero
        expected_points = (
            (player_row['goals_scored'] / games_played) * pos_points['goal'] +
            (player_row['assists'] / games_played) * pos_points['assist'] +
            (player_row['clean_sheets'] / games_played) * pos_points['clean_sheet'] +
            (player_row['minutes'] / games_played) * 0.01  # Playing time contribution
        )

        # Adjust based on fixture difficulty
        expected_points *= difficulty_factor
        if player_row['minutes'] >= 60:
            expected_points += 1

        return expected_points

    def get_top_players_for_next_gameweek(self, min_minutes_threshold):
        """Filters and returns top players by expected points for the next gameweek."""
        filtered_players = self.player_df[self.player_df['minutes'] > min_minutes_threshold]
        return filtered_players.sort_values('expected_points', ascending=False)
    
    def create_team(self, budget=100):
        """Selects an optimal team within the budget and position constraints."""
        
        # Filter players by position
        goalkeepers = self.player_df[self.player_df['position'] == 'Goalkeeper'].sort_values(by='expected_points', ascending=False)
        defenders = self.player_df[self.player_df['position'] == 'Defender'].sort_values(by='expected_points', ascending=False)
        midfielders = self.player_df[self.player_df['position'] == 'Midfielder'].sort_values(by='expected_points', ascending=False)
        forwards = self.player_df[self.player_df['position'] == 'Forward'].sort_values(by='expected_points', ascending=False)

        # Select top players by position based on expected points
        selected_goalkeepers = goalkeepers.head(2)
        selected_defenders = defenders.head(5)
        selected_midfielders = midfielders.head(5)
        selected_forwards = forwards.head(3)

        # Combine selected players into a single DataFrame
        team = pd.concat([selected_goalkeepers, selected_defenders, selected_midfielders, selected_forwards])

        # Check budget constraint
        total_price = team['now_cost'].sum() / 10  # `now_cost` is typically in tenths of a million
        if total_price > budget:
            print("The selected team exceeds the budget. Adjusting selection...")
            return None  # Implement further optimization if needed, e.g., removing the lowest expected point player in each category until within budget

        print(f"Team selected within budget of {budget}: Total cost = {total_price}")
        return team[['web_name', 'position', 'expected_points', 'now_cost']]


# Usage
data_fetcher = FPLDataFetcher()

# Fetch and save player data
player_data = data_fetcher.fetch_player_data()
player_data.to_csv('fpl_player_data.csv', index=False)
print('Data saved to fpl_player_data.csv')

# Fetch and save fixture data
fixture_data = data_fetcher.fetch_fixture_data()
fixture_data.to_csv('fixture_info.csv', index=False)
print('Fixture data saved to fixture_info.csv')

# Initialize Fixture Analyzer and Player Analyzer
fixture_analyzer = FixtureAnalyzer(fixture_data)
player_analyzer = PlayerAnalyzer(player_data, fixture_analyzer)

# Calculate and display top players for the next gameweek
next_gameweek = fixture_analyzer.fixtures_df[fixture_analyzer.fixtures_df['finished'] == False]['event'].min()
min_minutes_threshold = (next_gameweek * 90) / 2
top_players = player_analyzer.get_top_players_for_next_gameweek(min_minutes_threshold)

print(f"\nPlayers with Expected Points for Next Gameweek ({next_gameweek}):")
print(top_players[['web_name', 'position', 'expected_points']].to_string())

selected_team = player_analyzer.create_team()
print(selected_team)
