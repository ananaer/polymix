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
        Get NBA games from Polymarket

        Args:
            date_filter: Optional date string in format 'YYYY-MM-DD' to filter games

        Returns:
            List of game dictionaries with standardized format
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

                # Filter for game events (contains 'vs.')
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
                    print(f"Warning: Could not normalize teams: {away_team} vs {home_team}")
                    continue

                # Find the Game Winner market (moneyline)
                # The moneyline market has question exactly equal to the event title
                winner_market = None
                for market in event.get('markets', []):
                    question = market.get('question', '')
                    if question == title:
                        winner_market = market
                        break

                # Fallback: if not found, try to find one with "Moneyline" that's NOT "1H Moneyline"
                if not winner_market:
                    for market in event.get('markets', []):
                        question = market.get('question', '')
                        if 'Moneyline' in question and '1H' not in question:
                            winner_market = market
                            break

                if not winner_market:
                    continue

                # Parse outcomes and prices
                try:
                    import math
                    outcomes = json.loads(winner_market.get('outcomes', '[]'))
                    prices = json.loads(winner_market.get('outcomePrices', '[]'))

                    if len(outcomes) != 2 or len(prices) != 2:
                        continue

                    # Process outcomes in their original order
                    outcome_data = []
                    for outcome, price in zip(outcomes, prices):
                        team_code = normalize_team_name(outcome, 'polymarket')
                        if team_code:
                            outcome_data.append({
                                'code': team_code,
                                'raw_prob': float(price) * 100
                            })

                    if len(outcome_data) != 2:
                        continue

                    # Normalize probabilities - give remainder to SMALLER value
                    prob1 = outcome_data[0]['raw_prob']
                    prob2 = outcome_data[1]['raw_prob']

                    floor1 = math.floor(prob1)
                    floor2 = math.floor(prob2)
                    remainder = 100 - (floor1 + floor2)

                    # Give remainder to the SMALLER raw probability
                    if prob1 <= prob2:
                        outcome_data[0]['prob'] = floor1 + remainder
                        outcome_data[1]['prob'] = floor2
                    else:
                        outcome_data[0]['prob'] = floor1
                        outcome_data[1]['prob'] = floor2 + remainder

                    # Map to team codes
                    probs = {
                        outcome_data[0]['code']: outcome_data[0]['prob'],
                        outcome_data[1]['code']: outcome_data[1]['prob']
                    }

                    game_data = {
                        'platform': 'Polymarket',
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_code': away_code,
                        'home_code': home_code,
                        'away_prob': probs.get(away_code, 0),
                        'home_prob': probs.get(home_code, 0),
                        'slug': slug,
                        'end_date': winner_market.get('endDate', ''),
                        'url': f'https://polymarket.com/event/{slug}',
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
