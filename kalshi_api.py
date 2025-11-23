import requests
from typing import List, Dict
from collections import defaultdict
from team_mapping import normalize_team_name

class KalshiAPI:
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    NBA_SERIES = "KXNBAGAME"

    def __init__(self):
        self.session = requests.Session()

    def get_nba_games(self) -> List[Dict]:
        """
        Get NBA games from Kalshi

        Returns:
            List of game dictionaries with standardized format
        """
        url = f"{self.BASE_URL}/markets"
        params = {
            'series_ticker': self.NBA_SERIES,
            'status': 'open',
            'limit': 100
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            markets = data.get('markets', [])

            # Group markets by game (each game has 2 markets, one for each team)
            games_dict = defaultdict(dict)

            for market in markets:
                title = market.get('title', '')

                # Filter for Winner markets only
                if 'Winner?' not in title:
                    continue

                # Extract game identifier from ticker
                ticker = market.get('ticker', '')
                # Ticker format: KXNBAGAME-25NOV16BKNWAS-BKN
                parts = ticker.split('-')
                if len(parts) < 3:
                    continue

                game_id = parts[1]  # e.g., "25NOV16BKNWAS"
                team_code = parts[2]  # e.g., "BKN" or "WAS"

                # Extract team names from title
                # Format: "Brooklyn vs Washington Winner?"
                title_clean = title.replace(' Winner?', '')
                teams = title_clean.split(' vs ')
                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()

                # Get team codes
                away_code = normalize_team_name(away_team, 'kalshi')
                home_code = normalize_team_name(home_team, 'kalshi')

                if not away_code or not home_code:
                    print(f"Warning: Could not normalize Kalshi teams: {away_team} vs {home_team}")
                    continue

                # Get probability directly from last_price (already in percentage)
                last_price = market.get('last_price', 0)
                probability = last_price  # last_price is already the correct percentage

                # Store in games_dict
                if game_id not in games_dict:
                    games_dict[game_id] = {
                        'platform': 'Kalshi',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'close_time': market.get('close_time', ''),
                        'ticker': ticker,
                    }

                # Add probability for this team
                if team_code == away_code:
                    games_dict[game_id]['away_prob'] = probability
                elif team_code == home_code:
                    games_dict[game_id]['home_prob'] = probability

            # Convert to list and filter complete games (with both probabilities)
            games = []
            for game_id, game_data in games_dict.items():
                if 'away_prob' in game_data and 'home_prob' in game_data:
                    # last_price is already in percentage format, use directly
                    away_prob = game_data['away_prob']
                    home_prob = game_data['home_prob']

                    # Update game data with the direct values
                    game_data['away_prob'] = away_prob
                    game_data['home_prob'] = home_prob

                    # Add Kalshi market URL
                    ticker = game_data.get('ticker', '')
                    if ticker:
                        game_data['url'] = f'https://kalshi.com/markets/{ticker}'

                    games.append(game_data)

            return games

        except requests.RequestException as e:
            print(f"Error fetching Kalshi data: {e}")
            return []

    def get_today_games(self) -> List[Dict]:
        """Get today's NBA games (Kalshi API doesn't have easy date filtering, returns all open)"""
        return self.get_nba_games()
