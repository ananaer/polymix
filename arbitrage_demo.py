#!/usr/bin/env python3
"""
套利分析演示 - 使用原始订单簿数据而非归一化概率

关键概念:
1. 归一化概率只用于展示，不反映真实市场成本
2. 套利需要看实际的买卖价差
3. Polymarket 使用 mid price, Kalshi 使用 bid/ask spread
"""

import requests
import json

def get_kalshi_orderbook():
    """获取 Kalshi 原始订单簿数据"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {'series_ticker': 'KXNBAGAME', 'status': 'open', 'limit': 100}

    response = requests.get(url, params=params, timeout=10)
    markets = response.json().get('markets', [])

    # 按比赛分组
    games = {}
    for market in markets:
        ticker = market.get('ticker', '')
        parts = ticker.split('-')
        if len(parts) >= 3:
            game_id = parts[1]
            team = parts[2]

            if game_id not in games:
                games[game_id] = {}

            games[game_id][team] = {
                'yes_bid': market.get('yes_bid', 0),      # 卖出价（你能得到的）
                'yes_ask': market.get('yes_ask', 0),      # 买入价（你需要付的）
                'last_price': market.get('last_price', 0),
                'volume': market.get('volume', 0)
            }

    return games

def get_polymarket_prices():
    """获取 Polymarket 价格"""
    url = "https://gamma-api.polymarket.com/events"
    params = {'closed': 'false', 'tag_id': '745', 'limit': 100}

    response = requests.get(url, params=params, timeout=10)
    events = response.json()

    games = {}
    for event in events:
        title = event.get('title', '')
        if ' vs. ' not in title:
            continue

        teams = title.split(' vs. ')
        if len(teams) != 2:
            continue

        # 找到 moneyline 市场
        for market in event.get('markets', []):
            if market.get('question') == title:
                outcomes = json.loads(market.get('outcomes', '[]'))
                prices = json.loads(market.get('outcomePrices', '[]'))

                if len(outcomes) == 2 and len(prices) == 2:
                    games[title] = {
                        outcomes[0]: float(prices[0]),  # 0.0 - 1.0
                        outcomes[1]: float(prices[1])
                    }
                break

    return games

def analyze_arbitrage():
    """分析套利机会"""
    print("=" * 70)
    print("套利分析：原始订单簿数据 vs 归一化概率")
    print("=" * 70)

    kalshi_games = get_kalshi_orderbook()
    poly_games = get_polymarket_prices()

    # 示例：Brooklyn vs Washington
    print("\n【示例：Brooklyn vs Washington】\n")

    # Kalshi 数据
    bkn_was_game = kalshi_games.get('25NOV16BKNWAS', {})
    if bkn_was_game:
        bkn_data = bkn_was_game.get('BKN', {})
        was_data = bkn_was_game.get('WAS', {})

        print("Kalshi 原始订单簿:")
        print(f"  Brooklyn:")
        print(f"    - Bid (卖出价): {bkn_data['yes_bid']}¢ ← 你能得到的价格")
        print(f"    - Ask (买入价): {bkn_data['yes_ask']}¢ ← 你需要支付的价格")
        print(f"  Washington:")
        print(f"    - Bid (卖出价): {was_data['yes_bid']}¢")
        print(f"    - Ask (买入价): {was_data['yes_ask']}¢")

        # 计算价差
        total_ask = bkn_data['yes_ask'] + was_data['yes_ask']
        spread = total_ask - 100
        print(f"\n  总买入成本: {bkn_data['yes_ask']} + {was_data['yes_ask']} = {total_ask}¢")
        print(f"  价差: {spread}¢ ({spread}%)")

        if spread > 0:
            print(f"  💡 这意味着如果你买入双方，成本是 {total_ask}¢，但总赔付只有 100¢")
            print(f"     → 你会损失 {spread}¢ (这就是市场做市商的利润)")

        # 归一化后的概率
        bkn_norm = round((bkn_data['yes_ask'] / total_ask) * 100)
        was_norm = 100 - bkn_norm
        print(f"\n  归一化显示概率: Brooklyn {bkn_norm}%, Washington {was_norm}%")
        print(f"  ⚠️  但这不是真实交易成本！")

    # Polymarket 数据
    print("\n" + "-" * 70)
    poly_bkn_was = poly_games.get('Nets vs. Wizards', {})
    if poly_bkn_was:
        nets_price = poly_bkn_was.get('Nets', 0)
        wizards_price = poly_bkn_was.get('Wizards', 0)

        print("\nPolymarket 价格 (类似 mid price):")
        print(f"  Nets: {nets_price:.4f} ({nets_price*100:.2f}¢)")
        print(f"  Wizards: {wizards_price:.4f} ({wizards_price*100:.2f}¢)")
        print(f"  总和: {(nets_price + wizards_price)*100:.2f}¢")

        if nets_price + wizards_price < 1.0:
            spread = (1.0 - nets_price - wizards_price) * 100
            print(f"  价差: {spread:.2f}¢")

    print("\n" + "=" * 70)
    print("套利策略建议")
    print("=" * 70)
    print("""
1. ✓ 使用原始价格数据：
   - Kalshi: yes_bid (卖出) 和 yes_ask (买入)
   - Polymarket: outcomePrices (接近 mid price)

2. ✓ 寻找套利机会：
   if Polymarket_price < Kalshi_yes_bid:
       # 在 Polymarket 买入，在 Kalshi 卖出
       profit = (Kalshi_yes_bid - Polymarket_price * 100) - fees

   if Polymarket_price > Kalshi_yes_ask:
       # 在 Kalshi 买入，在 Polymarket 卖出
       profit = (Polymarket_price * 100 - Kalshi_yes_ask) - fees

3. ✗ 不要使用归一化概率：
   - 归一化只是为了展示"公平"概率
   - 不反映真实的交易成本和价差
   - 会隐藏套利机会

4. 考虑因素：
   - 交易手续费 (Polymarket ~1-2%, Kalshi ~7%)
   - 滑点 (大单会移动价格)
   - Gas fees (Polymarket on Polygon)
   - 时间风险 (两边下单之间的价格变动)
""")

if __name__ == '__main__':
    analyze_arbitrage()
