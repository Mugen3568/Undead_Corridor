import pygame as pg
import math
from random import randint, choice
from settings import *

# --- THEME COLORS (DEMONIC HELLSCAPE) ---
BLOOD_RED = (180, 0, 0)
HELLFIRE = (255, 40, 40)
BONE_WHITE = (230, 220, 200)
BONE_DIM = (150, 140, 130)
DARK_ABYSS = (15, 0, 0)

class UIAnimator:
    def __init__(self, app):
        self.app = app
        self.time = 0
        
        # Pre-make scanline surface for performance
        self.scanline_surf = pg.Surface(app.screen.get_size()).convert_alpha()
        self.scanline_surf.fill((0, 0, 0, 0))
        for y in range(0, app.screen.get_height(), 4):
            pg.draw.line(self.scanline_surf, (0, 0, 0, 50), (0, y), (app.screen.get_width(), y))

    def update(self):
        self.time += 0.1

    def draw_scanlines(self):
        """ Draws a CRT monitor effect overlay """
        self.app.screen.blit(self.scanline_surf, (0, 0))

    def draw_glitch_text(self, text, x, y, size=100, color=HELLFIRE):
        """ Renders text with a jittery holographic glitch effect """
        font = pg.font.Font(None, size)
        
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        
        if randint(0, 100) < 10:
            r_surf = font.render(text, True, (255, 0, 0))
            self.app.screen.blit(r_surf, (rect.x + randint(-5, 5), rect.y))
            b_surf = font.render(text, True, (0, 255, 255))
            self.app.screen.blit(b_surf, (rect.x + randint(-5, 5), rect.y))
        else:
            self.app.screen.blit(surf, rect)

    def draw_pulsing_text(self, text, x, y, size=40, color=HELLFIRE):
        """ Text that fades in and out using Sine wave """
        alpha = (math.sin(self.time) + 1) / 2 * 255
        
        font = pg.font.Font(None, size)
        surf = font.render(text, True, color)
        surf.set_alpha(int(alpha))
        
        rect = surf.get_rect(center=(x, y))
        self.app.screen.blit(surf, rect)

