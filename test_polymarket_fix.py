#!/usr/bin/env python3
"""Test Polymarket probability normalization"""

from polymarket_api import PolymarketAPI
import json

api = PolymarketAPI()
games = api.get_nba_games()

print(f"\n找到 {len(games)} 场NBA比赛\n")

# Find Nets vs Wizards game
for game in games:
    if 'Nets' in game['away_team'] or 'Nets' in game['home_team']:
        print(f"找到Nets比赛:")
        print(f"  {game['away_team']} @ {game['home_team']}")
        print(f"  {game['away_code']}: {game['away_prob']}%")
        print(f"  {game['home_code']}: {game['home_prob']}%")
        print(f"  总和: {game['away_prob'] + game['home_prob']}%")
        print(f"  Slug: {game.get('slug', 'N/A')}")
        print()

print("\n前5场比赛:")
for i, game in enumerate(games[:5], 1):
    total = game['away_prob'] + game['home_prob']
    print(f"{i}. {game['away_team']} @ {game['home_team']}")
    print(f"   {game['away_prob']}% + {game['home_prob']}% = {total}%")
