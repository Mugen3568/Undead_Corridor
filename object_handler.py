from sprite_object import *
from npc import *
from pickup import Pickup
from settings import LEVEL_CONFIG
from random import choices, randrange, choice
from resource_helper import resource_path
import math


class ObjectHandler:
    def __init__(self, game, level_id=1):
        self.game = game
        self.sprite_list = []
        self.npc_list = []
        self.pickup_list = []  # Track pickups
        self.npc_sprite_path = resource_path('resources/sprites/npc/')
        self.static_sprite_path = resource_path('resources/sprites/static_sprites/')
        self.anim_sprite_path = resource_path('resources/sprites/animated_sprites/')
        add_sprite = self.add_sprite
        add_npc = self.add_npc
        self.npc_positions = {}
        
        # Get level configuration
        data = LEVEL_CONFIG.get(level_id, LEVEL_CONFIG[1])
        self.level_config = data  # Store for spawn_boss
        self.allowed_enemies = data['enemies']
        self.max_enemies = data['enemy_count']
        self.boss_names = data.get('boss', [])  # Now a LIST
        self.boss_hp = data.get('boss_hp', 1000)
        
        # Enemy class mapping
        self.enemy_types = {
            'zombie_axe': ZombieAxe,
            'Tormented': Tormented,
            'doom_zombie': DoomZombie,
            'Crawler': Crawler,
            'undead_warrior': UndeadWarrior,
            'Frogman': Frogman,
            'imp_doom': ImpDoom,
            'spider_mutant': SpiderMutant,
            'Creature': Creature,
            'doom_zombie(srg)': DoomZombieSRG,
            'Crow mauler': CrowMauler,
            'Lord of flies': LordOfFlies,
            'cyber_demon': CyberDemonMob,
            'Abomination': Abomination,
            'Toadman': Toadman,
            'grell': Grell,
            'Demon_dog': DemonDog,
        }

        # spawn npc
        self.spawn_enemies()
        self.spawn_boss()
        
        # spawn pickups
        self.spawn_pickups()
        
        # New: Spawn rare easter egg sprites in hidden corners
        self.spawn_easter_eggs()

    def spawn_easter_eggs(self):
        """Finds dead-ends in the map and places rare decorative sprites there."""
        dead_ends = []
        floor_tiles = self.game.map.floor_tiles
        world_map = self.game.map.world_map
        
        for x, y in floor_tiles:
            # A dead end or corner is a floor tile with 3 or more adjacent walls
            neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            wall_count = sum(1 for nx, ny in neighbors if (nx, ny) in world_map)
            
            if wall_count >= 3:
                # Filter for seclusion: must be at least 15 units away from player spawn
                dist_to_spawn = math.hypot(x - self.game.map.center_x, y - self.game.map.center_y)
                if dist_to_spawn > 15:
                    dead_ends.append((x + 0.5, y + 0.5))
        
        # Select 3 random dead ends for easter eggs (if any found)
        if dead_ends:
            num_eggs = min(3, len(dead_ends))
            egg_spots = choices(dead_ends, k=num_eggs)
            
            for spot in egg_spots:
                # 50% chance for candelabra, 50% for colored light
                if choice([True, False]):
                    self.add_sprite(SpriteObject(self.game, path=resource_path('resources/sprites/static_sprites/candlebra.png'), pos=spot))
                else:
                    light_color = choice(['green_light', 'red_light'])
                    self.add_sprite(SpriteObject(self.game, path=resource_path(f'resources/sprites/animated_sprites/{light_color}/0.png'), pos=spot))
            
            print(f"Placed {num_eggs} hidden easter egg sprites in the map corners. Find them if you can! 🦇")

        # npc map
        # add_npc(SoldierNPC(game, pos=(11.0, 19.0)))
        # add_npc(SoldierNPC(game, pos=(11.5, 4.5)))
        # add_npc(SoldierNPC(game, pos=(13.5, 6.5)))
        # add_npc(SoldierNPC(game, pos=(2.0, 20.0)))
        # add_npc(SoldierNPC(game, pos=(4.0, 29.0)))
        # add_npc(CacoDemonNPC(game, pos=(5.5, 14.5)))
        # add_npc(CacoDemonNPC(game, pos=(5.5, 16.5)))
        # add_npc(CyberDemonNPC(game, pos=(14.5, 25.5)))

    def spawn_boss(self):
        """Spawn bosses at the FARTHEST points from the player in the dungeon."""
        boss_names = self.boss_names
        boss_hp = self.boss_hp
        
        # Calculate distance from player start for every floor tile
        player_x, player_y = self.game.player.x, self.game.player.y
        floor_tiles = []
        for x in range(self.game.map.cols):
            for y in range(self.game.map.rows):
                if (x, y) not in self.game.map.world_map:
                    dist = math.hypot(x - player_x, y - player_y)
                    floor_tiles.append((dist, x, y))
        
        # Sort by distance descending — farthest tiles first
        floor_tiles.sort(reverse=True)
        
        tile_idx = 0
        for boss_name in boss_names:
            if boss_name in self.enemy_types:
                boss_class = self.enemy_types[boss_name]
                spawned = False
                
                # Walk through farthest tiles until we find a valid one
                while not spawned and tile_idx < len(floor_tiles):
                    dist, x, y = floor_tiles[tile_idx]
                    tile_idx += 1
                    
                    boss = boss_class(self.game, pos=(x + 0.5, y + 0.5))
                    boss.health = boss_hp
                    boss.max_health = boss_hp
                    boss.is_boss = True
                    self.npc_list.append(boss)
                    spawned = True
                    print(f"Boss '{boss_name}' spawned at ({x},{y}) — {dist:.0f} tiles from player")

    def spawn_enemies(self):
        """Spawn enemies for the current level"""
        attempts = 0
        spawned = 0
        max_attempts = 2000
        # --- SAFE ROOM: Use difficulty-scaled safe distance ---
        from settings import DIFFICULTY_SCALING
        difficulty = getattr(self.game, 'difficulty', 'NORMAL')
        diff_cfg = DIFFICULTY_SCALING.get(difficulty, DIFFICULTY_SCALING['NORMAL'])
        safe_distance = diff_cfg.get('safe_dist', 8)
        
        while spawned < self.max_enemies and attempts < max_attempts:
            attempts += 1
            x = randrange(self.game.map.cols)
            y = randrange(self.game.map.rows)
            pos = (x, y)
            
            # Check if it's a wall
            if pos in self.game.map.world_map:
                continue
            
            # Check safe zone
            player_x, player_y = int(self.game.player.x), int(self.game.player.y)
            dist = math.hypot(x - player_x, y - player_y)
            
            if dist > safe_distance:
                enemy_name = choice(self.allowed_enemies)
                if enemy_name in self.enemy_types:
                    self.add_npc(self.enemy_types[enemy_name](self.game, pos=(x + 0.5, y + 0.5)))
                    spawned += 1

    def spawn_pickups(self):
        """Spawn health and armor pickups randomly around the map"""
        # Adjust count based on level difficulty
        count = 10 + (self.max_enemies // 3)  # More pickups for harder levels
        
        attempts = 0
        spawned = 0
        max_attempts = 2000
        safe_distance = 5  # Don't spawn too close to player
        
        while spawned < count and attempts < max_attempts:
            attempts += 1
            x = randrange(self.game.map.cols)
            y = randrange(self.game.map.rows)
            pos = (x, y)
            
            # Check if it's a wall
            if pos in self.game.map.world_map:
                continue
            
            # Check safe zone from player
            player_x, player_y = int(self.game.player.x), int(self.game.player.y)
            dist = math.hypot(x - player_x, y - player_y)
            
            if dist > safe_distance:
                # 60% health, 40% armor distribution
                p_type = choice(['health', 'health', 'health', 'armor', 'armor'])
                pickup = Pickup(self.game, (x + 0.5, y + 0.5), p_type)
                self.pickup_list.append(pickup)
                spawned += 1
        
        print(f"Spawned {spawned} pickups ({count} requested)")

    def check_win(self):
        if not len(self.npc_positions):
            self.game.object_renderer.win() # Draws the win image
            pg.display.flip()
            pg.time.delay(1500)       # Wait 1.5 seconds
            self.game.back_to_menu()  # Go back to Menu

    def check_win_condition(self):
        """Check if all enemies are dead (Level Cleared)"""
        alive_count = 0
        for npc in self.npc_list:
            if npc.alive:
                alive_count += 1
        
        if alive_count == 0:
            return True
        return False

    def update(self):
        self.npc_positions = {npc.map_pos for npc in self.npc_list if npc.alive}
        [sprite.update() for sprite in self.sprite_list]
        
        # Update NPCs and award points for kills
        for npc in self.npc_list:
            npc.update()
            
            # --- NEW: Award points when enemy just died ---
            # Check if they are dead but haven't awarded points yet
            if not npc.alive and not getattr(npc, 'score_awarded', False):
                self.game.player_score += npc.score_value
                npc.score_awarded = True  # Flag to prevent double counting
        
        # --- NEW: Remove enemies that have fully decayed ---
        # We rebuild the list, keeping only those who are NOT marked for removal
        self.npc_list = [npc for npc in self.npc_list if not npc.should_be_removed]
        
        # --- NEW: Update pickups and remove collected ones ---
        for pickup in self.pickup_list:
            pickup.update()
        self.pickup_list = [p for p in self.pickup_list if not p.collected]
        
        self.check_win()

    def add_npc(self, npc):
        self.npc_list.append(npc)

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)