class SmartButton:
    def __init__(self, text, x, y, width=300, height=80, value_text=None):
        self.text = text
        self.value_text = value_text
        self.base_width = width
        self.base_x = x
        self.base_y = y
        self.rect = pg.Rect(0, 0, width, height)
        self.rect.center = (x, y)
        
        # Animation State
        self.hover_progress = 0  # 0.0 to 1.0
        self.is_hovered = False
        self.current_width = float(width)

    def draw(self, screen, font):
        mx, my = pg.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mx, my)

        # Smooth Animation (Lerp)
        target = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * 0.15
        
        # Smooth width expansion
        target_w = self.base_width + 40 if self.is_hovered else self.base_width
        self.current_width += (target_w - self.current_width) * 0.15
        
        # Subtle vertical lift on hover
        lift = int(2 * self.hover_progress)
        
        # Update rect
        self.rect.width = int(self.current_width)
        self.rect.centerx = self.base_x
        self.rect.centery = self.base_y - lift
        
        # --- Difficulty color coding ---
        if 'BABY' in self.text or 'INSTRUCTOR' in self.text:
            accent = (0, 220, 255)
        elif 'EASY' in self.text:
            accent = (0, 180, 0)
        elif 'NORMAL' in self.text:
            accent = (200, 140, 0)
        elif 'HARD' in self.text or 'NIGHTMARE' in self.text:
            accent = (255, 0, 0)
        else:
            accent = HELLFIRE
        
        # Base button color
        base_r = 40 + int(40 * self.hover_progress)
        base_color = (base_r, 0, 0)
        
        # Red glow behind hovered button
        if self.hover_progress > 0.1:
            glow = pg.Surface((self.rect.width + 30, self.rect.height + 20), pg.SRCALPHA)
            glow_alpha = int(90 * self.hover_progress)
            glow_color = (accent[0] // 2, accent[1] // 2, accent[2] // 2, glow_alpha)
            pg.draw.rect(glow, glow_color, glow.get_rect(), border_radius=10)
            screen.blit(glow, (self.rect.x - 15, self.rect.y - 10))
        
        # Main rectangle
        pg.draw.rect(screen, base_color, self.rect, border_radius=8)
        
        # Border (intensifies on hover, uses difficulty accent)
        border_r = int(120 + (accent[0] - 120) * self.hover_progress)
        border_g = int(accent[1] * self.hover_progress)
        border_b = int(accent[2] * self.hover_progress)
        border_color = (min(255, border_r), min(255, border_g), min(255, border_b))
        pg.draw.rect(screen, border_color, self.rect, 2, border_radius=8)

        # --- TEXT RENDERING ---
        text_color = BONE_WHITE if self.is_hovered else BONE_DIM
        
        if self.value_text:
            # --- THE NEW TEXT DROP SHADOW ---
            shadow_color = (0, 0, 0)
            shadow_offset = 3
            
            # Split Rendering: Label Left, Value Right
            # Auto-scale padding
            padding = 25
            max_label_w = (self.rect.width // 2) - padding
            
            # Label
            label_surf = font.render(self.text, True, text_color)
            if label_surf.get_width() > max_label_w:
                scale_ratio = max_label_w / label_surf.get_width()
                new_w = int(label_surf.get_width() * scale_ratio)
                new_h = int(label_surf.get_height() * scale_ratio)
                label_surf = pg.transform.smoothscale(label_surf, (new_w, new_h))
            
            label_rect = label_surf.get_rect(midleft=(self.rect.left + padding, self.rect.centery - 2))
            
            # Label Shadow
            label_shadow = font.render(self.text, True, shadow_color)
            if label_shadow.get_width() > max_label_w:
                label_shadow = pg.transform.smoothscale(label_shadow, (label_surf.get_width(), label_surf.get_height()))
            
            # Value (Highlight in red/fire color)
            val_color = HELLFIRE if self.is_hovered else (180, 50, 50)
            value_surf = font.render(self.value_text, True, val_color)
            if value_surf.get_width() > max_label_w:
                scale_ratio = max_label_w / value_surf.get_width()
                new_w = int(value_surf.get_width() * scale_ratio)
                new_h = int(value_surf.get_height() * scale_ratio)
                value_surf = pg.transform.smoothscale(value_surf, (new_w, new_h))
                
            value_rect = value_surf.get_rect(midright=(self.rect.right - padding, self.rect.centery - 2))
            
            # Value Shadow
            value_shadow = font.render(self.value_text, True, shadow_color)
            if value_shadow.get_width() > max_label_w:
                value_shadow = pg.transform.smoothscale(value_shadow, (value_surf.get_width(), value_surf.get_height()))

            # Blit Shadows
            screen.blit(label_shadow, (label_rect.x + shadow_offset, label_rect.y + shadow_offset))
            screen.blit(value_shadow, (value_rect.x + shadow_offset, value_rect.y + shadow_offset))
            
            # Blit Main Text
            screen.blit(label_surf, label_rect)
            screen.blit(value_surf, value_rect)
        else:
            # --- THE NEW TEXT DROP SHADOW ---
            shadow_color = (0, 0, 0)
            shadow_offset = 3
            
            # Centered Rendering (Default)
            txt_surf = font.render(self.text, True, text_color)
            
            # Auto-scale if text overflows button width
            padding = 30
            if txt_surf.get_width() > self.rect.width - padding:
                scale_ratio = (self.rect.width - padding) / txt_surf.get_width()
                new_w = int(txt_surf.get_width() * scale_ratio)
                new_h = int(txt_surf.get_height() * scale_ratio)
                txt_surf = pg.transform.smoothscale(txt_surf, (new_w, new_h))
            
            # Render shadow
            shadow_surf = font.render(self.text, True, shadow_color)
            if shadow_surf.get_width() > self.rect.width - padding:
                shadow_surf = pg.transform.smoothscale(shadow_surf, (txt_surf.get_width(), txt_surf.get_height()))
            
            txt_rect = txt_surf.get_rect(center=(self.rect.centerx, self.rect.centery - 2))
            screen.blit(shadow_surf, (txt_rect.x + shadow_offset, txt_rect.y + shadow_offset))
            screen.blit(txt_surf, txt_rect)
        
        # Blood Accent Bar (left side)
        if self.hover_progress > 0.1:
            bar_h = int(self.rect.height * self.hover_progress)
            pg.draw.rect(screen, accent, (self.rect.left - 10, self.rect.centery - bar_h // 2, 4, bar_h))

        return self.is_hovered


class Slider:
    """Hell-themed horizontal slider for settings screens"""
    def __init__(self, x, y, width=300, value=0.5, label=''):
        self.x = x
        self.y = y
        self.width = width
        self.value = value  # 0.0 to 1.0
        self.label = label
        
        # Scaling factor based on reference height 900
        # Check if screen is initialized, fallback to 1.0
        try:
            sf = pg.display.get_surface().get_height() / 900
        except:
            sf = 1.0
            
        self.track_height = max(2, int(8 * sf))
        self.track_rect = pg.Rect(x - width // 2, y - self.track_height // 2, width, self.track_height)
        self.knob_radius = int(12 * sf)
        self.dragging = False
        self.hovered = False

    def update(self, mouse_pos, mouse_pressed, mouse_clicked):
        """Update slider state. Returns True if value changed."""
        knob_x = self.track_rect.x + int(self.value * self.width)
        knob_rect = pg.Rect(knob_x - self.knob_radius, self.y - self.knob_radius,
                            self.knob_radius * 2, self.knob_radius * 2)
        
        self.hovered = knob_rect.collidepoint(mouse_pos) or self.track_rect.collidepoint(mouse_pos)
        
        if mouse_clicked and self.hovered:
            self.dragging = True
        
        if not mouse_pressed:
            self.dragging = False
        
        if self.dragging:
            new_val = (mouse_pos[0] - self.track_rect.x) / self.width
            new_val = max(0.0, min(1.0, new_val))
            if new_val != self.value:
                self.value = new_val
                return True
        return False

    def draw(self, screen, font):
        """Draw the slider with hell theme"""
        # Label
        if self.label:
            label_surf = font.render(self.label, True, BONE_DIM)
            label_rect = label_surf.get_rect(center=(self.x, self.y - 35))
            screen.blit(label_surf, label_rect)
        
        # Track background
        pg.draw.rect(screen, (60, 0, 0), self.track_rect, border_radius=4)
        
        # Filled portion
        fill_width = int(self.value * self.width)
        if fill_width > 0:
            fill_rect = pg.Rect(self.track_rect.x, self.track_rect.y, fill_width, self.track_height)
            pg.draw.rect(screen, BLOOD_RED, fill_rect, border_radius=4)
        
        # Track border
        pg.draw.rect(screen, (120, 0, 0), self.track_rect, 1, border_radius=4)
        
        # Knob
        knob_x = self.track_rect.x + fill_width
        knob_color = HELLFIRE if (self.hovered or self.dragging) else BLOOD_RED
        
        # Glow when active
        if self.hovered or self.dragging:
            glow_surf = pg.Surface((self.knob_radius * 4, self.knob_radius * 4), pg.SRCALPHA)
            pg.draw.circle(glow_surf, (120, 0, 0, 60),
                          (self.knob_radius * 2, self.knob_radius * 2), self.knob_radius * 2)
            screen.blit(glow_surf, (knob_x - self.knob_radius * 2, self.y - self.knob_radius * 2))
        
        pg.draw.circle(screen, knob_color, (knob_x, self.y), self.knob_radius)
        pg.draw.circle(screen, (200, 40, 40), (knob_x, self.y), self.knob_radius, 2)
        
        # Value percentage
        pct_text = font.render(f"{int(self.value * 100)}%", True, BONE_WHITE)
        pct_rect = pct_text.get_rect(midleft=(self.track_rect.right + 20, self.y))
        screen.blit(pct_text, pct_rect)
