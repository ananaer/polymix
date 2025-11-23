#!/usr/bin/env python3
"""Verify normalization logic with multiple games"""

import requests
import json
import math

BASE_URL = "https://gamma-api.polymarket.com"
NBA_TAG_ID = "745"

url = f"{BASE_URL}/events"
params = {
    'closed': 'false',
    'tag_id': NBA_TAG_ID,
    'limit': 20
}

response = requests.get(url, params=params, timeout=10)
events = response.json()

print("\n测试前10场比赛的归一化:\n")

count = 0
for event in events:
    if count >= 10:
        break

    title = event.get('title', '')
    if ' vs. ' not in title:
        continue

    # Find moneyline market
    for market in event.get('markets', []):
        question = market.get('question', '')
        if question == title:
            outcomes = json.loads(market.get('outcomes', '[]'))
            prices = json.loads(market.get('outcomePrices', '[]'))

            if len(outcomes) == 2 and len(prices) == 2:
                prob1 = float(prices[0]) * 100
                prob2 = float(prices[1]) * 100
                floor1 = math.floor(prob1)
                floor2 = math.floor(prob2)
                remainder = 100 - (floor1 + floor2)

                # Give remainder to LARGER value
                if prob1 >= prob2:
                    normalized1 = floor1 + remainder
                    normalized2 = floor2
                else:
                    normalized1 = floor1
                    normalized2 = floor2 + remainder

                print(f"{count + 1}. {title}")
                print(f"   原始: {outcomes[0]} {prob1:.1f}%, {outcomes[1]} {prob2:.1f}%")
                print(f"   归一化: {outcomes[0]} {normalized1}%, {outcomes[1]} {normalized2}% (总和={normalized1+normalized2}%)")
                print()

                count += 1
                break
