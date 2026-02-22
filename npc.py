from sprite_object import *
from random import randint, random
from settings import NPC_STATS, DIFFICULTY_SCALING
from resource_helper import resource_path


class NPC(AnimatedSprite):
    def __init__(self, game, path=None, pos=(10.5, 5.5),
                 scale=0.8, shift=0.15, animation_time=180,
                 health=None, attack_dist=None, speed=None, damage=None):
        # CHANGED: scale 0.6 -> 0.8 (Bigger), shift 0.38 -> 0.15 (Higher on screen)
        if path is None:
            path = resource_path('resources/sprites/npc/soldier/0.png')
        super().__init__(game, path, pos, scale, shift, animation_time)
        # --- FIX: Manually save scale for health bar calculations ---
        self.scale = scale
        
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.pain_images = self.get_images(self.path + '/pain')
        self.walk_images = self.get_images(self.path + '/walk')

        # --- NEW: Extract NPC name from path ---
        # e.g., 'resources/sprites/npc/zombie_axe/0.png' -> 'zombie_axe'
        self.npc_name = path.split('/')[-2]
        
        # --- Get Base Stats from settings.py ---
        stats = NPC_STATS.get(self.npc_name, {'hp': 100, 'dmg': 10, 'speed': 0.03, 'attack_dist': 1.0})
        
        # --- Apply Difficulty Multiplier ---
        difficulty = getattr(game, 'difficulty', 'NORMAL')
        diff_mult = DIFFICULTY_SCALING.get(difficulty, DIFFICULTY_SCALING['NORMAL'])
        
        # Use explicit overrides if provided, otherwise use NPC_STATS
        base_health = health if health is not None else stats['hp']
        base_damage = damage if damage is not None else stats['dmg']
        self.health = int(base_health * diff_mult['health'])
        self.max_health = self.health
        self.attack_damage = int(base_damage * diff_mult['damage'])
        
        # Speed and attack distance - use overrides or NPC_STATS (constant across difficulties)
        self.attack_dist = attack_dist if attack_dist is not None else stats.get('attack_dist', randint(3, 6))
        self.speed = speed if speed is not None else stats.get('speed', 0.03)
        self.size = 20
        
        # --- SMART AI: Reaction time (how often NPC re-evaluates pathfinding) ---
        self.reaction_ms = diff_mult.get('reaction_ms', 300)
        self.last_think_time = 0
        
        self.accuracy = 0.15
        self.alive = True
        self.pain = False
        self.ray_cast_value = False
        self.frame_counter = 0
        self.player_search_trigger = False
        self.pain_timer = 0  # Cooldown for pain sound (prevents spam)
        self.is_boss = False  # NEW: Flag for bosses
        self.name = "Enemy"  # NEW: Enemy name for display
        self.score_value = 100  # Default score for killing this enemy
        
        # --- NEW VARIABLES FOR CLEANUP ---
        self.decay_start_time = 0
        self.should_be_removed = False

    def update(self):
        self.check_animation_time()
        self.get_sprite()
        self.run_logic()
        # self.draw_ray_cast()
        
        # --- NEW: Disappear Logic ---
        # Check if death animation finished and wait time has passed
        if not self.alive and self.decay_start_time > 0:
            if pg.time.get_ticks() - self.decay_start_time > 2000:  # 2000ms = 2 seconds
                self.should_be_removed = True

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        if self.check_wall(int(self.x + dx * self.size), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * self.size)):
            self.y += dy

    def movement(self):
        next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.player.map_pos)
        next_x, next_y = next_pos

        # pg.draw.rect(self.game.screen, 'blue', (100 * next_x, 100 * next_y, 100, 100))
        if next_pos not in self.game.object_handler.npc_positions:
            angle = math.atan2(next_y + 0.5 - self.y, next_x + 0.5 - self.x)
            dx = math.cos(angle) * self.speed
            dy = math.sin(angle) * self.speed
            self.check_wall_collision(dx, dy)

    def attack(self):
        if self.animation_trigger:
            self.game.sound.npc_shot.play()
            if random() < self.accuracy:
                self.game.player.get_damage(self.attack_damage)

    def animate_death(self):
        if not self.alive:
            # If we have death images and animation is not finished
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1
            
            # --- NEW: Check if animation just finished ---
            elif self.frame_counter == len(self.death_images) - 1:
                # Animation is done. Start the decay timer if not started yet.
                if self.decay_start_time == 0:
                    self.decay_start_time = pg.time.get_ticks()

    def animate_pain(self):
        self.animate(self.pain_images)
        if self.animation_trigger:
            self.pain = False

    def check_hit_in_npc(self):
        # 1. Check if Raycast hit the NPC (NPC is visible)
        # 2. Check if Player actually fired
        if self.ray_cast_value and self.game.player.shot:
            
            # 3. Check aiming: Is the player looking roughly at the center of the sprite?
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                
                # Get the weapon the player is currently holding
                current_weapon = self.game.player.current_weapon
                
                # 4. Check Range: Is the enemy close enough for this specific weapon?
                if self.dist < current_weapon.max_dist:
                    
                    # --- FIX: PAIN SOUND COOLDOWN (500ms) ---
                    # Only play pain sound once per 500ms (prevents spam from machine guns)
                    now = pg.time.get_ticks()
                    if now - self.pain_timer > 500:
                        self.game.sound.npc_pain.play()
                        self.pain_timer = now  # Reset timer
                    
                    self.game.player.shot = False  # Prevent single shot from hitting multiple frames
                    self.pain = True
                    self.health -= current_weapon.damage  # Use specific weapon damage
                    self.check_health()

    def check_health(self):
        if self.health < 1:
            if self.alive:  # Only trigger this ONCE when they die
                self.alive = False
                self.game.sound.npc_death.play()
                # --- FIX 1: Reset animation to start of death sequence ---
                self.frame_counter = 0
                # --- FIX 2: Check if death images exist to prevent crash ---
                if len(self.death_images) == 0:
                    print(f"WARNING: No death images for {self.path}")
                    # Force removal if no animation exists
                    self.decay_start_time = pg.time.get_ticks()
                
                # --- ENERGY REWARD: Charge the player's ultimate ---
                energy_reward = 50 if self.is_boss else 10
                self.game.player.add_energy(energy_reward)

    def run_logic(self):
        if self.alive:
            self.ray_cast_value = self.ray_cast_player_npc()
            self.check_hit_in_npc()

            if self.pain:
                self.animate_pain()

            elif self.ray_cast_value:
                self.player_search_trigger = True

                if self.dist < self.attack_dist:
                    self.animate(self.attack_images)
                    self.attack()
                else:
                    self.animate(self.walk_images)
                    # --- SMART AI: Only move if reaction timer allows ---
                    now = pg.time.get_ticks()
                    if now - self.last_think_time >= self.reaction_ms:
                        self.last_think_time = now
                        self.movement()

            elif self.player_search_trigger:
                self.animate(self.walk_images)
                # --- SMART AI: Reaction-gated movement ---
                now = pg.time.get_ticks()
                if now - self.last_think_time >= self.reaction_ms:
                    self.last_think_time = now
                    self.movement()

            else:
                self.animate(self.idle_images)
        else:
            self.animate_death()

    @property
    def map_pos(self):
        return int(self.x), int(self.y)

    def ray_cast_player_npc(self):
        if self.game.player.map_pos == self.map_pos:
            return True

        wall_dist_v, wall_dist_h = 0, 0
        player_dist_v, player_dist_h = 0, 0

        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        ray_angle = self.theta

        # --- FIX: Prevent division by zero ---
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)
        
        # Epsilon prevents ZeroDivisionError when angle is perfectly horizontal
        if abs(sin_a) < 0.00001:
            sin_a = 0.00001
        if abs(cos_a) < 0.00001:
            cos_a = 0.00001

        # horizontals
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        for i in range(MAX_DEPTH):
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor == self.map_pos:
                player_dist_h = depth_hor
                break
            if tile_hor in self.game.map.world_map:
                wall_dist_h = depth_hor
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth

        # verticals
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert == self.map_pos:
                player_dist_v = depth_vert
                break
            if tile_vert in self.game.map.world_map:
                wall_dist_v = depth_vert
                break
            x_vert += dx
            y_vert += dy
            depth_vert += delta_depth

        player_dist = max(player_dist_v, player_dist_h)
        wall_dist = max(wall_dist_v, wall_dist_h)

        if 0 < player_dist < wall_dist or not wall_dist:
            return True
        return False

    def draw_ray_cast(self):
        pg.draw.circle(self.game.screen, 'red', (100 * self.x, 100 * self.y), 15)
        if self.ray_cast_player_npc():
            pg.draw.line(self.game.screen, 'orange', (100 * self.game.player.x, 100 * self.game.player.y),
                         (100 * self.x, 100 * self.y), 2)


