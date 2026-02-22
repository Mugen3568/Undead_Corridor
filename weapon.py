from sprite_object import *
from settings import WEAPON_DAMAGE
from resource_helper import resource_path

class Weapon(AnimatedSprite):
    def __init__(self, game, path=None, scale=0.4, animation_time=90):
        if path is None:
            path = resource_path('resources/sprites/weapon/shotgun/0.png')
        super().__init__(game=game, path=path, scale=scale, animation_time=animation_time)
        # Rescale images
        self.images = deque(
            [pg.transform.smoothscale(img, (self.image.get_width() * scale, self.image.get_height() * scale))
             for img in self.images])
        
        # Default positioning (Center)
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2, HEIGHT - self.images[0].get_height())
        
        self.reloading = False
        self.num_images = len(self.images)
        self.frame_counter = 0
        self.name = ''  # Child classes set this for draw positioning
        
        # --- Extract weapon name and get damage from settings ---
        weapon_name = path.split('/')[-2]
        self.damage = WEAPON_DAMAGE.get(weapon_name, 10)
        
        # Other Stats
        self.max_dist = 20
        self.automatic = False

    def animate_shot(self):
        if self.reloading:
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.num_images:
                    self.reloading = False
                    self.frame_counter = 0

    def draw(self):
        image = self.images[0]
        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        
        # Dynamically scale weapon to ~70% of screen height
        scale_ratio = (screen_h * 0.7) / image.get_height()
        new_w = int(image.get_width() * scale_ratio)
        new_h = int(image.get_height() * scale_ratio)
        scaled_img = pg.transform.scale(image, (new_w, new_h))
        
        # Pin flush to bottom
        weapon_y = screen_h - new_h
        
        # Shotgun & Rifle -> bottom-right, everything else -> bottom-center
        if self.name in ('shotgun', 'rifle'):
            weapon_x = screen_w - new_w
        else:
            # If the centered weapon is narrower than the screen, stretch it
            # so the arm cutoffs are pushed flush against the screen edges
            if new_w < screen_w:
                scale_w = screen_w / image.get_width()
                new_w = screen_w
                new_h = int(image.get_height() * scale_w)
                scaled_img = pg.transform.scale(image, (new_w, new_h))
                # Push down so forearms spill off the bottom of the screen
                # Increase 0.35 to push lower, decrease to push higher
                weapon_y = int(screen_h * 0.25)
            weapon_x = (screen_w // 2) - (new_w // 2)
        
        self.game.screen.blit(scaled_img, (weapon_x, weapon_y))

    def update(self):
        self.check_animation_time()
        self.animate_shot()
        
    def play_sound(self):
        pass

# --- SPECIFIC WEAPONS ---

class Shotgun(Weapon):
    def __init__(self, game):
        super().__init__(game, path=resource_path('resources/sprites/weapon/shotgun/0.png'), scale=0.6, animation_time=90)
        self.name = 'shotgun'
        self.max_dist = 15
        self.automatic = False

    def play_sound(self):
        self.game.sound.shotgun.play()

class Rifle(Weapon):
    def __init__(self, game):
        super().__init__(game, path=resource_path('resources/sprites/weapon/rifle/0.png'), scale=0.5, animation_time=90)
        self.name = 'rifle'
        self.max_dist = 25
        self.automatic = True
        # Static position pinned to bottom-right (same level as shotgun)
        self.weapon_pos = (WIDTH - self.images[0].get_width(), HEIGHT - self.images[0].get_height())

    def draw(self):
        # Use static rendering pinned to bottom-right (no dynamic scaling)
        self.game.screen.blit(self.images[0], self.weapon_pos)

    def play_sound(self):
        self.game.sound.rifle.play()

class EnergyCannon(Weapon):
    def __init__(self, game):
        super().__init__(game, path=resource_path('resources/sprites/weapon/energy_cannon/0.png'), scale=0.5, animation_time=60)
        self.name = 'energy_cannon'
        self.max_dist = 15
        self.automatic = False

    def play_sound(self):
        self.game.sound.energy_cannon.play()

class Handgun(Weapon):
    def __init__(self, game):
        super().__init__(game, path=resource_path('resources/sprites/weapon/handgun/0.png'), scale=1.2, animation_time=90)
        self.name = 'handgun'
        self.max_dist = 18
        self.automatic = False

    def play_sound(self):
        self.game.sound.handgun.play()
        
class Katana(Weapon):
    def __init__(self, game):
        super().__init__(game, path=resource_path('resources/sprites/weapon/katana/0.png'), scale=0.9, animation_time=60)
        self.name = 'katana'
        self.max_dist = 2.5
        self.automatic = False
        # Original static positioning
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2, HEIGHT - self.images[0].get_height() + 15)

    def draw(self):
        # Use original static rendering (no dynamic scaling)
        self.game.screen.blit(self.images[0], self.weapon_pos)

    def play_sound(self):
        # REMOVED 'maxtime' so the sound plays fully
        self.game.sound.katana.play()