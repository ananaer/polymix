#!/usr/bin/env python3
"""
Kalshi API for NFL games
Fetches NFL game data from Kalshi
"""

import requests
from nfl_team_mapping import normalize_team_name, get_team_info

class NFLKalshiAPI:
    def __init__(self):
        self.BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
        self.NFL_SERIES = "KXNFLGAME"

    def get_nfl_games(self):
        """
        Fetch NFL games from Kalshi
        Returns list of game dictionaries with standardized format
        """
        url = f"{self.BASE_URL}/markets"
        params = {
            'series_ticker': self.NFL_SERIES,
            'status': 'open',
            'limit': 200
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            markets = data.get('markets', [])

            # Group markets by event (2 markets per game, one for each team)
            games_dict = {}
            for market in markets:
                event_ticker = market.get('event_ticker', '')
                ticker = market.get('ticker', '')
                team_name = market.get('yes_sub_title', '')

                if not event_ticker or not team_name:
                    continue

                # Normalize team name
                team_code = normalize_team_name(team_name, 'kalshi')
                if not team_code:
                    continue

                # Get probability directly from last_price (already in percentage)
                prob = market.get('last_price', 0)

                if event_ticker not in games_dict:
                    games_dict[event_ticker] = {'ticker': ticker}

                games_dict[event_ticker][team_code] = {
                    'name': team_name,
                    'prob': prob,
                    'team_code': team_code
                }

            # Convert to game format
            games = []
            for event_ticker, teams in games_dict.items():
                if len(teams) != 2:
                    continue

                team_codes = list(teams.keys())
                team1_code = team_codes[0]
                team2_code = team_codes[1]

                team1_info = get_team_info(team1_code)
                team2_info = get_team_info(team2_code)

                if not team1_info or not team2_info:
                    continue

                # Determine home/away based on event title pattern
                # Kalshi format is usually "Away at Home"
                team1_data = teams[team1_code]
                team2_data = teams[team2_code]

                # last_price is already in percentage format, use directly
                away_prob = team1_data['prob']
                home_prob = team2_data['prob']

                # Create game entry (assume first team is away, second is home)
                ticker = teams.get('ticker', '')
                game = {
                    'away_team': team1_info[0],  # Polymarket name for consistency
                    'home_team': team2_info[0],
                    'away_code': team1_code,
                    'home_code': team2_code,
                    'away_prob': away_prob,
                    'home_prob': home_prob,
                    'event_ticker': event_ticker,
                    'url': f'https://kalshi.com/markets/{ticker}' if ticker else '',
                }

                games.append(game)

            return games

        except Exception as e:
            print(f"Error fetching NFL games from Kalshi: {e}")
            return []


if __name__ == '__main__':
    # Test the API
    api = NFLKalshiAPI()
    games = api.get_nfl_games()
    print(f"\nFound {len(games)} NFL games:")
    for game in games[:5]:
        print(f"  {game['away_team']} @ {game['home_team']}: {game['away_prob']:.1f}% vs {game['home_prob']:.1f}%")