# --- BASE ENEMY TYPES ---

class MeleeEnemy(NPC):
    def __init__(self, game, path, pos, scale=0.8, shift=0.15, animation_time=180,
                 health=None, attack_dist=None, speed=None, damage=None):
        super().__init__(game, path, pos, scale, shift, animation_time,
                         health=health, attack_dist=attack_dist, speed=speed, damage=damage)
        self.score_value = 100


class RangedEnemy(NPC):
    def __init__(self, game, path, pos, scale=0.8, shift=0.15, animation_time=180,
                 health=None, attack_dist=None, speed=None, damage=None):
        super().__init__(game, path, pos, scale, shift, animation_time,
                         health=health, attack_dist=attack_dist, speed=speed, damage=damage)
        self.score_value = 300


class LungeEnemy(NPC):
    """Enemy that doubles speed when within lunge range of the player."""
    def __init__(self, game, path, pos, scale=0.8, shift=0.15, animation_time=180,
                 health=None, attack_dist=None, speed=None, damage=None):
        super().__init__(game, path, pos, scale, shift, animation_time,
                         health=health, attack_dist=attack_dist, speed=speed, damage=damage)
        self.base_speed = self.speed
        self.lunge_range = 4.5
        self.score_value = 200

    def movement(self):
        # Double speed when within lunge range
        if hasattr(self, 'dist') and self.dist < self.lunge_range:
            self.speed = self.base_speed * 2
        else:
            self.speed = self.base_speed
        super().movement()


