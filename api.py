#!/usr/bin/env python3
"""
Flask API for PolyMix monitoring
Provides real-time NBA odds comparison data
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from polymarket_api import PolymarketAPI
from kalshi_api import KalshiAPI
from team_mapping import TEAM_LOGOS
from nfl_polymarket_api import NFLPolymarketAPI
from nfl_kalshi_api import NFLKalshiAPI
from nfl_team_mapping import NFL_TEAM_LOGOS
from odds_api_aggregator import OddsAPIAggregator
from manifold_api import ManifoldAPI
from config import PLATFORMS
import os
from collections import defaultdict, deque

app = Flask(__name__, static_folder='static')
CORS(app)

# Cache data to avoid too frequent API calls
nba_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 30  # Cache for 30 seconds
}

nfl_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 30  # Cache for 30 seconds
}

# Historical data storage (keep last 60 data points = 30 minutes at 30s intervals)
nba_game_history = defaultdict(lambda: {
    'diff_history': deque(maxlen=60),
    'poly_history': deque(maxlen=60),
    'kalshi_history': deque(maxlen=60),
    'timestamps': deque(maxlen=60)
})

nfl_game_history = defaultdict(lambda: {
    'diff_history': deque(maxlen=60),
    'poly_history': deque(maxlen=60),
    'kalshi_history': deque(maxlen=60),
    'timestamps': deque(maxlen=60)
})

def get_date_range():
    """Get today and tomorrow's date strings"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    return today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')

def match_games(polymarket_games, kalshi_games):
    """Match games between platforms"""
    matched = []
    for poly_game in polymarket_games:
        poly_away = poly_game['away_code']
        poly_home = poly_game['home_code']

        for kalshi_game in kalshi_games:
            kalshi_away = kalshi_game['away_code']
            kalshi_home = kalshi_game['home_code']

            if poly_away == kalshi_away and poly_home == kalshi_home:
                matched.append((poly_game, kalshi_game))
                break

    return matched

def match_additional_platform(base_games, additional_games):
    """Match additional platform games to base games"""
    matched_dict = {}
    for base_game in base_games:
        game_key = f"{base_game['away_code']}@{base_game['home_code']}"
        matched_dict[game_key] = None

        for add_game in additional_games:
            if (add_game['away_code'] == base_game['away_code'] and
                add_game['home_code'] == base_game['home_code']):
                matched_dict[game_key] = add_game
                break

    return matched_dict

