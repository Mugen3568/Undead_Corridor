import math

# game settings
RES = WIDTH, HEIGHT = 1600, 900
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 0

PLAYER_POS = 1.5, 5
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 60

# --- PLAYER STATS ---
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_ARMOR = 50      # Armor is 50% of Health
PLAYER_MAX_ENERGY = 100

PLAYER_RECOVERY_DELAY = 700

# --- MOUSE ---
MOUSE_SENSITIVITY = 0.0003
MOUSE_MAX_REL = 40
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - MOUSE_BORDER_LEFT

# --- COLORS ---
FLOOR_COLOR = (30, 30, 30)
HEALTH_BAR_COLOR = (200, 0, 0)   # Red
ARMOR_BAR_COLOR = (0, 0, 200)    # Blue
ENERGY_BAR_COLOR = (0, 220, 255)  # Cyan

# --- RAYCASTING ---
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20
SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

TEXTURE_SIZE = 256
HALF_TEXTURE_SIZE = TEXTURE_SIZE // 2

# --- PROCEDURAL MAP SETTINGS ---
rows = 30  # Size of the map (Y axis)
cols = 30  # Size of the map (X axis)

# --- MINIMAP SETTINGS ---
MINIMAP_SCALE = 5  # How many pixels per map tile
MINIMAP_RES = (cols * MINIMAP_SCALE, rows * MINIMAP_SCALE)
MINIMAP_POS = (WIDTH - MINIMAP_RES[0] - 10, 10)  # Top Right, with 10px padding
MINIMAP_WALL_COLOR = (100, 100, 100)
MINIMAP_PLAYER_COLOR = (0, 255, 0)

# --- LEVEL CONFIGURATION ---
# boss is now a LIST to support multiple bosses per level
LEVEL_CONFIG = {
    1: {
        'map_size': (30, 30),
        'enemies': ['Abomination', 'Crawler', 'Tormented', 'undead_warrior'],
        'boss': ['Creature'],
        'enemy_count': 15,
        'boss_hp': 1000
    },
    2: {
        'map_size': (35, 35),
        'enemies': ['grell', 'doom_zombie', 'zombie_axe'],
        'boss': ['Demon_dog'],
        'enemy_count': 20,
        'boss_hp': 1500
    },
    3: {
        'map_size': (40, 40),
        'enemies': ['imp_doom', 'Demon_dog', 'doom_zombie(srg)'],
        'boss': ['cyber_demon'],
        'enemy_count': 25,
        'boss_hp': 1200
    },
    4: {
        'map_size': (45, 45),
        'enemies': ['Toadman', 'Frogman', 'Crawler', 'spider_mutant'],
        'boss': ['Crow mauler', 'Lord of flies'],
        'enemy_count': 20,
        'boss_hp': 2000
    },
    5: {
        'map_size': (50, 50),
        'enemies': ['Abomination', 'Tormented', 'cyber_demon', 'grell',
                    'doom_zombie(srg)', 'Crawler'],
        'boss': ['Creature', 'Lord of flies', 'Crow mauler'],
        'enemy_count': 40,
        'boss_hp': 3000
    }
}

# --- PLAYER WEAPON DAMAGE ---
WEAPON_DAMAGE = {
    'knife': 25,       # 2 hits to kill a zombie
    'pistol': 20,      # 3 hits to kill a zombie
    'shotgun': 150,    # 1 shot kills weak enemies (if all pellets hit)
    'rifle': 25,       # High damage automatic
    'minigun': 20,     # Shreds everything
    'katana': 50,      # Powerful melee
    'handgun': 20,     # Same as pistol
    'energy_cannon': 800  # Ultimate AoE blast
}

# --- ENEMY BASE STATS ---
# Keys: hp, dmg, speed, attack_dist
# hp/dmg are for 'NORMAL' difficulty (scaled by DIFFICULTY_SCALING).
NPC_STATS = {
    # --- Melee Enemies ---
    'zombie_axe':       {'hp': 50,   'dmg': 10,  'speed': 0.03,  'attack_dist': 1.0},
    'Tormented':        {'hp': 60,   'dmg': 12,  'speed': 0.03,  'attack_dist': 1.0},
    'undead_warrior':   {'hp': 100,  'dmg': 15,  'speed': 0.03,  'attack_dist': 1.0},
    'Frogman':          {'hp': 120,  'dmg': 15,  'speed': 0.045, 'attack_dist': 1.0},
    'imp_doom':         {'hp': 100,  'dmg': 20,  'speed': 0.03,  'attack_dist': 1.0},

    # --- Mid-Range ---
    'spider_mutant':    {'hp': 90,   'dmg': 15,  'speed': 0.025, 'attack_dist': 4.5},

    # --- Lunge Enemies (speed doubles when close) ---
    'Crawler':          {'hp': 70,   'dmg': 10,  'speed': 0.05,  'attack_dist': 1.0},
    'Lord of flies':    {'hp': 180,  'dmg': 22,  'speed': 0.04,  'attack_dist': 1.0},

    # --- Ranged / Shooters ---
    'doom_zombie':      {'hp': 50,   'dmg': 8,   'speed': 0.025, 'attack_dist': 6.0},
    'doom_zombie(srg)': {'hp': 70,   'dmg': 15,  'speed': 0.025, 'attack_dist': 6.0},
    'cyber_demon':      {'hp': 400,  'dmg': 35,  'speed': 0.025, 'attack_dist': 5.0},
    'Toadman':          {'hp': 200,  'dmg': 20,  'speed': 0.02,  'attack_dist': 6.0},

    # --- Former Bosses (now regular enemies; HP overridden when spawned as boss) ---
    'Abomination':      {'hp': 200,  'dmg': 20,  'speed': 0.04,  'attack_dist': 1.5},
    'grell':            {'hp': 180,  'dmg': 18,  'speed': 0.07,  'attack_dist': 1.5},
    'Demon_dog':        {'hp': 250,  'dmg': 30,  'speed': 0.05,  'attack_dist': 2.0},

    # --- AoE Enemy ---
    'Creature':         {'hp': 300,  'dmg': 25,  'speed': 0.03,  'attack_dist': 4.5},

    # --- Heavy Melee Boss ---
    'Crow mauler':      {'hp': 150,  'dmg': 25,  'speed': 0.035, 'attack_dist': 1.5},
}

# --- DIFFICULTY MULTIPLIERS ---
# We scale Health significantly, but Damage only slightly.
DIFFICULTY_SCALING = {
    'BABY':   {'health': 0.5, 'damage': 0.0, 'reaction_ms': 800, 'safe_dist': 12},
    'EASY':   {'health': 0.7, 'damage': 0.8, 'reaction_ms': 600, 'safe_dist': 10},
    'NORMAL': {'health': 1.0, 'damage': 1.0, 'reaction_ms': 300, 'safe_dist': 8},
    'HARD':   {'health': 1.5, 'damage': 1.2, 'reaction_ms': 100, 'safe_dist': 6},
}