class AoeEnemy(NPC):
    """Enemy with AoE ground slam attack that hits players within range."""
    def __init__(self, game, path, pos, scale=0.8, shift=0.15, animation_time=180,
                 health=None, attack_dist=None, speed=None, damage=None):
        super().__init__(game, path, pos, scale, shift, animation_time,
                         health=health, attack_dist=attack_dist, speed=speed, damage=damage)
        self.aoe_range = 3.0  # Reduced from 4.5 so players can outrange it
        self.score_value = 500
        self.last_attack_time = 0
        self.attack_cooldown = 3000  # 3 seconds between slams

    def attack(self):
        """AoE ground slam - damages player if within range, with cooldown."""
        if self.animation_trigger:
            now = pg.time.get_ticks()
            if now - self.last_attack_time >= self.attack_cooldown:
                self.game.sound.npc_shot.play()
                if self.dist < self.aoe_range:
                    self.game.player.get_damage(self.attack_damage)
                self.last_attack_time = now


# --- MELEE ENEMIES ---

class ZombieAxe(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/zombie_axe/0.png'), pos)
        self.name = "Zombie (Axe)"


class Tormented(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Tormented/0.png'), pos=pos,
                         health=NPC_STATS['Tormented']['hp'], attack_dist=NPC_STATS['Tormented']['attack_dist'],
                         speed=NPC_STATS['Tormented']['speed'], damage=NPC_STATS['Tormented']['dmg'])
        self.name = "Tormented"


class UndeadWarrior(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/undead_warrior/0.png'), pos)
        self.name = "Undead Warrior"


class Frogman(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/Frogman/0.png'), pos)
        self.name = "Frogman"


class ImpDoom(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/imp_doom/0.png'), pos)
        self.name = "Imp"


class Abomination(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Abomination/0.png'), pos=pos,
                         health=NPC_STATS['Abomination']['hp'], attack_dist=NPC_STATS['Abomination']['attack_dist'],
                         speed=NPC_STATS['Abomination']['speed'], damage=NPC_STATS['Abomination']['dmg'])
        self.name = "Abomination"
        self.score_value = 300


# --- RANGED / SHOOTER ENEMIES ---

class DoomZombie(RangedEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/doom_zombie/0.png'), pos)
        self.name = "Doom Zombie"


class DoomZombieSRG(RangedEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/doom_zombie(srg)/0.png'), pos)
        self.name = "Doom Zombie (SRG)"


class SpiderMutant(RangedEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/spider_mutant/0.png'), pos)
        self.name = "Spider Mutant"


class CyberDemonMob(RangedEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/cyber_demon/0.png'), pos, scale=1.1, shift=0.1)
        self.name = "Cyber Demon"
        self.score_value = 500


class Toadman(RangedEnemy):
    """Former boss, now a regular ranged (shooter) enemy."""
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/Toadman/0.png'), pos, scale=1.0, shift=0.2)
        self.name = "Toad King"
        self.score_value = 400


# --- LUNGE ENEMIES (speed doubles when close) ---

class Crawler(LungeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Crawler/0.png'), pos=pos,
                         health=NPC_STATS['Crawler']['hp'], attack_dist=NPC_STATS['Crawler']['attack_dist'],
                         speed=NPC_STATS['Crawler']['speed'], damage=NPC_STATS['Crawler']['dmg'])
        self.name = "Crawler"


class LordOfFlies(LungeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Lord of flies/0.png'), pos=pos,
                         health=NPC_STATS['Lord of flies']['hp'], attack_dist=NPC_STATS['Lord of flies']['attack_dist'],
                         speed=NPC_STATS['Lord of flies']['speed'], damage=NPC_STATS['Lord of flies']['dmg'])
        self.name = "Lord of Flies"
        self.score_value = 400


# --- AOE ENEMY ---

class Creature(AoeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Creature/0.png'), pos=pos,
                         health=NPC_STATS['Creature']['hp'], attack_dist=NPC_STATS['Creature']['attack_dist'],
                         speed=NPC_STATS['Creature']['speed'], damage=NPC_STATS['Creature']['dmg'])
        self.name = "Creature"


# --- HEAVY MELEE BOSS ---

class CrowMauler(MeleeEnemy):
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, path=resource_path('resources/sprites/npc/Crow mauler/0.png'), pos=pos,
                         health=NPC_STATS['Crow mauler']['hp'], attack_dist=NPC_STATS['Crow mauler']['attack_dist'],
                         speed=NPC_STATS['Crow mauler']['speed'], damage=NPC_STATS['Crow mauler']['dmg'])
        self.name = "Crow Mauler"
        self.score_value = 500


# --- FORMER BOSSES (now regular enemies; spawn_boss sets is_boss flag) ---

class Grell(MeleeEnemy):
    """Former boss, now a regular melee enemy."""
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/grell/0.png'), pos, scale=0.9, shift=0.3)
        self.name = "Grell"
        self.score_value = 400


class DemonDog(MeleeEnemy):
    """Former boss, now a regular melee enemy."""
    def __init__(self, game, pos=(10.5, 5.5)):
        super().__init__(game, resource_path('resources/sprites/npc/Demon_dog/0.png'), pos, scale=1.3, shift=0.05)
        self.name = "Demon Dog"
        self.score_value = 400



















