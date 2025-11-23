#!/usr/bin/env python3
"""
PolyMix - NBA Odds Comparison Tool
Compares NBA game odds between Polymarket and Kalshi to find arbitrage opportunities
"""

from polymarket_api import PolymarketAPI
from kalshi_api import KalshiAPI
from team_mapping import NBA_TEAMS
from typing import List, Dict, Tuple
from datetime import datetime


def match_games(polymarket_games: List[Dict], kalshi_games: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """
    Match games between two platforms based on team codes

    Returns:
        List of (polymarket_game, kalshi_game) tuples
    """
    matched = []

    for poly_game in polymarket_games:
        poly_away = poly_game['away_code']
        poly_home = poly_game['home_code']

        # Find matching Kalshi game
        for kalshi_game in kalshi_games:
            kalshi_away = kalshi_game['away_code']
            kalshi_home = kalshi_game['home_code']

            # Match if same teams (in same order)
            if poly_away == kalshi_away and poly_home == kalshi_home:
                matched.append((poly_game, kalshi_game))
                break

    return matched


def calculate_diff(matched_games: List[Tuple[Dict, Dict]]) -> List[Dict]:
    """
    Calculate probability differences for matched games

    Returns:
        List of comparison dictionaries sorted by largest difference
    """
    comparisons = []

    for poly_game, kalshi_game in matched_games:
        away_code = poly_game['away_code']
        home_code = poly_game['home_code']

        away_diff = abs(poly_game['away_prob'] - kalshi_game['away_prob'])
        home_diff = abs(poly_game['home_prob'] - kalshi_game['home_prob'])
        max_diff = max(away_diff, home_diff)

        comparison = {
            'away_team': poly_game['away_team'],
            'home_team': poly_game['home_team'],
            'away_code': away_code,
            'home_code': home_code,
            'polymarket_away': poly_game['away_prob'],
            'polymarket_home': poly_game['home_prob'],
            'kalshi_away': kalshi_game['away_prob'],
            'kalshi_home': kalshi_game['home_prob'],
            'away_diff': away_diff,
            'home_diff': home_diff,
            'max_diff': max_diff,
        }

        comparisons.append(comparison)

    # Sort by max difference (descending)
    comparisons.sort(key=lambda x: x['max_diff'], reverse=True)

    return comparisons


def print_results(comparisons: List[Dict]):
    """Pretty print the comparison results"""

    if not comparisons:
        print("\n❌ No matching games found between platforms")
        return

    print("\n" + "="*100)
    print(f"{'NBA ODDS COMPARISON':^100}")
    print(f"{'Polymarket vs Kalshi':^100}")
    print(f"{'Updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^100}")
    print("="*100)

    for i, comp in enumerate(comparisons, 1):
        away = comp['away_team']
        home = comp['home_team']

        print(f"\n{i}. {away} @ {home}")
        print("-" * 100)

        # Away team
        poly_away = comp['polymarket_away']
        kalshi_away = comp['kalshi_away']
        away_diff = comp['away_diff']

        print(f"   {away:20} | Polymarket: {poly_away:5.1f}%  |  Kalshi: {kalshi_away:5.1f}%  |  Diff: {away_diff:5.1f}%")

        # Home team
        poly_home = comp['polymarket_home']
        kalshi_home = comp['kalshi_home']
        home_diff = comp['home_diff']

        print(f"   {home:20} | Polymarket: {poly_home:5.1f}%  |  Kalshi: {kalshi_home:5.1f}%  |  Diff: {home_diff:5.1f}%")

        # Highlight if significant difference (>5%)
        max_diff = comp['max_diff']
        if max_diff > 5:
            print(f"   ⚠️  SIGNIFICANT DIFFERENCE: {max_diff:.1f}%")

    print("\n" + "="*100)
    print(f"Total games compared: {len(comparisons)}")
    print("="*100 + "\n")


def main():
    """Main program"""

    print("🏀 PolyMix - NBA Odds Comparison Tool")
    print("Fetching data from Polymarket and Kalshi...\n")

    # Fetch data from both platforms
    print("📊 Fetching Polymarket data...")
    poly_api = PolymarketAPI()
    poly_games = poly_api.get_today_games()
    print(f"   Found {len(poly_games)} games on Polymarket")

    print("📊 Fetching Kalshi data...")
    kalshi_api = KalshiAPI()
    kalshi_games = kalshi_api.get_today_games()
    print(f"   Found {len(kalshi_games)} games on Kalshi")

    # Match games
    print("\n🔄 Matching games between platforms...")
    matched = match_games(poly_games, kalshi_games)
    print(f"   Matched {len(matched)} games")

    # Calculate differences
    comparisons = calculate_diff(matched)

    # Print results
    print_results(comparisons)


if __name__ == "__main__":
    main()
