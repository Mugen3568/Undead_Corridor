import pygame as pg
import os
import math
from settings import *
from resource_helper import resource_path

class ObjectRenderer:
    def __init__(self, game, level_id=1):
        self.game = game
        self.screen = game.screen
        
        # --- SAFETY CHECK ---
        # If level_id is 0 or invalid, force it to 1 to prevent crash
        if level_id < 1:
            level_id = 1
        
        self.level_id = level_id
        self.base_path = resource_path(f'resources/levels/{level_id}/')
        print(f"--- LOADING LEVEL {level_id} ASSETS FROM: {self.base_path} ---")
        
        # --- NEW: Damage Flash Effect ---
        self.damage_alpha = 0  # Transparency of red flash (0 = invisible)
        
        # 1. Load Walls
        self.wall_textures = self.load_wall_textures()
        
        # 2. Load Sky (Strict path checking)
        sky_path = self.base_path + 'sky.png'
        if os.path.exists(sky_path):
            print(f"✓ Loading Custom Sky: {sky_path}")
            self.sky_image = self.get_texture(sky_path, (WIDTH, HALF_HEIGHT))
        else:
            print(f"⚠ WARNING: Custom Sky not found at {sky_path}. Using Default.")
            self.sky_image = self.get_texture(resource_path('resources/textures/sky.png'), (WIDTH, HALF_HEIGHT))
        
        # 3. Load Floor (Strict path checking)
        floor_path = self.base_path + 'floor.png'
        if os.path.exists(floor_path):
            print(f"✓ Loading Custom Floor: {floor_path}")
            self.floor_image = self.get_texture(floor_path, (WIDTH, HALF_HEIGHT))
        else:
            print(f"⚠ WARNING: Custom Floor not found at {floor_path}. Using solid gray.")
            self.floor_image = pg.Surface((WIDTH, HALF_HEIGHT))
            self.floor_image.fill((30, 30, 30))
        
        self.sky_offset = 0
        self.blood_screen = self.get_texture(resource_path('resources/textures/blood_screen.png'), RES)
        
        # --- ICONS ---
        # The game looks for these 3 files. If not found, it draws a white square.
        self.icon_size = 35
        self.icons = {}
        for name in ['health', 'armor', 'energy']:
            try:
                # Load the specific icon file (energy reuses stamina_icon.png)
                icon_file = 'stamina_icon.png' if name == 'energy' else f'{name}_icon.png'
                img = pg.image.load(resource_path(f'resources/HUD/{icon_file}')).convert_alpha()
                self.icons[name] = pg.transform.scale(img, (self.icon_size, self.icon_size))
            except FileNotFoundError:
                print(f"MISSING ICON: {resource_path(f'resources/HUD/{icon_file}')}")
                # Fallback: White square if file is missing
                s = pg.Surface((self.icon_size, self.icon_size))
                s.fill('white') 
                self.icons[name] = s
        
        # Screen flash for ultimate
        self.screen_flash = 0

        # Digits for drawing numbers
        self.digit_size = 30 
        self.digit_images = [self.get_texture(resource_path(f'resources/textures/digits/{i}.png'), [self.digit_size] * 2)
                             for i in range(11)]
        self.digits = dict(zip(map(str, range(11)), self.digit_images))
        
        # Game Over / Win Screens
        self.game_over_image_1 = self.get_texture(resource_path('resources/textures/game_over_1.png'), RES)
        self.game_over_image_2 = self.get_texture(resource_path('resources/textures/game_over_2.png'), RES)
        self.win_image = self.get_texture(resource_path('resources/textures/win.png'), RES)

    def draw_player_hud(self):
        player = self.game.player
        
        # Define where the groups start (Top Left Corner area)
        start_x = 40
        start_y = 30
        gap = 200 # Space between groups

        # 1. Health Group (Left)
        self.draw_stat_group(
            value=player.health, max_val=player.max_health, 
            icon=self.icons['health'], color=HEALTH_BAR_COLOR,
            x=start_x, y=start_y
        )

        # 2. Armor Group (Middle)
        self.draw_stat_group(
            value=player.armor, max_val=player.max_armor, 
            icon=self.icons['armor'], color=ARMOR_BAR_COLOR,
            x=start_x + gap, y=start_y
        )

        # 3. Energy Group (Right) — replaces Stamina
        self.draw_stat_group(
            value=player.energy, max_val=player.max_energy, 
            icon=self.icons['energy'], color=ENERGY_BAR_COLOR,
            x=start_x + gap * 2, y=start_y
        )

    def draw_stat_group(self, value, max_val, icon, color, x, y):
        # A. Draw Icon
        self.screen.blit(icon, (x, y))

        # B. Draw Number (Right next to icon)
        self.draw_number(value, x + 45, y)

        # C. Draw Bar (Below icon and number)
        bar_width = 100
        bar_height = 10
        bar_x = x
        bar_y = y + 40 # Position below the icon

        # Background (Dark Gray)
        pg.draw.rect(self.screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        
        # Colored Part
        ratio = max(0, min(1, value / max_val))
        curr_width = int(bar_width * ratio)
        if curr_width > 0:
            pg.draw.rect(self.screen, color, (bar_x, bar_y, curr_width, bar_height))
        
        # Border (Optional, White outline)
        pg.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

    def draw_number(self, value, x, y):
        value = max(0, value) 
        s_value = str(value)
        for i, char in enumerate(s_value):
            self.screen.blit(self.digits[char], (x + i * self.digit_size, y))

    def draw(self):
        self.draw_background()
        self.render_game_objects()
        self.draw_boss_health_bars()  # NEW: Draw boss bars on top
        self.draw_player_hud()
        
        # --- NEW: Draw Score ---
        self.draw_score()
        
        # --- NEW: Draw Damage Flash ---
        self.draw_damage_overlay()
        
        # --- ULTIMATE PROMPT & FLASH ---
        self.draw_ultimate_prompt()
        self.draw_screen_flash()
        
        self.draw_crosshair()

    def draw_background(self):
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, 0))
        self.screen.blit(self.floor_image, (0, HALF_HEIGHT))

    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse=True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(resource_path(path)).convert_alpha()
        return pg.transform.scale(texture, res)

    def load_wall_textures(self):
        """Load wall textures from level-specific folder"""
        walls_path = self.base_path + 'walls/'
        textures = {}
        for i in range(1, 6):
            file_path = walls_path + f'{i}.png'
            try:
                textures[i] = self.get_texture(file_path)
            except FileNotFoundError:
                print(f"WARNING: Missing wall texture {file_path}. Using fallback gray texture.")
                # Create a gray fallback surface
                fallback = pg.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
                fallback.fill((50, 50, 50))
                textures[i] = fallback
        return textures

    def win(self):
        self.screen.blit(self.win_image, (0, 0))

    def game_over(self):
        self.screen.blit(self.game_over_image_1, (0, 0))
        self.screen.blit(self.game_over_image_2, (0, 0))

    def player_damage(self):
        self.screen.blit(self.blood_screen, (0, 0))
        # Trigger damage flash
        self.damage_alpha = 255  # Full red flash

    def draw_score(self):
        """ Draws the live score in the top-left corner """
        # Get score from game, default to 0 if not set
        score = getattr(self.game, 'player_score', 0)
        
        # Format: "SCORE: 001200" (6 digits, padded with zeros)
        score_text = f'SCORE: {score:06d}'
        
        # Use a smaller font for the score (40pt instead of 80pt)
        font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), 40)
        
        # Render Text (White with Black Outline for readability)
        # 1. Draw Black Shadow/Outline
        shadow_surf = font.render(score_text, True, (0, 0, 0))
        self.screen.blit(shadow_surf, (22, 102))  # Offset by 2px
        
        # 2. Draw Gold Text (Classic arcade color)
        text_surf = font.render(score_text, True, (255, 215, 0))
        self.screen.blit(text_surf, (20, 100))

    def draw_damage_overlay(self):
        """Draw red flash when player takes damage"""
        # If there is a flash active
        if self.damage_alpha > 0:
            # Reduce alpha (Fade out)
            self.damage_alpha -= 10  # Speed of fade
            if self.damage_alpha < 0:
                self.damage_alpha = 0
            
            # Create red surface
            damage_surf = pg.Surface((WIDTH, HEIGHT))
            damage_surf.fill((255, 0, 0))
            damage_surf.set_alpha(int(self.damage_alpha))
            
            # Draw using 'ADD' blend mode for a glowing effect
            self.screen.blit(damage_surf, (0, 0), special_flags=pg.BLEND_ADD)

    def draw_ultimate_prompt(self):
        """Show flashing 'ULTIMATE READY - PRESS [Q]' when energy is full"""
        player = self.game.player
        if player.energy >= player.max_energy:
            # Pulsing alpha for flash effect
            alpha = int(abs(math.sin(pg.time.get_ticks() / 200.0)) * 255)
            
            screen_w = self.game.screen.get_width()
            screen_h = self.game.screen.get_height()
            
            ready_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), 40)
            ready_text = ready_font.render('ULTIMATE READY - PRESS [Q]', True, (0, 255, 255))
            ready_text.set_alpha(alpha)
            
            text_rect = ready_text.get_rect(center=(screen_w // 2, screen_h - 150))
            self.game.screen.blit(ready_text, text_rect)

    def draw_screen_flash(self):
        """Decaying white flash triggered by the ultimate ability"""
        if self.screen_flash > 0:
            screen_w = self.game.screen.get_width()
            screen_h = self.game.screen.get_height()
            
            flash_surf = pg.Surface((screen_w, screen_h))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(int(self.screen_flash))
            self.game.screen.blit(flash_surf, (0, 0))
            self.screen_flash -= 15  # Fade out quickly
            if self.screen_flash < 0:
                self.screen_flash = 0

    def draw_crosshair(self):
        # Draw a small white circle in the exact center of the screen
        pg.draw.circle(self.screen, 'white', (HALF_WIDTH, HALF_HEIGHT), 3)

    def draw_victory(self):
        """Draw LEVEL CLEARED victory screen over win.png"""
        # Draw win.png as fullscreen background
        self.screen.blit(self.win_image, (0, 0))
        
        # Draw "LEVEL CLEARED" text in green
        font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), 100)
        text = font.render('LEVEL CLEARED', True, (0, 255, 0))
        rect = text.get_rect(center=(HALF_WIDTH, HALF_HEIGHT - 50))
        self.screen.blit(text, rect)
        
        # Draw subtext instruction
        font_s = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), 50)
        sub = font_s.render('Press ESC to Return to Menu', True, 'white')
        rect_s = sub.get_rect(center=(HALF_WIDTH, HALF_HEIGHT + 80))
        self.screen.blit(sub, rect_s)

    def draw_boss_health_bars(self):
        """Draw floating health bars above bosses"""
        for npc in self.game.object_handler.npc_list:
            if npc.is_boss and npc.alive:
                # Only draw if the boss is visible (ray_cast_value checks visibility)
                if npc.ray_cast_value:
                    bar_w = 100
                    bar_h = 10
                    
                    # Calculate screen position (top of sprite)
                    screen_x = npc.screen_x
                    # --- FIX: Changed 'npc.depth' to 'npc.norm_dist' ---
                    proj_height = (SCREEN_DIST / (npc.norm_dist + 0.0001)) * npc.scale
                    top_of_sprite_y = HALF_HEIGHT - proj_height // 2
                    
                    x = screen_x - bar_w // 2
                    y = top_of_sprite_y - 20  # 20 pixels above the sprite
                    
                    # Only draw if on screen
                    if 0 < x < WIDTH:
                        # Background (black)
                        pg.draw.rect(self.screen, (0, 0, 0), (x, y, bar_w, bar_h))
                        
                        # Health bar (red)
                        ratio = max(0, min(1, npc.health / npc.max_health))
                        pg.draw.rect(self.screen, (255, 0, 0), (x, y, bar_w * ratio, bar_h))
                        
                        # Border (white)
                        pg.draw.rect(self.screen, (255, 255, 255), (x, y, bar_w, bar_h), 1)