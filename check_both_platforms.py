#!/usr/bin/env python3
"""检查两个平台的Nets @ Wizards比赛数据"""

import requests
import json
import math

print("=" * 60)
print("检查 Polymarket")
print("=" * 60)

# Polymarket
url = "https://gamma-api.polymarket.com/events"
params = {'closed': 'false', 'tag_id': '745', 'limit': 100}
response = requests.get(url, params=params, timeout=10)
events = response.json()

for event in events:
    title = event.get('title', '')
    slug = event.get('slug', '')
    if 'nba-bkn-was-2025-11-16' in slug:
        print(f"\n找到: {title}")
        for market in event.get('markets', []):
            if market.get('question') == title:
                outcomes = json.loads(market.get('outcomes', '[]'))
                prices = json.loads(market.get('outcomePrices', '[]'))

                print(f"\n原始API数据:")
                for outcome, price in zip(outcomes, prices):
                    print(f"  {outcome}: {price} ({float(price)*100}%)")

                # 测试所有可能的归一化方法
                prob1 = float(prices[0]) * 100
                prob2 = float(prices[1]) * 100
                floor1 = math.floor(prob1)
                floor2 = math.floor(prob2)
                remainder = 100 - (floor1 + floor2)

                print(f"\nfloor1={floor1}, floor2={floor2}, remainder={remainder}")

                # 方法1: 余数给大的
                if prob1 >= prob2:
                    m1_1, m1_2 = floor1 + remainder, floor2
                else:
                    m1_1, m1_2 = floor1, floor2 + remainder
                print(f"方法1(余数给大的): {outcomes[0]} {m1_1}%, {outcomes[1]} {m1_2}%")

                # 方法2: 余数给小的
                if prob1 <= prob2:
                    m2_1, m2_2 = floor1 + remainder, floor2
                else:
                    m2_1, m2_2 = floor1, floor2 + remainder
                print(f"方法2(余数给小的): {outcomes[0]} {m2_1}%, {outcomes[1]} {m2_2}%")

                # 方法3: 用round
                round1 = round(prob1)
                round2 = 100 - round1
                print(f"方法3(round第一个): {outcomes[0]} {round1}%, {outcomes[1]} {round2}%")

                print(f"\n官网显示: BKN 43%, WAS 57%")
                break
        break

print("\n" + "=" * 60)
print("检查 Kalshi")
print("=" * 60)

# Kalshi
url = "https://api.elections.kalshi.com/trade-api/v2/markets"
params = {'series_ticker': 'KXNBAGAME', 'status': 'open', 'limit': 100}
response = requests.get(url, params=params, timeout=10)
data = response.json()
markets = data.get('markets', [])

bkn_was_markets = {}
for market in markets:
    ticker = market.get('ticker', '')
    title = market.get('title', '')
    if '25NOV16BKNWAS' in ticker:
        team_code = ticker.split('-')[-1]
        last_price = market.get('last_price', 0)
        bkn_was_markets[team_code] = {
            'title': title,
            'price': last_price
        }

if bkn_was_markets:
    print(f"\n找到 Brooklyn vs Washington:")
    print(f"\n原始API数据:")
    for team, info in bkn_was_markets.items():
        print(f"  {team}: {info['price']} cents")

    # Kalshi normalization
    codes = list(bkn_was_markets.keys())
    if len(codes) == 2:
        raw1 = bkn_was_markets[codes[0]]['price']
        raw2 = bkn_was_markets[codes[1]]['price']
        total = raw1 + raw2

        if total > 0:
            pct1 = (raw1 / total) * 100
            pct2 = (raw2 / total) * 100
            floor1 = math.floor(pct1)
            floor2 = math.floor(pct2)
            remainder = 100 - (floor1 + floor2)

            print(f"\npct1={pct1:.2f}, pct2={pct2:.2f}")
            print(f"floor1={floor1}, floor2={floor2}, remainder={remainder}")

            # 方法1: 余数给小的
            if raw1 <= raw2:
                m1_1, m1_2 = floor1 + remainder, floor2
            else:
                m1_1, m1_2 = floor1, floor2 + remainder
            print(f"方法1(余数给小的): {codes[0]} {m1_1}%, {codes[1]} {m1_2}%")

            # 方法2: 余数给大的
            if raw1 >= raw2:
                m2_1, m2_2 = floor1 + remainder, floor2
            else:
                m2_1, m2_2 = floor1, floor2 + remainder
            print(f"方法2(余数给大的): {codes[0]} {m2_1}%, {codes[1]} {m2_2}%")

            print(f"\n官网显示: Brooklyn 44%, Washington 56%")
