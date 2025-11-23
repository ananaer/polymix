#!/usr/bin/env python3
"""
订单簿数据总结 - 显示原始价格和价差
"""

from polymarket_api_v2 import PolymarketAPI
from kalshi_api_v2 import KalshiAPI

def main():
    poly_api = PolymarketAPI()
    kalshi_api = KalshiAPI()

    poly_games = poly_api.get_nba_games()
    kalshi_games = kalshi_api.get_nba_games()

    print("=" * 100)
    print("📊 订单簿数据总结")
    print("=" * 100)

    # Polymarket 数据
    print("\n【Polymarket】原始价格 (0.0-1.0 scale)\n")
    for i, game in enumerate(poly_games[:5], 1):
        total = game['away_price'] + game['home_price']
        print(f"{i}. {game['away_team']:15} @ {game['home_team']:15}")
        print(f"   Away: {game['away_price']:.4f} ({game['away_price']*100:5.1f}¢)")
        print(f"   Home: {game['home_price']:.4f} ({game['home_price']*100:5.1f}¢)")
        print(f"   Total: {total:.4f} ({total*100:.1f}¢)")
        print()

    # Kalshi 数据
    print("\n【Kalshi】订单簿数据 (cents)\n")
    for i, game in enumerate(kalshi_games[:5], 1):
        away_ob = game['away_orderbook']
        home_ob = game['home_orderbook']

        print(f"{i}. {game['away_team']:15} vs {game['home_team']:15}")
        print(f"   Away: Bid {away_ob['yes_bid']:2}¢ | Ask {away_ob['yes_ask']:2}¢")
        print(f"   Home: Bid {home_ob['yes_bid']:2}¢ | Ask {home_ob['yes_ask']:2}¢")
        print(f"   Total Ask: {game['total_ask']}¢ (价差 {game['spread']}¢)")
        print(f"   Total Bid: {game['total_bid']}¢")
        print()

    # 匹配的比赛
    print("\n【比较】Polymarket vs Kalshi (匹配的比赛)\n")

    matched = 0
    for poly_game in poly_games:
        for kalshi_game in kalshi_games:
            poly_teams = {poly_game['away_code'], poly_game['home_code']}
            kalshi_teams = {kalshi_game['away_code'], kalshi_game['home_code']}

            if poly_teams == kalshi_teams:
                matched += 1
                print(f"{matched}. {poly_game['away_team']} vs {poly_game['home_team']}")

                # 找到对应的队伍
                away_code = poly_game['away_code']
                home_code = poly_game['home_code']

                # Polymarket 价格
                poly_away = poly_game['away_price'] * 100
                poly_home = poly_game['home_price'] * 100

                # Kalshi 订单簿
                kalshi_away_bid = kalshi_game['away_orderbook']['yes_bid']
                kalshi_away_ask = kalshi_game['away_orderbook']['yes_ask']
                kalshi_home_bid = kalshi_game['home_orderbook']['yes_bid']
                kalshi_home_ask = kalshi_game['home_orderbook']['yes_ask']

                print(f"   {poly_game['away_team']:12} ({away_code}):")
                print(f"     Polymarket: {poly_away:5.1f}¢")
                print(f"     Kalshi Bid: {kalshi_away_bid:2}¢ | Ask: {kalshi_away_ask:2}¢")
                print(f"     价差: Poly vs K-Bid = {poly_away - kalshi_away_bid:+5.1f}¢, Poly vs K-Ask = {poly_away - kalshi_away_ask:+5.1f}¢")

                print(f"   {poly_game['home_team']:12} ({home_code}):")
                print(f"     Polymarket: {poly_home:5.1f}¢")
                print(f"     Kalshi Bid: {kalshi_home_bid:2}¢ | Ask: {kalshi_home_ask:2}¢")
                print(f"     价差: Poly vs K-Bid = {poly_home - kalshi_home_bid:+5.1f}¢, Poly vs K-Ask = {poly_home - kalshi_home_ask:+5.1f}¢")
                print()

                if matched >= 5:
                    break
        if matched >= 5:
            break

if __name__ == '__main__':
    main()
