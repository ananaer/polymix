#!/usr/bin/env python3
"""
套利检测器 - 自动识别 Polymarket 和 Kalshi 之间的套利机会
"""

from typing import List, Dict, Optional
from polymarket_api_v2 import PolymarketAPI
from kalshi_api_v2 import KalshiAPI

class ArbitrageDetector:
    """
    套利检测器

    考虑因素：
    - Polymarket 手续费: ~1-2%
    - Kalshi 手续费: ~7%
    - Gas费 (Polymarket on Polygon): ~$0.01-0.10
    """

    # 手续费率
    POLY_FEE = 0.02   # 2%
    KALSHI_FEE = 0.07 # 7%

    def __init__(self):
        self.poly_api = PolymarketAPI()
        self.kalshi_api = KalshiAPI()

    def get_arbitrage_opportunities(self, sport='nba', min_profit=0.5) -> List[Dict]:
        """
        查找套利机会

        Args:
            sport: 'nba' or 'nfl'
            min_profit: 最小利润百分比 (0.5 = 0.5%)

        Returns:
            List of arbitrage opportunities with详细说明
        """
        # 获取数据
        poly_games = self.poly_api.get_nba_games()
        kalshi_games = self.kalshi_api.get_nba_games()

        # 匹配比赛
        opportunities = []

        for poly_game in poly_games:
            for kalshi_game in kalshi_games:
                # 尝试匹配比赛
                if self._games_match(poly_game, kalshi_game):
                    # 检查套利机会
                    arb = self._check_arbitrage(poly_game, kalshi_game)
                    if arb and arb['profit_pct'] >= min_profit:
                        opportunities.append(arb)

        # 按利润排序
        opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
        return opportunities

    def _games_match(self, poly_game: Dict, kalshi_game: Dict) -> bool:
        """检查两个比赛是否匹配"""
        # 使用 team codes 匹配
        poly_teams = {poly_game['away_code'], poly_game['home_code']}
        kalshi_teams = {kalshi_game['away_code'], kalshi_game['home_code']}
        return poly_teams == kalshi_teams

    def _check_arbitrage(self, poly_game: Dict, kalshi_game: Dict) -> Optional[Dict]:
        """
        检查套利机会

        策略1: 在 Polymarket 买入，在 Kalshi 卖出
        策略2: 在 Kalshi 买入，在 Polymarket 卖出
        """
        results = []

        # 获取队伍代码 (确保顺序一致)
        away_code = poly_game['away_code']
        home_code = poly_game['home_code']

        # Polymarket 价格 (0-1 scale)
        poly_away = poly_game['away_price']
        poly_home = poly_game['home_price']

        # Kalshi 订单簿 (cents)
        kalshi_away_ob = kalshi_game['away_orderbook']
        kalshi_home_ob = kalshi_game['home_orderbook']

        # === 策略 1a: Poly买away, Kalshi卖away ===
        # 在 Poly 买 away: 花费 poly_away (+ fee)
        # 在 Kalshi 卖 away: 得到 kalshi_away_ob['yes_bid'] cents
        poly_cost = poly_away * (1 + self.POLY_FEE) * 100  # convert to cents
        kalshi_revenue = kalshi_away_ob['yes_bid'] * (1 - self.KALSHI_FEE)
        profit_1a = kalshi_revenue - poly_cost

        if profit_1a > 0:
            results.append({
                'team': f"{poly_game['away_team']} ({away_code})",
                'strategy': f"在Polymarket买入 {poly_game['away_team']}, 在Kalshi卖出",
                'poly_action': f"买入 @ {poly_away:.3f} ({poly_away*100:.1f}¢)",
                'kalshi_action': f"卖出 @ {kalshi_away_ob['yes_bid']}¢ bid",
                'poly_cost': poly_cost,
                'kalshi_revenue': kalshi_revenue,
                'profit': profit_1a,
                'profit_pct': (profit_1a / poly_cost) * 100 if poly_cost > 0 else 0,
                'game': f"{poly_game['away_team']} vs {poly_game['home_team']}",
                'details': {
                    'poly_price': poly_away,
                    'poly_fee': self.POLY_FEE * 100,
                    'kalshi_bid': kalshi_away_ob['yes_bid'],
                    'kalshi_fee': self.KALSHI_FEE * 100
                }
            })

        # === 策略 1b: Poly买home, Kalshi卖home ===
        poly_cost = poly_home * (1 + self.POLY_FEE) * 100
        kalshi_revenue = kalshi_home_ob['yes_bid'] * (1 - self.KALSHI_FEE)
        profit_1b = kalshi_revenue - poly_cost

        if profit_1b > 0:
            results.append({
                'team': f"{poly_game['home_team']} ({home_code})",
                'strategy': f"在Polymarket买入 {poly_game['home_team']}, 在Kalshi卖出",
                'poly_action': f"买入 @ {poly_home:.3f} ({poly_home*100:.1f}¢)",
                'kalshi_action': f"卖出 @ {kalshi_home_ob['yes_bid']}¢ bid",
                'poly_cost': poly_cost,
                'kalshi_revenue': kalshi_revenue,
                'profit': profit_1b,
                'profit_pct': (profit_1b / poly_cost) * 100 if poly_cost > 0 else 0,
                'game': f"{poly_game['away_team']} vs {poly_game['home_team']}",
                'details': {
                    'poly_price': poly_home,
                    'poly_fee': self.POLY_FEE * 100,
                    'kalshi_bid': kalshi_home_ob['yes_bid'],
                    'kalshi_fee': self.KALSHI_FEE * 100
                }
            })

        # === 策略 2a: Kalshi买away, Poly卖away ===
        # 注意: Polymarket 没有直接的 bid/ask，假设可以用 price 卖出
        kalshi_cost = kalshi_away_ob['yes_ask'] * (1 + self.KALSHI_FEE)
        poly_revenue = poly_away * (1 - self.POLY_FEE) * 100
        profit_2a = poly_revenue - kalshi_cost

        if profit_2a > 0:
            results.append({
                'team': f"{poly_game['away_team']} ({away_code})",
                'strategy': f"在Kalshi买入 {poly_game['away_team']}, 在Polymarket卖出",
                'kalshi_action': f"买入 @ {kalshi_away_ob['yes_ask']}¢ ask",
                'poly_action': f"卖出 @ {poly_away:.3f} ({poly_away*100:.1f}¢)",
                'kalshi_cost': kalshi_cost,
                'poly_revenue': poly_revenue,
                'profit': profit_2a,
                'profit_pct': (profit_2a / kalshi_cost) * 100 if kalshi_cost > 0 else 0,
                'game': f"{poly_game['away_team']} vs {poly_game['home_team']}",
                'details': {
                    'kalshi_ask': kalshi_away_ob['yes_ask'],
                    'kalshi_fee': self.KALSHI_FEE * 100,
                    'poly_price': poly_away,
                    'poly_fee': self.POLY_FEE * 100
                }
            })

        # === 策略 2b: Kalshi买home, Poly卖home ===
        kalshi_cost = kalshi_home_ob['yes_ask'] * (1 + self.KALSHI_FEE)
        poly_revenue = poly_home * (1 - self.POLY_FEE) * 100
        profit_2b = poly_revenue - kalshi_cost

        if profit_2b > 0:
            results.append({
                'team': f"{poly_game['home_team']} ({home_code})",
                'strategy': f"在Kalshi买入 {poly_game['home_team']}, 在Polymarket卖出",
                'kalshi_action': f"买入 @ {kalshi_home_ob['yes_ask']}¢ ask",
                'poly_action': f"卖出 @ {poly_home:.3f} ({poly_home*100:.1f}¢)",
                'kalshi_cost': kalshi_cost,
                'poly_revenue': poly_revenue,
                'profit': profit_2b,
                'profit_pct': (profit_2b / kalshi_cost) * 100 if kalshi_cost > 0 else 0,
                'game': f"{poly_game['away_team']} vs {poly_game['home_team']}",
                'details': {
                    'kalshi_ask': kalshi_home_ob['yes_ask'],
                    'kalshi_fee': self.KALSHI_FEE * 100,
                    'poly_price': poly_home,
                    'poly_fee': self.POLY_FEE * 100
                }
            })

        # 返回最佳机会
        if results:
            return max(results, key=lambda x: x['profit_pct'])
        return None


def main():
    """测试套利检测"""
    detector = ArbitrageDetector()

    print("=" * 80)
    print("🔍 套利机会检测")
    print("=" * 80)

    opportunities = detector.get_arbitrage_opportunities(min_profit=0.1)

    if not opportunities:
        print("\n❌ 没有发现套利机会 (利润 >= 0.1%)")
    else:
        print(f"\n✅ 发现 {len(opportunities)} 个套利机会:\n")

        for i, opp in enumerate(opportunities, 1):
            print(f"【机会 {i}】{opp['game']}")
            print(f"  队伍: {opp['team']}")
            print(f"  策略: {opp['strategy']}")
            print(f"  步骤1: {opp.get('poly_action') or opp.get('kalshi_action')}")
            print(f"  步骤2: {opp.get('kalshi_action') or opp.get('poly_action')}")
            print(f"  预期利润: {opp['profit']:.2f}¢ ({opp['profit_pct']:.2f}%)")
            print(f"  详细:")
            for key, val in opp['details'].items():
                print(f"    - {key}: {val}")
            print()


if __name__ == '__main__':
    main()
