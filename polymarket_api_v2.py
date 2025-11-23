import requests
import json
from typing import List, Dict, Optional
from team_mapping import normalize_team_name

class PolymarketAPI:
    BASE_URL = "https://gamma-api.polymarket.com"
    NBA_TAG_ID = "745"

    def __init__(self):
        self.session = requests.Session()

    def get_nba_games(self, date_filter: Optional[str] = None) -> List[Dict]:
        """
        Get NBA games from Polymarket with RAW price data (no normalization)

        Returns raw outcome prices (0.0 - 1.0 scale)
        """
        url = f"{self.BASE_URL}/events"
        params = {
            'closed': 'false',
            'tag_id': self.NBA_TAG_ID,
            'limit': 100
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            events = response.json()

            games = []
            for event in events:
                title = event.get('title', '')
                slug = event.get('slug', '')

                # Filter for game events
                if ' vs. ' not in title:
                    continue

                # Optional date filtering
                if date_filter and date_filter not in slug:
                    continue

                # Extract team names
                teams = title.split(' vs. ')
                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()

                # Get team codes
                away_code = normalize_team_name(away_team, 'polymarket')
                home_code = normalize_team_name(home_team, 'polymarket')

                if not away_code or not home_code:
                    continue

                # Find the moneyline market
                winner_market = None
                for market in event.get('markets', []):
                    question = market.get('question', '')
                    if question == title:
                        winner_market = market
                        break

                if not winner_market:
                    for market in event.get('markets', []):
                        question = market.get('question', '')
                        if 'Moneyline' in question and '1H' not in question:
                            winner_market = market
                            break

                if not winner_market:
                    continue

                # Parse outcomes and prices - KEEP RAW VALUES
                try:
                    outcomes = json.loads(winner_market.get('outcomes', '[]'))
                    prices = json.loads(winner_market.get('outcomePrices', '[]'))

                    if len(outcomes) != 2 or len(prices) != 2:
                        continue

                    # Map outcomes to team codes and keep raw prices
                    team_prices = {}
                    for outcome, price in zip(outcomes, prices):
                        team_code = normalize_team_name(outcome, 'polymarket')
                        if team_code:
                            team_prices[team_code] = float(price)  # 0.0 - 1.0

                    if len(team_prices) != 2:
                        continue

                    # Calculate total (should be ~1.0 or slightly less for Polymarket)
                    total = sum(team_prices.values())

                    game_data = {
                        'platform': 'Polymarket',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'away_price': team_prices.get(away_code, 0),  # Raw price (0-1)
                        'home_price': team_prices.get(home_code, 0),
                        'total_price': total,
                        'slug': slug,
                        'end_date': winner_market.get('endDate', ''),
                    }

                    games.append(game_data)

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing market data for {title}: {e}")
                    continue

            return games

        except requests.RequestException as e:
            print(f"Error fetching Polymarket data: {e}")
            return []

    def get_today_games(self) -> List[Dict]:
        """Get today's NBA games"""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_nba_games(date_filter=today)
