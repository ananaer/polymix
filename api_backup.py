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
import os
from collections import defaultdict, deque

app = Flask(__name__, static_folder='static')
CORS(app)

# Cache data to avoid too frequent API calls
cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 30  # Cache for 30 seconds
}

# Historical data storage (keep last 60 data points = 30 minutes at 30s intervals)
game_history = defaultdict(lambda: {
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

def calculate_comparisons(matched_games):
    """Calculate odds comparisons"""
    comparisons = []

    for poly_game, kalshi_game in matched_games:
        away_diff = abs(poly_game['away_prob'] - kalshi_game['away_prob'])
        home_diff = abs(poly_game['home_prob'] - kalshi_game['home_prob'])
        max_diff = max(away_diff, home_diff)

        # Extract game time from end_date
        game_time = poly_game.get('end_date', '')[:16] if poly_game.get('end_date') else ''

        comparison = {
            'away_team': poly_game['away_team'],
            'home_team': poly_game['home_team'],
            'away_code': poly_game['away_code'],
            'home_code': poly_game['home_code'],
            'polymarket': {
                'away': round(poly_game['away_prob'], 1),
                'home': round(poly_game['home_prob'], 1)
            },
            'kalshi': {
                'away': round(kalshi_game['away_prob'], 1),
                'home': round(kalshi_game['home_prob'], 1)
            },
            'diff': {
                'away': round(away_diff, 1),
                'home': round(home_diff, 1),
                'max': round(max_diff, 1)
            },
            'game_time': game_time
        }

        comparisons.append(comparison)

    # Sort by max difference (descending)
    comparisons.sort(key=lambda x: x['diff']['max'], reverse=True)

    return comparisons

@app.route('/api/odds')
def get_odds():
    """Get NBA odds comparison data"""
    # Check cache
    now = datetime.now()
    if cache['data'] and cache['timestamp']:
        elapsed = (now - cache['timestamp']).seconds
        if elapsed < cache['cache_duration']:
            return jsonify(cache['data'])

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

        # Match and compare
        matched = match_games(poly_games, kalshi_games)
        comparisons = calculate_comparisons(matched)

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
        cache['data'] = result
        cache['timestamp'] = now

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