def calculate_comparisons(matched_games, team_logos, game_history_dict, odds_games=None, manifold_games=None):
    """Calculate odds comparisons with historical tracking and analysis"""
    comparisons = []
    current_time = datetime.now()

    # Match additional platforms if provided
    odds_dict = {}
    manifold_dict = {}

    if odds_games:
        base_games = [poly_game for poly_game, _ in matched_games]
        odds_dict = match_additional_platform(base_games, odds_games)

    if manifold_games:
        base_games = [poly_game for poly_game, _ in matched_games]
        manifold_dict = match_additional_platform(base_games, manifold_games)

    for poly_game, kalshi_game in matched_games:
        away_diff = abs(poly_game['away_prob'] - kalshi_game['away_prob'])
        home_diff = abs(poly_game['home_prob'] - kalshi_game['home_prob'])
        max_diff = max(away_diff, home_diff)

        # Extract game time from end_date
        game_time = poly_game.get('end_date', '')[:16] if poly_game.get('end_date') else ''

        # Create unique game key
        game_key = f"{poly_game['away_code']}@{poly_game['home_code']}"

        # Get historical data for this game
        history = game_history_dict[game_key]

        # Add current data to history
        history['diff_history'].append(max_diff)
        history['poly_history'].append((poly_game['away_prob'], poly_game['home_prob']))
        history['kalshi_history'].append((kalshi_game['away_prob'], kalshi_game['home_prob']))
        history['timestamps'].append(current_time.isoformat())

        # Calculate trend (comparing recent 5 points vs older 5 points)
        trend = 'stable'
        trend_value = 0
        if len(history['diff_history']) >= 10:
            recent_avg = sum(list(history['diff_history'])[-5:]) / 5
            older_avg = sum(list(history['diff_history'])[-10:-5]) / 5
            trend_value = recent_avg - older_avg
            if trend_value > 0.5:
                trend = 'increasing'
            elif trend_value < -0.5:
                trend = 'decreasing'

        # Calculate price change (current vs 5 minutes ago = ~10 data points ago)
        poly_change = {'away': 0, 'home': 0}
        kalshi_change = {'away': 0, 'home': 0}
        if len(history['poly_history']) >= 10:
            old_poly = history['poly_history'][-10]
            poly_change['away'] = round(poly_game['away_prob'] - old_poly[0], 1)
            poly_change['home'] = round(poly_game['home_prob'] - old_poly[1], 1)

            old_kalshi = history['kalshi_history'][-10]
            kalshi_change['away'] = round(kalshi_game['away_prob'] - old_kalshi[0], 1)
            kalshi_change['home'] = round(kalshi_game['home_prob'] - old_kalshi[1], 1)

        # Calculate arbitrage opportunity score (0-100)
        arb_score = 0
        # Base score from difference (0-50)
        arb_score += min(max_diff * 5, 50)
        # Bonus for increasing trend (0-20)
        if trend == 'increasing':
            arb_score += min(abs(trend_value) * 10, 20)
        # Bonus for volatility (0-15)
        if len(history['diff_history']) >= 5:
            recent_diffs = list(history['diff_history'])[-5:]
            volatility = max(recent_diffs) - min(recent_diffs)
            arb_score += min(volatility * 3, 15)
        # Bonus for high absolute difference (0-15)
        if max_diff >= 8:
            arb_score += 15
        elif max_diff >= 5:
            arb_score += 10

        arb_score = min(round(arb_score), 100)

        # Get additional platform data if available
        game_key = f"{poly_game['away_code']}@{poly_game['home_code']}"
        odds_game = odds_dict.get(game_key)
        manifold_game = manifold_dict.get(game_key)

        comparison = {
            'away_team': poly_game['away_team'],
            'home_team': poly_game['home_team'],
            'away_code': poly_game['away_code'],
            'home_code': poly_game['home_code'],
            'away_logo': team_logos.get(poly_game['away_code'], ''),
            'home_logo': team_logos.get(poly_game['home_code'], ''),
            'polymarket': {
                'away': round(poly_game['away_prob'], 1),
                'home': round(poly_game['home_prob'], 1),
                'url': poly_game.get('url', '')
            },
            'kalshi': {
                'away': round(kalshi_game['away_prob'], 1),
                'home': round(kalshi_game['home_prob'], 1),
                'url': kalshi_game.get('url', '')
            },
            'odds_api': {
                'away': round(odds_game['away_prob'], 1) if odds_game else None,
                'home': round(odds_game['home_prob'], 1) if odds_game else None,
                'url': odds_game.get('url', '') if odds_game else '',
                'bookmakers': odds_game.get('bookmakers', []) if odds_game else []
            } if odds_game else None,
            'manifold': {
                'away': round(manifold_game['away_prob'], 1) if manifold_game else None,
                'home': round(manifold_game['home_prob'], 1) if manifold_game else None,
                'url': manifold_game.get('url', '') if manifold_game else ''
            } if manifold_game else None,
            'diff': {
                'away': round(away_diff, 1),
                'home': round(home_diff, 1),
                'max': round(max_diff, 1)
            },
            'trend': {
                'direction': trend,
                'value': round(trend_value, 1)
            },
            'price_change': {
                'polymarket': poly_change,
                'kalshi': kalshi_change
            },
            'arbitrage_score': arb_score,
            'game_time': game_time,
            'history': {
                'diff': list(history['diff_history']),
                'timestamps': list(history['timestamps'])
            }
        }

        comparisons.append(comparison)

    # Sort by arbitrage score (descending), then by max difference
    comparisons.sort(key=lambda x: (x['arbitrage_score'], x['diff']['max']), reverse=True)

    return comparisons

