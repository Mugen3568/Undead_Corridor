import pygame as pg
import sys
import math
import random
from settings import *
from resource_helper import resource_path
from ui_system import UIAnimator, SmartButton, Slider
from game_config import GameConfig, RESOLUTIONS

class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.config = game.config
        
        # Menu States
        self.menu_state = 'main'
        
        # Initialize Animator
        self.animator = UIAnimator(game)
        
        # --- Key rebinding state ---
        self.waiting_for_key = None  # Action name when rebinding
        
        # --- Leaderboard state ---
        self.leaderboard_level = 1  # Which level tab is active (1-5)
        
        # Procedural Ambient Background setup (remains static)
        self.loop_duration = 12.0
        self.particles = []
        self.embers = []
        
        # Initialize UI components
        self.setup_ui()

        # --- Menu Music ---
        self.music_path = resource_path('resources/sound/menu_theme.mp3')
        try:
            pg.mixer.music.load(self.music_path)
            pg.mixer.music.set_volume(self.config.menu_volume)
            pg.mixer.music.play(-1)
        except:
            print("Music file not found.")

    def setup_ui(self):
        """Rebuild all resolution-dependent UI elements"""
        # Current screen dimensions
        W, H = self.screen.get_size()
        
        # Scale factors (based on reference 1600x900)
        sf_h = H / 900
        sf_w = W / 1600
        
        # Fonts
        self.title_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(120 * sf_h))
        self.menu_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(60 * sf_h))
        self.small_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(40 * sf_h))
        
        # --- CREATE SMART BUTTONS (Perfect Center Math Plan) ---
        center_x = W // 2
        button_w = int(W * 0.30)  # 30% of screen width
        button_h = int(80 * sf_h)
        wide_button_w = int(button_w * 1.5)
        
        # Vertical stacking constants
        v_start = int(0.40 * H)   # 40% down
        v_gap = int(0.12 * H)     # 12% gap
        
        self.buttons = {
            'main': [
                SmartButton("START OPERATION", center_x, v_start, width=button_w, height=button_h),
                SmartButton("LEADERBOARD", center_x, v_start + v_gap, width=button_w, height=button_h),
                SmartButton("SETTINGS", center_x, v_start + v_gap * 2, width=button_w, height=button_h),
                SmartButton("QUIT", center_x, v_start + v_gap * 3, width=button_w, height=button_h)
            ],
            'difficulty': [
                SmartButton("BABY - I'M AN INSTRUCTOR", center_x, int(0.25 * H), width=int(W * 0.4), height=button_h),
                SmartButton("EASY - I'M TOO YOUNG TO DIE", center_x, int(0.37 * H), width=int(W * 0.4), height=button_h),
                SmartButton("NORMAL - HURT ME PLENTY", center_x, int(0.49 * H), width=int(W * 0.4), height=button_h),
                SmartButton("HARD - NIGHTMARE!", center_x, int(0.61 * H), width=int(W * 0.4), height=button_h),
                SmartButton("BACK", center_x, int(0.77 * H), width=button_w, height=button_h)
            ],
            'level_select': [
                SmartButton("LEVEL 1 - FLESHPITS", center_x, int((0.27 + 0*0.088) * H), width=int(W * 0.4), height=button_h),
                SmartButton("LEVEL 2 - NIHILITY", center_x, int((0.27 + 1*0.088) * H), width=int(W * 0.4), height=button_h),
                SmartButton("LEVEL 3 - MAJULA", center_x, int((0.27 + 2*0.088) * H), width=int(W * 0.4), height=button_h),
                SmartButton("LEVEL 4 - TORMENTED", center_x, int((0.27 + 3*0.088) * H), width=int(W * 0.4), height=button_h),
                SmartButton("LEVEL 5 - ASCENDED", center_x, int((0.27 + 4*0.088) * H), width=int(W * 0.4), height=button_h),
            ],
            'leaderboard': [
                SmartButton("BACK", center_x, int(0.88 * H), width=button_w, height=button_h)
            ],
            'settings': [
                SmartButton("CONTROLS", center_x, int(0.38 * H), width=button_w, height=button_h),
                SmartButton("GRAPHICS", center_x, int(0.5 * H), width=button_w, height=button_h),
                SmartButton("AUDIO", center_x, int(0.61 * H), width=button_w, height=button_h),
                SmartButton("BACK", center_x, int(0.77 * H), width=button_w, height=button_h)
            ],
            'controls': [
                SmartButton("BACK", center_x, int(0.83 * H), width=button_w, height=button_h)
            ],
            'graphics': [
                SmartButton("RESOLUTION", center_x, int(0.38 * H), width=wide_button_w, height=button_h),
                SmartButton("FULLSCREEN", center_x, int(0.51 * H), width=wide_button_w, height=button_h),
                SmartButton("APPLY", center_x, int(0.64 * H), width=button_w, height=button_h),
                SmartButton("BACK", center_x, int(0.77 * H), width=button_w, height=button_h)
            ],
            'audio': [
                SmartButton("BACK", center_x, int(0.83 * H), width=button_w, height=button_h)
            ]
        }
        self.buttons['level_select'].append(SmartButton("BACK", center_x, int(0.83 * H), width=button_w, height=button_h))
        
        # --- Audio Sliders ---
        self.sliders = {
            'menu_vol': Slider(center_x, int(0.38 * H), int(W * 0.35), self.config.menu_volume, 'MENU MUSIC'),
            'game_vol': Slider(center_x, int(0.5 * H), int(W * 0.35), self.config.game_volume, 'GAME MUSIC'),
            'effects_vol': Slider(center_x, int(0.61 * H), int(W * 0.35), self.config.effects_volume, 'EFFECTS'),
        }

        # --- Update Background Particles ---
        self.particles = []
        for i in range(40):
            self.particles.append({
                'x': random.randint(0, W),
                'y': random.randint(0, H),
                'speed': random.uniform(10, 25) * sf_h,
                'size': max(1, int(random.randint(1, 3) * sf_h)),
                'seed': random.uniform(0, 100),
                'color': (255, 50, 50) if random.random() < 0.3 else (180, 160, 140)
            })
            
        # --- BACKGROUND LOAD & RESCALE ---
        try:
            self.bg_image = pg.image.load(resource_path('resources/textures/menu_bg.png')).convert()
            self.bg_image = pg.transform.scale(self.bg_image, (W, H))
        except Exception as e:
            print(f"Error loading menu background: {e}")
            self.bg_image = pg.Surface((W, H))
            self.bg_image.fill((15, 0, 0))

        # --- Menu Music ---
        self.music_path = resource_path('resources/sound/menu_theme.mp3')
        try:
            pg.mixer.music.load(self.music_path)
            pg.mixer.music.set_volume(0.4)
            pg.mixer.music.play(-1)
        except:
            print("Music file not found.")

    def check_events(self):
        mx, my = pg.mouse.get_pos()
        click = False
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.config.save()
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                click = True
            
            # Handle mouse wheel for leaderboard level switching
            if event.type == pg.MOUSEWHEEL and self.menu_state == 'leaderboard':
                self.leaderboard_level -= event.y  # scroll up = prev, down = next
                self.leaderboard_level = max(1, min(5, self.leaderboard_level))
            
            # Handle key rebinding
            if event.type == pg.KEYDOWN and self.waiting_for_key:
                self.config.controls[self.waiting_for_key] = event.key
                self.waiting_for_key = None
                self.config.save()
                continue
            
            # Handle ESC in menus
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if self.menu_state == 'pause':
                    self.game.toggle_pause()
                elif self.menu_state == 'difficulty':
                    self.menu_state = 'main'
                elif self.menu_state == 'level_select':
                    self.menu_state = 'difficulty'
                elif self.menu_state == 'leaderboard':
                    self.menu_state = 'main'
                elif self.menu_state in ('controls', 'graphics', 'audio'):
                    self.menu_state = 'settings'
                elif self.menu_state == 'settings':
                    self.menu_state = 'main'
        
        if self.menu_state != 'pause':
            # Discrete click handling for menus
            if click:
                active_buttons = self.buttons.get(self.menu_state, [])
                button_handled = False
                for btn in active_buttons:
                    if btn.rect.collidepoint(mx, my):
                        self.handle_action(btn.text)
                        button_handled = True
                
                # Special handling for controls rebinding — skip if a button already handled this click
                if self.menu_state == 'controls' and not button_handled:
                    self.check_controls_click(mx, my)
                
                # Handle leaderboard tab clicks
                if self.menu_state == 'leaderboard' and not button_handled:
                    self.check_leaderboard_tab_click(mx, my)
        else:
            # Handle pause menu clicks (old style)
            if click:
                self.check_pause_menu_click(mx, my)

    def handle_action(self, text):
        """Handle button actions based on text"""
        # Main Menu Actions
        if "START" in text or "OPERATION" in text:
            self.menu_state = 'difficulty'
        elif text == "LEADERBOARD":
            self.menu_state = 'leaderboard'
        elif text == "SETTINGS":
            self.menu_state = 'settings'
        elif text == "QUIT":
            self.config.save()
            pg.quit()
            sys.exit()
        elif text == "BACK":
            if self.menu_state == 'level_select':
                self.menu_state = 'difficulty'
            elif self.menu_state in ('controls', 'graphics', 'audio'):
                self.menu_state = 'settings'
            elif self.menu_state == 'settings':
                self.menu_state = 'main'
            else:
                self.menu_state = 'main'
        
        # Settings sub-menu navigation
        elif text == "CONTROLS":
            self.menu_state = 'controls'
        elif text == "GRAPHICS":
            self.menu_state = 'graphics'
        elif text == "AUDIO":
            self.menu_state = 'audio'
        
        # Graphics actions
        elif "RESOLUTION" in text:
            # Cycle resolution
            self.config.resolution_index = (self.config.resolution_index + 1) % len(RESOLUTIONS)
        elif text == "FULLSCREEN":
            self.config.fullscreen = not self.config.fullscreen
        elif text == "APPLY":
            self._apply_graphics()
        
        # Difficulty Actions
        elif "BABY" in text:
            self.game.difficulty = 'BABY'
            self.menu_state = 'level_select'
        elif "EASY" in text:
            self.game.difficulty = 'EASY'
            self.menu_state = 'level_select'
        elif "NORMAL" in text:
            self.game.difficulty = 'NORMAL'
            self.menu_state = 'level_select'
        elif "HARD" in text:
            self.game.difficulty = 'HARD'
            self.menu_state = 'level_select'
        
        # Level Actions
        elif "LEVEL" in text and text.startswith("LEVEL"):
            lvl_idx = int(text.split()[1])
            if lvl_idx in LEVEL_CONFIG:
                self.game.start_game(level_index=lvl_idx)

    def _apply_graphics(self):
        """Apply resolution and fullscreen from config"""
        res = RESOLUTIONS[self.config.resolution_index]
        flags = pg.FULLSCREEN if self.config.fullscreen else 0
        self.game.screen = pg.display.set_mode(res, flags)
        self.screen = self.game.screen
        
        # Dynamic UI Rebuild
        self.setup_ui()
        
        self.config.save()

    def draw(self):
        # Determine what to draw based on state
        if self.menu_state == 'pause':
            self.draw_pause_menu()
        else:
            # Draw procedural ambient background
            self.draw_ambient_background()
            
            # Update Animation Timer
            self.animator.update()
            
            # Draw specific menu
            if self.menu_state == 'main':
                self.draw_main_menu()
            elif self.menu_state == 'difficulty':
                self.draw_difficulty_select()
            elif self.menu_state == 'level_select':
                self.draw_level_select()
            elif self.menu_state == 'leaderboard':
                self.draw_leaderboard()
            elif self.menu_state == 'settings':
                self.draw_settings()
            elif self.menu_state == 'controls':
                self.draw_controls()
            elif self.menu_state == 'graphics':
                self.draw_graphics()
            elif self.menu_state == 'audio':
                self.draw_audio()
            
            # Draw CRT Overlay
            self.animator.draw_scanlines()
            
            # Infernal audio breathing
            self.update_infernal_audio()
        
        pg.display.flip()

    def draw_ambient_background(self):
        """Procedural sine-driven ambient background — infinite seamless loop"""
        W, H = self.screen.get_size()
        t = pg.time.get_ticks() / 1000
        progress = (t % self.loop_duration) / self.loop_duration
        breath = math.sin(progress * 2 * math.pi)

        # Base infernal fill
        self.screen.fill((15, 0, 0))

        # --- Subtle Breathing Overlay ---
        breath_alpha = 20 + breath * 10
        overlay = pg.Surface((W, H))
        overlay.fill((30, 5, 5))
        overlay.set_alpha(int(breath_alpha))
        self.screen.blit(overlay, (0, 0))

        # --- Ambient Light Flicker ---
        flicker = 1 + (
            math.sin(progress * 2 * math.pi * 2) * 0.03 +
            math.sin(progress * 2 * math.pi * 5) * 0.01
        )

        # --- Draw Particles ---
        dt = self.game.delta_time if hasattr(self.game, 'delta_time') else 0.016

        for p in self.particles:
            p['y'] -= p['speed'] * dt
            if p['y'] < 0:
                p['y'] = H
                p['x'] = random.randint(0, W)

            drift = math.sin(t + p['seed']) * 10 * dt
            p['x'] += drift

            color = tuple(min(255, int(c * flicker)) for c in p['color'])
            pg.draw.circle(self.screen, color, (int(p['x']), int(p['y'])), p['size'])

        # --- DRAW BACKGROUND IMAGE ---
        self.screen.blit(self.bg_image, (0, 0))

        # --- EMBER PARTICLE SYSTEM ---
        if random.random() < 0.3:
            # Spawn near the bottom center where the fire is
            x = random.randint(W // 3, (W // 3) * 2)
            y = H + 10
            radius = int(random.randint(2, 5) * (H / 900))
            speed_y = random.uniform(50, 150) * dt * (H / 900)
            speed_x = random.uniform(-50, 50) * dt * (W / 1600)
            alpha = 255
            self.embers.append([x, y, radius, speed_y, speed_x, alpha])

        for ember in self.embers[:]:
            ember[0] += ember[4]
            ember[1] -= ember[3]
            ember[5] -= 120 * dt  # Fade out based on time

            if ember[5] <= 0:
                self.embers.remove(ember)
                continue

            ember_surf = pg.Surface((ember[2] * 2, ember[2] * 2), pg.SRCALPHA)
            # Orange/Yellow fire color
            color = (255, 140, 0, max(0, int(ember[5])))
            pg.draw.circle(ember_surf, color, (ember[2], ember[2]), ember[2])
            self.screen.blit(ember_surf, (ember[0], ember[1]))

        # --- Dark Fog for Depth ---
        fog = pg.Surface((W, H))
        fog.fill((0, 0, 0))
        fog.set_alpha(60)
        self.screen.blit(fog, (0, 0))

    def draw_main_menu(self):
        """Draw main menu — Demonic Hellscape"""
        t = pg.time.get_ticks() / 1000
        pulse = 1 + math.sin(t * 1.5) * 0.03  # subtle breathing

        title_text = 'UNDEAD CORRIDOR'

        W, H = self.screen.get_size()
        half_w = W // 2
        
        main_surface = self.title_font.render(title_text, True, (230, 220, 200))
        main_surface = pg.transform.scale(
            main_surface,
            (int(main_surface.get_width() * pulse),
             int(main_surface.get_height() * pulse))
        )
        main_rect = main_surface.get_rect(center=(half_w, int(0.1 * H)))
        self.screen.blit(main_surface, main_rect)

        # Draw Smart Buttons
        for btn in self.buttons['main']:
            btn.draw(self.screen, self.menu_font)

    def draw_demonic_subtext(self, text, x, y):
        """Flickering infernal subtext"""
        t = pg.time.get_ticks() / 1000
        flicker = abs(math.sin(t * 6)) * 30
        color = (min(255, int(200 + flicker)), 40, 40)
        sub_surface = self.small_font.render(text, True, color)
        rect = sub_surface.get_rect(center=(x, y))
        self.screen.blit(sub_surface, rect)

    def update_infernal_audio(self):
        """Slow breathing volume modulation on menu music"""
        t = pg.time.get_ticks() / 1000
        breath = (math.sin(t * 0.4) + 1) / 2
        music_volume = (self.config.menu_volume * 0.9) + breath * (self.config.menu_volume * 0.1)
        pg.mixer.music.set_volume(music_volume)

    def draw_difficulty_select(self):
        """Draw difficulty selection with animated buttons"""
        W, H = self.screen.get_size()
        half_w = W // 2
        
        # Title
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(90 * (H/900))).render('SELECT DIFFICULTY', True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(half_w, int(0.13 * H)))
        self.screen.blit(title_surface, title_rect)
        
        # Descriptions
        descriptions = [
            "Invincible - Slow Enemies",
            "Enemies: 70% HP - Less Damage",
            "Enemies: 100% HP - Standard",
            "Enemies: 150% HP - High Damage"
        ]
        
        # Draw buttons with descriptions
        desc_font_size = 28
        desc_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), desc_font_size)
        
        for i, btn in enumerate(self.buttons['difficulty']):
            btn.draw(self.screen, self.menu_font)
            
            # Add description below button (except Back button)
            if i < 4:
                desc_text = descriptions[i]
                desc_surface = desc_font.render(desc_text, True, (170, 170, 170))
                
                # Auto-scale if wider than button
                max_width = btn.rect.width - 40
                if desc_surface.get_width() > max_width:
                    scale_ratio = max_width / desc_surface.get_width()
                    new_w = int(desc_surface.get_width() * scale_ratio)
                    new_h = int(desc_surface.get_height() * scale_ratio)
                    desc_surface = pg.transform.smoothscale(desc_surface, (new_w, new_h))
                
                desc_rect = desc_surface.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 20))
                self.screen.blit(desc_surface, desc_rect)

    def draw_level_select(self):
        """Draw level selection with animated buttons"""
        W, H = self.screen.get_size()
        half_w = W // 2
        
        # Title
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(90 * (H/900))).render('SELECT MISSION', True, (255, 50, 50))
        title_rect = title_surface.get_rect(center=(half_w, int(0.11 * H)))
        self.screen.blit(title_surface, title_rect)
        
        # Show current difficulty
        diff_colors = {'BABY': (0, 220, 255), 'EASY': (0, 255, 0), 'NORMAL': (255, 215, 0), 'HARD': (255, 0, 0)}
        diff_color = diff_colors.get(self.game.difficulty, (255, 255, 255))
        diff_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(40 * (H/900)))
        diff_text = diff_font.render(f"DIFFICULTY: {self.game.difficulty}", True, diff_color)
        diff_rect = diff_text.get_rect(center=(half_w, int(0.2 * H)))
        self.screen.blit(diff_text, diff_rect)
        
        # Draw Smart Buttons
        for btn in self.buttons['level_select']:
            btn.draw(self.screen, self.menu_font)

    def draw_leaderboard(self):
        """Scrolling per-level leaderboard with tab navigation"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        level = self.leaderboard_level
        
        level_names = {1: 'FLESHPITS', 2: 'NIHILITY', 3: 'MAJULA', 4: 'TORMENTED', 5: 'ASCENDED'}
        
        # Title
        title_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(70 * sf))
        title_surface = title_font.render('TOP COMMANDERS', True, (255, 215, 0))
        self.screen.blit(title_surface, title_surface.get_rect(center=(half_w, int(0.09 * H))))
        
        # Level tabs (horizontal row)
        tab_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(28 * sf))
        tab_w = int(160 * sf)
        tab_h = int(40 * sf)
        total_tabs_w = tab_w * 5 + 4 * int(10 * sf)
        start_x = half_w - total_tabs_w // 2
        
        for i in range(1, 6):
            tx = start_x + (i - 1) * (tab_w + int(10 * sf))
            ty = int(0.17 * H)
            tab_rect = pg.Rect(tx, ty, tab_w, tab_h)
            
            if i == level:
                pg.draw.rect(self.screen, (120, 0, 0), tab_rect, border_radius=6)
                pg.draw.rect(self.screen, (200, 50, 50), tab_rect, 2, border_radius=6)
                text_color = (255, 255, 255)
            else:
                pg.draw.rect(self.screen, (25, 25, 30), tab_rect, border_radius=6)
                pg.draw.rect(self.screen, (60, 60, 60), tab_rect, 1, border_radius=6)
                text_color = (120, 120, 120)
            
            tab_text = tab_font.render(f"LVL {i}", True, text_color)
            self.screen.blit(tab_text, tab_text.get_rect(center=tab_rect.center))
        
        # Level name subtitle
        subtitle_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(32 * sf))
        subtitle = subtitle_font.render(f"LEVEL {level} - {level_names.get(level, '')}", True, (180, 160, 140))
        self.screen.blit(subtitle, subtitle.get_rect(center=(half_w, int(0.26 * H))))
        
        # Column Headers
        header_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(34 * sf))
        col_left = half_w - int(300 * sf)
        col_mid = half_w - int(80 * sf)
        col_right = half_w + int(180 * sf)
        
        header_y = int(0.32 * H)
        rank_h = header_font.render("RANK", True, (100, 255, 100))
        name_h = header_font.render("NAME", True, (100, 255, 100))
        score_h = header_font.render("SCORE", True, (100, 255, 100))
        self.screen.blit(rank_h, (col_left, header_y))
        self.screen.blit(name_h, (col_mid, header_y))
        self.screen.blit(score_h, (col_right, header_y))
        
        # Divider line
        pg.draw.line(self.screen, (60, 0, 0), (col_left, header_y + int(40 * sf)), (col_right + int(150 * sf), header_y + int(40 * sf)), 1)
        
        # Fetch per-level data
        scores = self.game.db.get_top_scores(level=level)
        row_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(32 * sf))
        
        if not scores:
            empty_text = row_font.render("No scores yet — be the first!", True, (80, 80, 80))
            self.screen.blit(empty_text, empty_text.get_rect(center=(half_w, int(0.5 * H))))
        else:
            for i, (name, score) in enumerate(scores):
                y = int((0.37 + i * 0.048) * H)
                
                # Rank medal colors
                if i == 0:
                    rank_color = (255, 215, 0)  # Gold
                elif i == 1:
                    rank_color = (192, 192, 192)  # Silver
                elif i == 2:
                    rank_color = (205, 127, 50)  # Bronze
                else:
                    rank_color = (160, 160, 160)
                
                self.screen.blit(row_font.render(f"#{i+1}", True, rank_color), (col_left, y))
                self.screen.blit(row_font.render(name, True, (255, 255, 255)), (col_mid, y))
                score_color = (255, 215, 0) if i < 3 else (200, 100, 100)
                self.screen.blit(row_font.render(str(score), True, score_color), (col_right, y))
        
        # Scroll hint
        hint_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(24 * sf))
        hint = hint_font.render("SCROLL MOUSE WHEEL TO SWITCH LEVELS", True, (80, 70, 60))
        self.screen.blit(hint, hint.get_rect(center=(half_w, int(0.84 * H))))
        
        # Back Button
        for btn in self.buttons['leaderboard']:
            btn.draw(self.screen, self.menu_font)

    def check_leaderboard_tab_click(self, mx, my):
        """Handle clicks on the level tabs in the leaderboard"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        
        tab_w = int(160 * sf)
        tab_h = int(40 * sf)
        total_tabs_w = tab_w * 5 + 4 * int(10 * sf)
        start_x = half_w - total_tabs_w // 2
        
        for i in range(1, 6):
            tx = start_x + (i - 1) * (tab_w + int(10 * sf))
            ty = int(0.17 * H)
            tab_rect = pg.Rect(tx, ty, tab_w, tab_h)
            if tab_rect.collidepoint(mx, my):
                self.leaderboard_level = i
                break

    def draw_pause_menu(self):
        """Draw pause menu (old style for compatibility)"""
        W, H = self.screen.get_size()
        half_w = W // 2
        half_h = H // 2
        sf = H / 900
        
        # 1. Create a transparent overlay
        overlay = pg.Surface((W, H))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 2. Draw Title
        title_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(90 * sf))
        title = title_font.render('PAUSED', True, (255, 255, 255))
        self.screen.blit(title, (half_w - title.get_width() // 2, int(0.22 * H)))
        
        # 3. Draw Options
        pause_options = ['Continue', 'Main Menu', 'Quit']
        for i, option in enumerate(pause_options):
            text = self.small_font.render(option, True, 'white')
            rect = text.get_rect(center=(half_w, int((0.44 + i * 0.11) * H)))
            
            # Simple hover effect
            mx, my = pg.mouse.get_pos()
            if rect.collidepoint(mx, my):
                pg.draw.rect(self.screen, (50, 50, 50), rect.inflate(20, 10))
            
            self.screen.blit(text, rect)

    def check_pause_menu_click(self, mx, my):
        """Handle pause menu clicks"""
        W, H = self.screen.get_size()
        half_w = W // 2
        
        # Continue
        if pg.Rect(half_w - 100, int(0.41 * H), 200, 50).collidepoint(mx, my):
            self.game.toggle_pause()
        # Main Menu
        elif pg.Rect(half_w - 150, int(0.52 * H), 300, 50).collidepoint(mx, my):
            self.game.toggle_pause()
            self.game.back_to_menu()
        # Quit
        elif pg.Rect(half_w - 100, int(0.63 * H), 200, 50).collidepoint(mx, my):
            pg.quit()
            sys.exit()

    # ===========================
    # SETTINGS SCREENS
    # ===========================

    def draw_settings(self):
        """Settings hub — CONTROLS / GRAPHICS / AUDIO"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(90 * sf)).render('SETTINGS', True, (230, 220, 200))
        title_rect = title_surface.get_rect(center=(half_w, int(0.13 * H)))
        self.screen.blit(title_surface, title_rect)
        
        for btn in self.buttons['settings']:
            btn.draw(self.screen, self.menu_font)

    def draw_controls(self):
        """Controls rebinding screen"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(80 * sf)).render('CONTROLS', True, (230, 220, 200))
        title_rect = title_surface.get_rect(center=(half_w, int(0.11 * H)))
        self.screen.blit(title_surface, title_rect)
        
        actions = list(self.config.controls.keys())
        label_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), int(36 * sf))
        key_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(36 * sf))
        
        mx, my = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()[0]
        
        for i, action in enumerate(actions):
            y = int((0.24 + i * 0.088) * H)
            row_width = int(600 * sf)
            row_height = int(55 * sf)
            row_rect = pg.Rect(half_w - row_width // 2, y - int(20 * sf), row_width, row_height)
            
            hovered = row_rect.collidepoint(mx, my)
            if hovered:
                pg.draw.rect(self.screen, (40, 0, 0), row_rect, border_radius=6)
            pg.draw.rect(self.screen, (120, 0, 0) if hovered else (60, 0, 0), row_rect, 1, border_radius=6)
            
            # Action name (left)
            display_name = action.replace('_', ' ')
            action_surf = label_font.render(display_name, True, (180, 170, 160))
            self.screen.blit(action_surf, (half_w - int(280 * sf), y - int(5 * sf)))
            
            # Key name (right)
            if self.waiting_for_key == action:
                key_text = '> PRESS KEY <'
                key_color = (255, 40, 40)
            else:
                key_text = pg.key.name(self.config.controls[action]).upper()
                key_color = (230, 220, 200)
            
            key_surf = key_font.render(key_text, True, key_color)
            key_rect = key_surf.get_rect(midright=(half_w + int(280 * sf), y + int(8 * sf)))
            self.screen.blit(key_surf, key_rect)
        
        # Click to rebind moved to check_controls_click for discrete event handling
        
        # Instructions
        if self.waiting_for_key:
            hint = self.small_font.render('Press any key to bind...', True, (255, 40, 40))
        else:
            hint = self.small_font.render('Click a control to rebind', True, (120, 110, 100))
        hint_rect = hint.get_rect(center=(half_w, int(0.75 * H)))
        self.screen.blit(hint, hint_rect)
        
        for btn in self.buttons['controls']:
            btn.draw(self.screen, self.menu_font)

    def check_controls_click(self, mx, my):
        """Handle control rebind clicks using discrete click events"""
        if self.waiting_for_key:
            return
            
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
            
        actions = list(self.config.controls.keys())
        for i, action in enumerate(actions):
            y = int((0.24 + i * 0.088) * H)
            row_width = int(600 * sf)
            row_height = int(55 * sf)
            row_rect = pg.Rect(half_w - row_width // 2, y - int(20 * sf), row_width, row_height)
            if row_rect.collidepoint(mx, my):
                self.waiting_for_key = action
                break

    def draw_graphics(self):
        """Graphics settings screen"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(80 * sf)).render('GRAPHICS', True, (230, 220, 200))
        title_rect = title_surface.get_rect(center=(half_w, int(0.11 * H)))
        self.screen.blit(title_surface, title_rect)
        
        # Update button values dynamically
        res = RESOLUTIONS[self.config.resolution_index]
        self.buttons['graphics'][0].value_text = f"<  {res[0]} x {res[1]}  >"
        self.buttons['graphics'][1].value_text = "ON" if self.config.fullscreen else "OFF"
        
        for btn in self.buttons['graphics']:
            btn.draw(self.screen, self.menu_font)

    def draw_audio(self):
        """Audio settings screen with sliders"""
        W, H = self.screen.get_size()
        half_w = W // 2
        sf = H / 900
        
        title_surface = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Bold.ttf'), int(80 * sf)).render('AUDIO', True, (230, 220, 200))
        title_rect = title_surface.get_rect(center=(half_w, int(0.11 * H)))
        self.screen.blit(title_surface, title_rect)
        
        mx, my = pg.mouse.get_pos()
        mouse_pressed = pg.mouse.get_pressed()[0]
        
        slider_font = pg.font.Font(resource_path('resources/Cinzel/static/Cinzel-Regular.ttf'), 30)
        
        for key, slider in self.sliders.items():
            changed = slider.update((mx, my), mouse_pressed, mouse_pressed)
            slider.draw(self.screen, slider_font)
            
            if changed:
                if key == 'menu_vol':
                    self.config.menu_volume = slider.value
                    pg.mixer.music.set_volume(slider.value)
                elif key == 'game_vol':
                    self.config.game_volume = slider.value
                elif key == 'effects_vol':
                    self.config.effects_volume = slider.value
                self.config.save()
        
        for btn in self.buttons['audio']:
            btn.draw(self.screen, self.menu_font)
