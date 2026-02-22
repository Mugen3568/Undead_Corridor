import pygame as pg
import sys
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from resource_helper import resource_path
from menu import Menu
from database import Database
from game_config import GameConfig

class Game:
    def __init__(self):
        pg.init()
        # We need the mouse visible in the menu
        pg.mouse.set_visible(True) 
        self.screen = pg.display.set_mode(RES)
        pg.display.set_caption('Undead Corridor')
        icon = pg.image.load(resource_path('resources/textures/icon.png'))
        pg.display.set_icon(icon)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        
        # Initialize Database and Score
        self.db = Database()  # Connect to SQLite database
        self.player_score = 0  # Current run score
        
        # Initialize Difficulty
        self.difficulty = 'NORMAL'  # Default difficulty (EASY, NORMAL, HARD)
        
        # Initialize Config (must be before Menu)
        self.config = GameConfig()
        
        # Initialize Menu
        self.menu = Menu(self)
        self.in_menu = True  # Start in menu
        self.paused = False  # New: Track pause state
        
        # We don't create game objects yet, wait for 'Play'
        
    def start_game(self, level_index=0):
        # This function is called by the Menu when a level is selected
        self.in_menu = False
        pg.mouse.set_visible(False) # Hide mouse for gameplay
        pg.event.set_grab(True)     # Lock mouse to window
        
        # Stop menu music before starting game
        pg.mixer.music.stop()
        
        self.new_game(level_index)

    def toggle_pause(self):
        """Toggle pause state and freeze/unfreeze game logic"""
        self.paused = not self.paused
        if self.paused:
            # Capture the frozen frame (Freeze once, don't re-render 3D world)
            self.pause_bg = self.screen.copy()
            
            self.menu.menu_state = 'pause'
            pg.mouse.set_visible(True)
            pg.event.set_grab(False)
            pg.mixer.pause()  # Pause game sounds
        else:
            self.menu.menu_state = 'main'  # Reset menu state
            pg.mouse.set_visible(False)
            pg.event.set_grab(True)
            pg.mixer.unpause()  # Resume sounds

    def new_game(self, level_index=1):
        # Initialize victory flag and score
        self.victory = False
        self.player_score = 0  # Reset score on new game
        self.level_id = level_index  # Save level ID for leaderboard
        
        # 1. Create Map first
        self.map = Map(self)
        
        # 2. Create Player
        self.player = Player(self)
        
        # 3. Position player at map center (Safe - both exist now)
        self.player.x = self.map.center_x + 0.5
        self.player.y = self.map.center_y + 0.5
        
        # 4. Initialize Renderer and Raycasting
        self.object_renderer = ObjectRenderer(self, level_id=level_index)
        self.raycasting = RayCasting(self)
        
        # 5. Create Pathfinding (Must happen AFTER map is generated)
        self.pathfinding = PathFinding(self)
        self.pathfinding.get_graph()  # Ensure graph is built
        
        # 6. Create Object Handler (Spawns enemies AFTER pathfinding is ready)
        # UPDATED: Pass level_id to ObjectHandler
        self.object_handler = ObjectHandler(self, level_id=level_index)
        
        # 7. Create Starting Weapon
        self.weapon = Shotgun(self)
        
        # 8. Audio
        self.sound = Sound(self)
        pg.mixer.music.play(-1)

    def update(self):
        if self.paused:
            return  # Don't update if paused
        
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        
        # --- NEW: Check Victory Condition ---
        if self.object_handler.check_win_condition() and not self.victory:
            self.victory = True
            # Show victory screen briefly
            self.object_renderer.draw_victory()
            pg.display.flip()
            pg.time.delay(2000)  # Wait 2 seconds
            # Ask for player name
            self.show_name_input()
            # Go to leaderboard
            self.menu.menu_state = 'leaderboard'
            self.back_to_menu()
        
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')
        
        # Reset the shot flag at the VERY END of the frame so NPCs can register the hit
        self.player.shot = False

    def draw(self):
        # 1. Draw 3D View & HUD
        self.object_renderer.draw()
        
        # 2. Draw Weapon
        self.player.current_weapon.draw()
        
        # 3. Draw Mini-Map
        self.map.draw()
        
        # 4. Draw Victory Screen if level cleared
        if getattr(self, 'victory', False):
            self.object_renderer.draw_victory()
        
        # 5. Update Display
        pg.display.flip()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            
            # Toggle Pause with ESC (or return to menu if victory)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if getattr(self, 'victory', False):
                    # Return to menu on ESC during victory
                    self.back_to_menu()
                else:
                    # Toggle pause normally
                    self.toggle_pause()
                
            # If NOT paused, handle shooting
            if not self.paused:
                if event.type == self.global_event:
                    self.global_trigger = True
                self.player.single_fire_event(event)
            else:
                # If paused, let the menu handle clicks
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.menu.check_pause_menu_click(*pg.mouse.get_pos())

    def show_name_input(self):
        """ Centered name input screen with empty-name protection and ESC to skip """
        user_text = ""
        input_active = True
        W, H = self.screen.get_size()
        half_w, half_h = W // 2, H // 2
        sf = H / 900
        
        title_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(70 * sf))
        score_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(50 * sf))
        input_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(46 * sf))
        hint_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(30 * sf))
        
        while input_active:
            self.screen.fill((5, 5, 10))
            
            # Score display (gold, centered)
            score_text = score_font.render(f"SCORE: {self.player_score}", True, (255, 215, 0))
            self.screen.blit(score_text, score_text.get_rect(center=(half_w, half_h - int(160 * sf))))
            
            # Title
            title = title_font.render("ENTER YOUR NAME", True, (230, 220, 200))
            self.screen.blit(title, title.get_rect(center=(half_w, half_h - int(80 * sf))))
            
            # Input box
            box_w, box_h = int(500 * sf), int(60 * sf)
            box_rect = pg.Rect(half_w - box_w // 2, half_h - box_h // 2, box_w, box_h)
            pg.draw.rect(self.screen, (30, 30, 40), box_rect, border_radius=8)
            pg.draw.rect(self.screen, (120, 0, 0), box_rect, 2, border_radius=8)
            
            # User text (centered in box)
            display_text = user_text
            if pg.time.get_ticks() % 1000 < 500:
                display_text += "|"
            text_surf = input_font.render(display_text, True, (0, 255, 0))
            self.screen.blit(text_surf, text_surf.get_rect(center=box_rect.center))
            
            # Submit hint (green if valid, gray if empty)
            has_valid_name = len(user_text.strip()) > 0
            submit_color = (100, 255, 100) if has_valid_name else (80, 80, 80)
            submit_hint = hint_font.render("PRESS ENTER TO SUBMIT", True, submit_color)
            self.screen.blit(submit_hint, submit_hint.get_rect(center=(half_w, half_h + int(60 * sf))))
            
            # Skip hint
            skip_hint = hint_font.render("PRESS ESC TO SKIP", True, (120, 40, 40))
            self.screen.blit(skip_hint, skip_hint.get_rect(center=(half_w, half_h + int(110 * sf))))
            
            pg.display.flip()
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        input_active = False  # Skip without saving
                    elif event.key == pg.K_RETURN:
                        if len(user_text.strip()) > 0:
                            self.db.add_score(user_text.strip(), self.player_score, self.level_id)
                        input_active = False
                    elif event.key == pg.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        if len(user_text) < 15:
                            user_text += event.unicode

    def back_to_menu(self):
        # Stop all active Sound Effects (guns, screams)
        pg.mixer.stop()
        
        # This function returns to the menu (called after game over or win)
        self.in_menu = True
        self.menu.menu_state = 'main'
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        
        # Restart menu music
        pg.mixer.music.load(resource_path('resources/sound/menu_theme.mp3'))
        pg.mixer.music.set_volume(self.config.menu_volume)
        pg.mixer.music.play(-1)

    def run(self):
        while True:
            if self.in_menu:
                # MAIN MENU LOOP
                self.menu.check_events()
                self.menu.draw()
            else:
                # GAMEPLAY LOOP
                if self.paused:
                    # PAUSE LOOP (Fixed: No flickering)
                    # 1. Draw the frozen background we captured
                    self.screen.blit(self.pause_bg, (0, 0))
                    
                    # 2. Draw the menu overlay on top
                    self.menu.draw_pause_menu()
                    
                    # 3. Handle pause menu clicks
                    self.check_events()
                    
                    # 4. Flip display ONCE
                    pg.display.flip()
                    self.clock.tick(FPS)
                else:
                    # NORMAL GAMEPLAY
                    self.check_events()
                    self.update()  # Updates movement, AI, physics
                    self.draw()

if __name__ == '__main__':
    game = Game()
    game.run()