@app.route('/api/odds')
@app.route('/api/odds/nba')
def get_nba_odds():
    """Get NBA odds comparison data"""
    # Check cache
    now = datetime.now()
    if nba_cache['data'] and nba_cache['timestamp']:
        elapsed = (now - nba_cache['timestamp']).seconds
        if elapsed < nba_cache['cache_duration']:
            return jsonify(nba_cache['data'])

    try:
        # Get date range
        today, tomorrow = get_date_range()

        # Fetch from both platforms
        poly_api = PolymarketAPI()
        kalshi_api = KalshiAPI()

        # Get games for today and tomorrow
        poly_today = poly_api.get_nba_games(date_filter=today)
        poly_tomorrow = poly_api.get_nba_games(date_filter=tomorrow)
        poly_games = poly_today + poly_tomorrow

        kalshi_games = kalshi_api.get_nba_games()

        # Fetch from additional platforms if enabled
        odds_games = []
        manifold_games = []

        if PLATFORMS.get('odds_api', {}).get('enabled', False):
            try:
                odds_api = OddsAPIAggregator()
                odds_games = odds_api.get_nba_games()
                print(f"✅ Fetched {len(odds_games)} games from Odds API")
            except Exception as e:
                print(f"⚠️  Odds API error: {e}")

        if PLATFORMS.get('manifold', {}).get('enabled', False):
            try:
                manifold_api = ManifoldAPI()
                manifold_games = manifold_api.get_nba_games()
                print(f"✅ Fetched {len(manifold_games)} games from Manifold")
            except Exception as e:
                print(f"⚠️  Manifold API error: {e}")

        # Match and compare
        matched = match_games(poly_games, kalshi_games)
        comparisons = calculate_comparisons(
            matched, TEAM_LOGOS, nba_game_history,
            odds_games=odds_games,
            manifold_games=manifold_games
        )

        # Group by date
        today_games = []
        tomorrow_games = []

        for game in comparisons:
            game_date = game['game_time'][:10] if game['game_time'] else ''
            if game_date == today:
                today_games.append(game)
            elif game_date == tomorrow:
                tomorrow_games.append(game)

        result = {
            'success': True,
            'sport': 'nba',
            'timestamp': now.isoformat(),
            'dates': {
                'today': today,
                'tomorrow': tomorrow
            },
            'stats': {
                'total_games': len(comparisons),
                'today_games': len(today_games),
                'tomorrow_games': len(tomorrow_games),
                'poly_total': len(poly_games),
                'kalshi_total': len(kalshi_games),
                'matched': len(matched)
            },
            'games': {
                'today': today_games,
                'tomorrow': tomorrow_games
            }
        }

        # Update cache
        nba_cache['data'] = result
        nba_cache['timestamp'] = now

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': now.isoformat()
        }), 500

@app.route('/api/odds/nfl')
def get_nfl_odds():
    """Get NFL odds comparison data"""
    # Check cache
    now = datetime.now()
    if nfl_cache['data'] and nfl_cache['timestamp']:
        elapsed = (now - nfl_cache['timestamp']).seconds
        if elapsed < nfl_cache['cache_duration']:
            return jsonify(nfl_cache['data'])

    try:
        # Fetch from both platforms
        poly_api = NFLPolymarketAPI()
        kalshi_api = NFLKalshiAPI()

        poly_games = poly_api.get_nfl_games()
        kalshi_games = kalshi_api.get_nfl_games()

        # Match and compare
        matched = match_games(poly_games, kalshi_games)
        comparisons = calculate_comparisons(matched, NFL_TEAM_LOGOS, nfl_game_history)

        result = {
            'success': True,
            'sport': 'nfl',
            'timestamp': now.isoformat(),
            'stats': {
                'total_games': len(comparisons),
                'poly_total': len(poly_games),
                'kalshi_total': len(kalshi_games),
                'matched': len(matched)
            },
            'games': comparisons
        }

        # Update cache
        nfl_cache['data'] = result
        nfl_cache['timestamp'] = now

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': now.isoformat()
        }), 500

@app.route('/')
def index():
    """Serve the monitoring dashboard"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Create static folder if not exists
    os.makedirs('static', exist_ok=True)

    print("🏀 PolyMix API Server")
    print("📊 Starting server at http://localhost:5001")
    print("🔄 Data refreshes every 30 seconds")

    app.run(debug=True, host='0.0.0.0', port=5001)
