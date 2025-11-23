#!/usr/bin/env python3
"""Debug Nets @ Wizards game raw API data"""

import requests
import json

BASE_URL = "https://gamma-api.polymarket.com"
NBA_TAG_ID = "745"

url = f"{BASE_URL}/events"
params = {
    'closed': 'false',
    'tag_id': NBA_TAG_ID,
    'limit': 100
}

response = requests.get(url, params=params, timeout=10)
events = response.json()

# Find Nets @ Wizards game
for event in events:
    title = event.get('title', '')
    if 'Nets' in title and 'Wizards' in title:
        print(f"\n找到比赛: {title}")
        print(f"Slug: {event.get('slug', '')}")

        # Find moneyline market
        for market in event.get('markets', []):
            question = market.get('question', '')
            if question == title:
                print(f"\n找到Moneyline市场:")
                outcomes = json.loads(market.get('outcomes', '[]'))
                prices = json.loads(market.get('outcomePrices', '[]'))

                print(f"\nOutcomes (原始顺序):")
                for i, (outcome, price) in enumerate(zip(outcomes, prices)):
                    raw_pct = float(price) * 100
                    print(f"  [{i}] {outcome}: {price} ({raw_pct}%)")

                # Test normalization
                import math
                prob1 = float(prices[0]) * 100
                prob2 = float(prices[1]) * 100
                floor1 = math.floor(prob1)
                floor2 = math.floor(prob2)
                remainder = 100 - (floor1 + floor2)

                print(f"\n归一化计算:")
                print(f"  prob1 = {prob1}, floor1 = {floor1}")
                print(f"  prob2 = {prob2}, floor2 = {floor2}")
                print(f"  remainder = {remainder}")

                # Method: give remainder to LARGER value
                if prob1 >= prob2:
                    normalized1 = floor1 + remainder
                    normalized2 = floor2
                    print(f"  prob1 >= prob2, 余数给第一个")
                else:
                    normalized1 = floor1
                    normalized2 = floor2 + remainder
                    print(f"  prob1 < prob2, 余数给第二个")

                print(f"\n结果:")
                print(f"  {outcomes[0]}: {normalized1}%")
                print(f"  {outcomes[1]}: {normalized2}%")
                print(f"  总和: {normalized1 + normalized2}%")

                break
        break
