#!/usr/bin/env python3
"""测试修复后的比例"""

from polymarket_api import PolymarketAPI
from kalshi_api import KalshiAPI

print("=" * 60)
print("测试 Polymarket (Nets vs Wizards)")
print("=" * 60)

poly_api = PolymarketAPI()
poly_games = poly_api.get_nba_games()

for game in poly_games:
    if 'Nets' in game['away_team'] and 'Wizards' in game['home_team']:
        print(f"\n{game['away_team']} @ {game['home_team']}")
        print(f"  {game['away_code']}: {game['away_prob']}%")
        print(f"  {game['home_code']}: {game['home_prob']}%")
        print(f"  总和: {game['away_prob'] + game['home_prob']}%")
        print(f"\n官网应该显示: Nets 43%, Wizards 57% (当API为0.425/0.575时)")
        break

print("\n" + "=" * 60)
print("测试 Kalshi (Brooklyn vs Washington)")
print("=" * 60)

kalshi_api = KalshiAPI()
kalshi_games = kalshi_api.get_nba_games()

for game in kalshi_games:
    if 'Brooklyn' in game['away_team'] or 'Brooklyn' in game['home_team']:
        if 'Washington' in game['away_team'] or 'Washington' in game['home_team']:
            print(f"\n{game['away_team']} vs {game['home_team']}")
            print(f"  {game['away_code']}: {game['away_prob']}%")
            print(f"  {game['home_code']}: {game['home_prob']}%")
            print(f"  总和: {game['away_prob'] + game['home_prob']}%")
            print(f"\n当前yes_bid: Brooklyn 42%, Washington 58%")
            break

print("\n" + "=" * 60)
print("测试其他比赛确保总和都是100%")
print("=" * 60)

print("\nPolymarket前5场:")
for i, game in enumerate(poly_games[:5], 1):
    total = game['away_prob'] + game['home_prob']
    status = "✓" if total == 100 else "✗"
    print(f"{i}. {game['away_team'][:15]:15} @ {game['home_team'][:15]:15} : {game['away_prob']:2}% + {game['home_prob']:2}% = {total:3}% {status}")

print("\nKalshi前5场:")
for i, game in enumerate(kalshi_games[:5], 1):
    total = game['away_prob'] + game['home_prob']
    status = "✓" if total == 100 else "✗"
    print(f"{i}. {game['away_team'][:15]:15} vs {game['home_team'][:15]:15} : {game['away_prob']:2}% + {game['home_prob']:2}% = {total:3}% {status}")
