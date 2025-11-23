#!/usr/bin/env python3
"""测试 Kalshi 使用哪个字段"""

import requests
import math

url = "https://api.elections.kalshi.com/trade-api/v2/markets"
params = {'series_ticker': 'KXNBAGAME', 'status': 'open', 'limit': 100}
response = requests.get(url, params=params, timeout=10)
data = response.json()
markets = data.get('markets', [])

print("测试 Brooklyn vs Washington 使用不同字段:\n")

bkn_market = None
was_market = None

for market in markets:
    if '25NOV16BKNWAS-BKN' in market.get('ticker', ''):
        bkn_market = market
    elif '25NOV16BKNWAS-WAS' in market.get('ticker', ''):
        was_market = market

if bkn_market and was_market:
    print("=== 方法1: 使用 last_price ===")
    bkn_last = bkn_market['last_price']
    was_last = was_market['last_price']
    print(f"BKN: {bkn_last}, WAS: {was_last}, 总和: {bkn_last + was_last}")

    print("\n=== 方法2: 使用 yes_bid ===")
    bkn_bid = bkn_market['yes_bid']
    was_bid = was_market['yes_bid']
    print(f"BKN: {bkn_bid}, WAS: {was_bid}, 总和: {bkn_bid + was_bid}")

    print("\n=== 方法3: 使用 yes_ask ===")
    bkn_ask = bkn_market['yes_ask']
    was_ask = was_market['yes_ask']
    print(f"BKN: {bkn_ask}, WAS: {was_ask}, 总和: {bkn_ask + was_ask}")

    print("\n=== 方法4: 使用 mid price (bid+ask)/2 ===")
    bkn_mid = (bkn_market['yes_bid'] + bkn_market['yes_ask']) / 2
    was_mid = (was_market['yes_bid'] + was_market['yes_ask']) / 2
    print(f"BKN: {bkn_mid}, WAS: {was_mid}, 总和: {bkn_mid + was_mid}")

    # 测试 yes_bid 归一化
    if bkn_bid + was_bid == 100:
        print(f"\n✓ yes_bid 已经是 100%: BKN {bkn_bid}%, WAS {was_bid}%")

    # 测试 yes_ask 归一化
    if bkn_ask + was_ask != 100:
        total = bkn_ask + was_ask
        bkn_pct = (bkn_ask / total) * 100
        was_pct = (was_ask / total) * 100

        bkn_floor = math.floor(bkn_pct)
        was_floor = math.floor(was_pct)
        remainder = 100 - (bkn_floor + was_floor)

        print(f"\n归一化 yes_ask:")
        print(f"  原始: BKN {bkn_pct:.2f}%, WAS {was_pct:.2f}%")
        print(f"  Floor: BKN {bkn_floor}, WAS {was_floor}, remainder {remainder}")

        # 余数给小的
        if bkn_ask <= was_ask:
            bkn_norm = bkn_floor + remainder
            was_norm = was_floor
        else:
            bkn_norm = bkn_floor
            was_norm = was_floor + remainder
        print(f"  归一化(余数给小的): BKN {bkn_norm}%, WAS {was_norm}%")

    print(f"\n官网显示: Brooklyn 44%, Washington 56%")
