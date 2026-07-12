"""
Animation modules for Word Quest game.

Contains special visual effects and celebration animations.
"""

from src.animations.rocket_boost import RocketBoostAnimation, create_rocket_boost_animation
from src.animations.planet_discovery import PlanetDiscoveryAnimation, create_planet_discovery_animation

__all__ = [
    'RocketBoostAnimation',
    'create_rocket_boost_animation',
    'PlanetDiscoveryAnimation',
    'create_planet_discovery_animation',
]