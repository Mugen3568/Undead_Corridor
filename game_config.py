import json
import os
import pygame as pg
from resource_helper import get_persistent_path

CONFIG_FILE = get_persistent_path('config.json')

DEFAULT_CONTROLS = {
    'MOVE_FORWARD': pg.K_w,
    'MOVE_BACK': pg.K_s,
    'MOVE_LEFT': pg.K_a,
    'MOVE_RIGHT': pg.K_d,
    'SHOOT': pg.K_SPACE,
    'SPECIAL_ABILITY': pg.K_q,
}

RESOLUTIONS = [
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]

DEFAULT_CONFIG = {
    'controls': {k: v for k, v in DEFAULT_CONTROLS.items()},
    'resolution_index': 1,  # 1600x900
    'fullscreen': False,
    'menu_volume': 0.4,
    'game_volume': 0.6,
    'effects_volume': 0.7,
    'mouse_sensitivity': 0.0003,
}


class GameConfig:
    def __init__(self):
        self.controls = dict(DEFAULT_CONTROLS)
        self.resolution_index = DEFAULT_CONFIG['resolution_index']
        self.fullscreen = DEFAULT_CONFIG['fullscreen']
        self.menu_volume = DEFAULT_CONFIG['menu_volume']
        self.game_volume = DEFAULT_CONFIG['game_volume']
        self.effects_volume = DEFAULT_CONFIG['effects_volume']
        self.mouse_sensitivity = DEFAULT_CONFIG['mouse_sensitivity']
        self.load()

    def load(self):
        """Load config from JSON file if it exists"""
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            # Controls (stored as key codes)
            if 'controls' in data:
                for action, keycode in data['controls'].items():
                    if action in self.controls:
                        self.controls[action] = keycode
            # Graphics
            if 'resolution_index' in data:
                idx = data['resolution_index']
                if 0 <= idx < len(RESOLUTIONS):
                    self.resolution_index = idx
            if 'fullscreen' in data:
                self.fullscreen = bool(data['fullscreen'])
            # Audio
            if 'menu_volume' in data:
                self.menu_volume = max(0.0, min(1.0, float(data['menu_volume'])))
            if 'game_volume' in data:
                self.game_volume = max(0.0, min(1.0, float(data['game_volume'])))
            if 'effects_volume' in data:
                self.effects_volume = max(0.0, min(1.0, float(data['effects_volume'])))
            if 'mouse_sensitivity' in data:
                self.mouse_sensitivity = max(0.0001, min(0.001, float(data['mouse_sensitivity'])))
        except Exception as e:
            print(f"Config load error: {e}")

    def save(self):
        """Save current config to JSON file"""
        data = {
            'controls': self.controls,
            'resolution_index': self.resolution_index,
            'fullscreen': self.fullscreen,
            'menu_volume': self.menu_volume,
            'game_volume': self.game_volume,
            'effects_volume': self.effects_volume,
            'mouse_sensitivity': self.mouse_sensitivity,
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")

    @property
    def resolution(self):
        return RESOLUTIONS[self.resolution_index]
