import pygame as pg
from settings import *
from resource_helper import resource_path
import math
import time

class Pickup(pg.sprite.Sprite):
    def __init__(self, game, pos, p_type='health'):
        self.game = game
        self.type = p_type  # 'health' or 'armor'
        
        # Position
        self.x, self.y = pos
        self.pos = pos
        
        # Load sprite
        self.load_image(p_type)
        
        # Properties
        self.scale = 0.5
        self.height_shift = 0.5  # Fixed height on the floor
        
        # Billboard logic
        self.image_width = self.image.get_width()
        self.image_half_height = self.image.get_height() // 2
        self.image_half_width = self.image_width // 2
        self.image_ratio = self.image_width / self.image.get_height()
        self.dx, self.dy, self.theta, self.screen_x, self.dist, self.norm_dist = 0, 0, 0, 0, 1, 1
        self.sprite_half_width = 0
        
        # State
        self.collected = False
    
    def load_image(self, p_type):
        """Load static sprite image for pickup"""
        self.image_path = resource_path(f'resources/sprites/static_sprites/{p_type}.png')
        try:
            self.image = pg.image.load(self.image_path).convert_alpha()
        except:
            # Fallback if image missing
            self.image = pg.Surface((50, 50))
            if p_type == 'health':
                self.image.fill((255, 0, 0))  # Red for health
            else:
                self.image.fill((0, 100, 255))  # Blue for armor
    
    def update(self):
        if not self.collected:
            self.get_sprite()
            self.check_collision()

    def check_collision(self):
        """Check if player is close enough to pick up"""
        px, py = self.game.player.pos
        if math.hypot(self.x - px, self.y - py) < 0.6:  # Close enough to touch
            self.apply_effect()
            self.collected = True

    def apply_effect(self):
        """Apply the pickup effect to the player"""
        if self.type == 'health':
            # Add 30 health, don't exceed max
            old_health = self.game.player.health
            self.game.player.health = min(self.game.player.health + 30, self.game.player.max_health)
            if self.game.player.health > old_health:
                print(f"Picked up Health! (+{int(self.game.player.health - old_health)})")
            
        elif self.type == 'armor':
            # Add 50 armor, don't exceed max
            old_armor = self.game.player.armor
            self.game.player.armor = min(self.game.player.armor + 50, self.game.player.max_armor)
            if self.game.player.armor > old_armor:
                print(f"Picked up Armor! (+{int(self.game.player.armor - old_armor)})")

    def get_sprite(self):
        """Billboard rendering - same logic as static sprites"""
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        delta = self.theta - self.game.player.angle
        if (dx > 0 and self.game.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta += math.tau

        delta_rays = delta / DELTA_ANGLE
        self.screen_x = (HALF_NUM_RAYS + delta_rays) * SCALE

        self.dist = math.hypot(dx, dy)
        self.norm_dist = self.dist * math.cos(delta)
        
        if -self.image_half_width < self.screen_x < (WIDTH + self.image_half_width) and self.norm_dist > 0.5:
            self.get_sprite_projection()

    def get_sprite_projection(self):
        """Project the sprite onto the screen"""
        proj = SCREEN_DIST / self.norm_dist * self.scale
        proj_width, proj_height = proj * self.image_ratio, proj

        image = pg.transform.scale(self.image, (int(proj_width), int(proj_height)))
        
        self.sprite_half_width = proj_width // 2
        height_shift = proj_height * self.height_shift
        pos = (self.screen_x - self.sprite_half_width, HALF_HEIGHT - proj_height // 2 + height_shift)

        self.game.raycasting.objects_to_render.append((self.norm_dist, image, pos))

