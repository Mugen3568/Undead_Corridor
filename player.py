from settings import *
import pygame as pg
import math
from weapon import *


class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.shot = False
        
        # Stats
        self.max_health = PLAYER_MAX_HEALTH
        self.max_armor = PLAYER_MAX_ARMOR
        self.health = PLAYER_MAX_HEALTH
        self.armor = PLAYER_MAX_ARMOR
        
        # --- ENERGY SYSTEM (replaces Stamina) ---
        self.energy = 0         # Starts empty — charge by killing!
        self.max_energy = PLAYER_MAX_ENERGY
        
        # Register player with game first so weapons can access it
        self.game.player = self
        
        # --- WEAPON INVENTORY (switchable with number keys) ---
        self.weapons = [
            Shotgun(game),
            Rifle(game),
            Handgun(game),
            Katana(game)
        ]
        self.weapon_index = 0
        self.current_weapon = self.weapons[self.weapon_index]
        
        # --- ULTIMATE WEAPON (hidden, only used by Q ability) ---
        self.energy_cannon = EnergyCannon(game)
        
        # --- ULTIMATE STATE ---
        self.ultimate_active = False
        self.previous_weapon_index = 0
        
        self.rel = 0
        self.health_recovery_delay = 700
        self.time_prev = pg.time.get_ticks()
        self.diag_move_corr = 1 / math.sqrt(2)

    # --- ENERGY METHODS ---
    
    def add_energy(self, amount):
        """Called when an enemy dies to charge the ultimate meter"""
        self.energy += amount
        if self.energy > self.max_energy:
            self.energy = self.max_energy

    def fire_ultimate(self):
        """Triggers the massive Energy Cannon AoE blast"""
        if self.energy >= self.max_energy and not self.ultimate_active:
            self.energy = 0  # Drain the bar
            self.ultimate_active = True
            
            # 1. Save current weapon and switch to Energy Cannon
            self.previous_weapon_index = self.weapon_index
            # Reset the old weapon's animation state
            self.current_weapon.frame_counter = 0
            self.current_weapon.reloading = False
            self.current_weapon = self.energy_cannon
            self.current_weapon.frame_counter = 0
            
            # 2. Trigger the firing animation + sound
            self.current_weapon.play_sound()
            self.shot = True
            self.current_weapon.reloading = True
            
            # 3. Deal massive AoE damage in a cone
            self.deal_aoe_damage()
            
            # 4. Flash the screen white
            self.game.object_renderer.screen_flash = 255

    def deal_aoe_damage(self):
        """Hits ALL enemies within a wide cone in front of the player"""
        cannon_damage = WEAPON_DAMAGE.get('energy_cannon', 800)
        for npc in self.game.object_handler.npc_list:
            if npc.alive:
                dx = npc.x - self.x
                dy = npc.y - self.y
                dist = math.hypot(dx, dy)
                
                # If within 15 tiles
                if dist < 15:
                    # Calculate angle to enemy
                    angle_to_npc = math.atan2(dy, dx)
                    # Difference between player aim and NPC angle
                    angle_diff = (angle_to_npc - self.angle + math.pi) % (2 * math.pi) - math.pi
                    
                    # If within a 90-degree cone (-45 to +45 degrees)
                    if abs(angle_diff) < math.radians(45):
                        npc.health -= cannon_damage
                        npc.pain = True
                        npc.check_health()

    # --- EXISTING METHODS ---

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < self.max_health:
            self.health += 1

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over() # Draws the 2 combined images
            pg.display.flip()
            pg.time.delay(1500)       # Wait 1.5 seconds
            self.game.back_to_menu()  # Go back to Menu

    def get_damage(self, damage):
        # --- BABY MODE: Complete invincibility ---
        if getattr(self.game, 'difficulty', 'NORMAL') == 'BABY':
            return
        
        # 50% absorption logic
        if self.armor > 0:
            damage_to_armor = damage * 0.5
            damage_to_health = damage * 0.5
            
            if self.armor >= damage_to_armor:
                self.armor -= damage_to_armor
                self.health -= damage_to_health
            else:
                # Armor breaks
                remaining_damage = damage_to_armor - self.armor
                self.armor = 0
                self.health -= (damage_to_health + remaining_damage)
        else:
            self.health -= damage

        # Clean up numbers
        self.health = int(self.health)
        self.armor = int(self.armor)
        
        # Effects
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def single_fire_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # Block left-click if Energy Cannon is active (ultimate only)
            if self.ultimate_active:
                return
            # Check if left click AND weapon is NOT automatic
            if event.button == 1 and not self.shot and not self.current_weapon.reloading:
                if not self.current_weapon.automatic:
                    self.current_weapon.play_sound()
                    self.shot = True
                    self.current_weapon.reloading = True
        
        # --- ULTIMATE: Listen for Special Ability key ---
        if event.type == pg.KEYDOWN:
            ability_key = self.game.config.controls.get('SPECIAL_ABILITY', pg.K_q)
            if event.key == ability_key:
                self.fire_ultimate()
            
            # --- QA DEBUG CHEATS (Remove before releasing the game!) ---
            if event.key == pg.K_o:
                self.energy = self.max_energy
                print("DEBUG: Energy Maxed!")
            if event.key == pg.K_p:
                for npc in self.game.object_handler.npc_list:
                    if not getattr(npc, 'is_boss', False):
                        npc.health = 0
                        npc.check_health()
                print("DEBUG: Normal mobs cleared!")

    def check_automatic_fire(self):
        # Block auto-fire if Energy Cannon is active
        if self.ultimate_active:
            return
        # Get mouse state
        mouse_pressed = pg.mouse.get_pressed()[0]
        
        # Only fire if mouse held AND weapon IS automatic AND ready to fire
        if mouse_pressed and self.current_weapon.automatic and not self.shot and not self.current_weapon.reloading:
            self.current_weapon.play_sound()
            self.shot = True
            self.current_weapon.reloading = True

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        controls = self.game.config.controls
        num_key_pressed = -1
        if keys[controls['MOVE_FORWARD']]:
            num_key_pressed += 1
            dx += speed_cos
            dy += speed_sin
        if keys[controls['MOVE_BACK']]:
            num_key_pressed += 1
            dx += -speed_cos
            dy += -speed_sin
        if keys[controls['MOVE_LEFT']]:
            num_key_pressed += 1
            dx += speed_sin
            dy += -speed_cos
        if keys[controls['MOVE_RIGHT']]:
            num_key_pressed += 1
            dx += -speed_sin
            dy += speed_cos

        # diag move correction
        if num_key_pressed:
            dx *= self.diag_move_corr
            dy *= self.diag_move_corr

        # --- UPDATED COLLISION CHECK ---
        # Only move X if no NPC collision AND no wall
        if not self.check_npc_collision(dx, 0):
            self.check_wall_collision(dx, 0)
        
        # Only move Y if no NPC collision AND no wall
        if not self.check_npc_collision(0, dy):
            self.check_wall_collision(0, dy)

        # if keys[pg.K_LEFT]:
        #     self.angle -= PLAYER_ROT_SPEED * self.game.delta_time
        # if keys[pg.K_RIGHT]:
        #     self.angle += PLAYER_ROT_SPEED * self.game.delta_time
        self.angle %= math.tau

    def check_npc_collision(self, dx, dy):
        """Check if player collides with any alive NPC"""
        # Calculate where the player WANTS to go
        dest_x = self.x + dx
        dest_y = self.y + dy
        
        # Check against every alive NPC
        for npc in self.game.object_handler.npc_list:
            if npc.alive:
                # Calculate distance to that NPC
                dist = math.hypot(npc.x - dest_x, npc.y - dest_y)
                
                # If distance is less than 0.6 (NPC Size + Player Size buffer)
                if dist < 0.6:
                    return True  # Collision detected! Stop moving.
        return False

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def draw(self):
        pg.draw.line(self.game.screen, 'yellow', (self.x * 100, self.y * 100),
                    (self.x * 100 + WIDTH * math.cos(self.angle),
                     self.y * 100 + WIDTH * math. sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, 'green', (self.x * 100, self.y * 100), 15)

    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    def weapon_control(self):
        """Handle weapon switching with number keys 1-5"""
        # Don't allow weapon switching during ultimate
        if self.ultimate_active:
            return
            
        keys = pg.key.get_pressed()
        new_index = self.weapon_index
        
        if keys[pg.K_1]:
            new_index = 0
        elif keys[pg.K_2]:
            new_index = 1
        elif keys[pg.K_3]:
            new_index = 2
        elif keys[pg.K_4]:
            new_index = 3
            
        # Only switch if the weapon changed
        if new_index != self.weapon_index:
            # Reset old weapon's animation
            self.current_weapon.frame_counter = 0
            self.current_weapon.reloading = False
            self.weapon_index = new_index
            self.game.sound.stop_weapons()  # Stop sounds when switching
            self.current_weapon = self.weapons[self.weapon_index]
            self.current_weapon.frame_counter = 0  # Start fresh
            self.current_weapon.reloading = False
            self.shot = False

    def update(self):
        self.movement()
        self.mouse_control()
        self.recover_health()
        self.weapon_control()  # Check for weapon switch
        self.check_automatic_fire()  # Check for automatic fire
        self.current_weapon.update()  # Update animation of current weapon
        
        # --- ULTIMATE: Auto-swap back after animation finishes ---
        if self.ultimate_active and not self.current_weapon.reloading:
            self.ultimate_active = False
            # Reset cannon's animation state
            self.current_weapon.frame_counter = 0
            self.current_weapon = self.weapons[self.previous_weapon_index]
            self.weapon_index = self.previous_weapon_index
            self.current_weapon.frame_counter = 0  # Start fresh
            self.current_weapon.reloading = False
            self.shot = False

    @property
    def pos(self):
        return self.x, self.y

    @property
    def map_pos(self):
        return int(self.x), int(self.y)