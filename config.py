#!/usr/bin/env python3
"""
Configuration file for PolyMix
Add your API keys here
"""

import os

# API Keys
API_KEYS = {
    'ODDS_API_KEY': os.environ.get('ODDS_API_KEY', ''),
    'PROP_ODDS_KEY': os.environ.get('PROP_ODDS_KEY', ''),
}

# Platform Settings
PLATFORMS = {
    'polymarket': {
        'enabled': True,
        'name': 'Polymarket',
        'color': '#6366f1',  # Indigo
        'requires_key': False
    },
    'kalshi': {
        'enabled': True,
        'name': 'Kalshi',
        'color': '#10b981',  # Green
        'requires_key': False
    },
    'odds_api': {
        'enabled': True,  # Enable when you add API key
        'name': 'Sportsbooks',
        'color': '#f59e0b',  # Amber
        'requires_key': True,
        'description': 'Aggregated odds from DraftKings, FanDuel, BetMGM, etc.'
    },
    'manifold': {
        'enabled': True,  # Enable if you want community predictions
        'name': 'Manifold',
        'color': '#8b5cf6',  # Purple
        'requires_key': False,
        'description': 'Community prediction market'
    }
}

# Cache settings
CACHE_DURATION = 30  # seconds

# Display settings
MAX_GAMES_DISPLAYED = 100
SHOW_INACTIVE_PLATFORMS = True
