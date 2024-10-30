import requests
import pandas as pd

class FPLDataFetcher:
    """Class to fetch and manage FPL player data."""
    
    PLAYER_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    
    def fetch_player_data(self):
        """Fetches player data from the FPL API and returns it as a DataFrame."""
        response = requests.get(self.PLAYER_URL)
        player_data = response.json()['elements']
        return pd.DataFrame(player_data)

class Player:
    """Represents a player with relevant stats and expected points calculation."""
    
    def __init__(self, player_data):
        self.id = player_data['id']
        self.first_name = player_data['first_name']
        self.second_name = player_data['second_name']
        self.team = player_data['team']
        self.position = player_data['element_type']
        self.total_points = player_data['total_points']
        self.minutes = player_data['minutes']
        self.goals_scored = player_data['goals_scored']
        self.assists = player_data['assists']
        self.clean_sheets = player_data['clean_sheets']
        self.bonus = player_data['bonus']
        self.status = player_data['status']  # Active ('a'), Injured ('i'), etc.
        
    def is_available(self):
        """Check if the player is active and likely to play."""
        return self.status == 'a'
    
    def calculate_expected_points(self):
        """Calculate expected points based on an algorithm involving goals, assists, and recent performance."""
        # Example formula for expected points
        base_points = self.total_points
        goal_contribution = self.goals_scored * 4  # Assuming 4 points per goal
        assist_contribution = self.assists * 3     # Assuming 3 points per assist
        clean_sheet_bonus = self.clean_sheets * 1  # Assuming 1 point per clean sheet
        
        # Expected points formula — feel free to adjust this based on your actual algorithm
        expected_points = base_points + goal_contribution + assist_contribution + clean_sheet_bonus + self.bonus
        return expected_points

class TeamSelector:
    """Class to represent and select an active team and calculate expected points."""
    
    def __init__(self, players_data):
        # Filter to only include players who are available (status 'a')
        self.players = [Player(player) for _, player in players_data.iterrows() if Player(player).is_available()]

    def select_squad(self):
        """Select the best starting 11 and a 4-player bench based on total points among active players."""
        # Sort players by total points in descending order
        sorted_players = sorted(self.players, key=lambda player: player.total_points, reverse=True)
        
        # Starting 11 and 4-player bench
        starting_11 = sorted_players[:11]
        bench = sorted_players[11:15]
        
        return starting_11, bench

    def calculate_squad_expected_points(self):
        """Calculate the expected points for the starting 11 and the 4-player bench."""
        starting_11, bench = self.select_squad()
        
        starting_11_points = sum(player.calculate_expected_points() for player in starting_11)
        bench_points = sum(player.calculate_expected_points() for player in bench)
        
        return starting_11_points, bench_points

# Usage example
fetcher = FPLDataFetcher()
players_data = fetcher.fetch_player_data()

# Instantiate TeamSelector with filtered players
team_selector = TeamSelector(players_data)

# Calculate expected points for the starting 11 and the bench
starting_11_points, bench_points = team_selector.calculate_squad_expected_points()

# Display the results
print("Expected Points of Starting 11:", starting_11_points)
print("Expected Points of Bench:", bench_points)
