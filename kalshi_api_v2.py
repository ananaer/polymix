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
        Get NBA games from Kalshi with RAW orderbook data (no normalization)

        Returns orderbook data:
        - yes_bid: 卖出价（你能得到的价格）
        - yes_ask: 买入价（你需要支付的价格）
        - spread: 价差
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
                parts = ticker.split('-')
                if len(parts) < 3:
                    continue

                game_id = parts[1]
                team_code = parts[2]

                # Extract team names from title
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
                    continue

                # Store RAW orderbook data
                orderbook = {
                    'yes_bid': market.get('yes_bid', 0),  # 卖出价
                    'yes_ask': market.get('yes_ask', 0),  # 买入价
                    'last_price': market.get('last_price', 0),
                    'volume': market.get('volume', 0)
                }

                # Initialize game data
                if game_id not in games_dict:
                    games_dict[game_id] = {
                        'platform': 'Kalshi',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'close_time': market.get('close_time', ''),
                    }

                # Store orderbook for each team
                if team_code == away_code:
                    games_dict[game_id]['away_orderbook'] = orderbook
                elif team_code == home_code:
                    games_dict[game_id]['home_orderbook'] = orderbook

            # Convert to list and calculate spreads
            games = []
            for game_id, game_data in games_dict.items():
                if 'away_orderbook' in game_data and 'home_orderbook' in game_data:
                    away_ob = game_data['away_orderbook']
                    home_ob = game_data['home_orderbook']

                    # Calculate total spread
                    total_ask = away_ob['yes_ask'] + home_ob['yes_ask']
                    total_bid = away_ob['yes_bid'] + home_ob['yes_bid']
                    spread = total_ask - 100

                    # Add summary data
                    game_data['total_ask'] = total_ask
                    game_data['total_bid'] = total_bid
                    game_data['spread'] = spread

                    games.append(game_data)

            return games

        except requests.RequestException as e:
            print(f"Error fetching Kalshi data: {e}")
            return []

    def get_today_games(self) -> List[Dict]:
        """Get today's NBA games"""
        return self.get_nba_games()
