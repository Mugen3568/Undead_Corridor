import pygame as pg
from settings import *
from random import choices, randrange, choice

# Standard map layout (Fallback)
_ = False
mini_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
    [1, _, _, 3, 3, 3, 3, _, _, _, 2, 2, 2, _, _, 1],
    [1, _, _, _, _, _, 4, _, _, _, _, _, 2, _, _, 1],
    [1, _, _, _, _, _, 4, _, _, _, _, _, 2, _, _, 1],
    [1, _, _, 3, 3, 3, 3, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, 4, _, _, _, 4, _, _, _, _, _, _, 1],
    [1, 1, 1, 3, 1, 3, 1, 1, 1, 3, _, _, 3, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


class Map:
    def __init__(self, game):
        self.game = game
        self.mini_map = mini_map  # Store fallback
        self.world_map = {}
        self.rows = rows
        self.cols = cols
        self.get_procedural_map()  # Generate random map on startup

    def get_procedural_map(self):
        """ Generates a Complex Tactical Dungeon with Interior Decorations """
        self.world_map = {}
        self.floor_tiles = set()
        
        # 1. Settings based on Level Size
        area = self.cols * self.rows
        # More attempts = denser map with more rooms
        attempts = int(area * 0.4)
        
        min_size = 6
        max_size = 12
        rooms = []

        # 2. Generate Base Rooms (Non-overlapping)
        for _ in range(attempts):
            w = randrange(min_size, max_size)
            h = randrange(min_size, max_size)
            x = randrange(2, self.cols - w - 2)
            y = randrange(2, self.rows - h - 2)
            
            # Check Overlap (with padding to prevent merged blobs)
            new_rect = pg.Rect(x - 1, y - 1, w + 2, h + 2)
            overlap = False
            for (rx, ry, rw, rh) in rooms:
                if new_rect.colliderect(pg.Rect(rx, ry, rw, rh)):
                    overlap = True
                    break
            
            if not overlap:
                rooms.append((x, y, w, h))
                # Carve the basic floor
                for i in range(x, x + w):
                    for j in range(y, y + h):
                        self.floor_tiles.add((i, j))
                
                # --- NEW: Add Tactical Cover (Interior Design) ---
                self.decorate_room(x, y, w, h)

        # 3. Connect Rooms (Corridors)
        # Sorting helps create a cleaner "flow" from left to right
        rooms.sort(key=lambda r: r[0])
        
        for i in range(len(rooms) - 1):
            (x1, y1, w1, h1) = rooms[i]
            (x2, y2, w2, h2) = rooms[i+1]
            
            cx1, cy1 = x1 + w1 // 2, y1 + h1 // 2
            cx2, cy2 = x2 + w2 // 2, y2 + h2 // 2
            
            # Create "Dogleg" corridors (L-shaped) instead of straight lines
            # This blocks line of sight, forcing close combat
            
            # Horizontal leg
            start_x, end_x = min(cx1, cx2), max(cx1, cx2)
            for x in range(start_x, end_x + 1):
                self.floor_tiles.add((x, cy1))
                
            # Vertical leg
            start_y, end_y = min(cy1, cy2), max(cy1, cy2)
            for y in range(start_y, end_y + 1):
                self.floor_tiles.add((cx2, y))

        # 4. Build Final Walls
        for j in range(self.rows):
            for i in range(self.cols):
                if (i, j) not in self.floor_tiles:
                    self.world_map[(i, j)] = choice([1, 2, 3, 4, 5])
        
        # 5. Set Spawn
        if rooms:
            self.center_x = rooms[0][0] + rooms[0][2] // 2
            self.center_y = rooms[0][1] + rooms[0][3] // 2
        else:
            self.center_x, self.center_y = self.cols // 2, self.rows // 2

    def decorate_room(self, x, y, w, h):
        """ Adds pillars, partition walls, and corners for tactical cover """
        # Only decorate if room is big enough
        if w < 5 or h < 5:
            return

        layout_type = choice(['pillars', 'central_block', 'partition', 'corners', 'random'])
        
        # 1. Four Corners (Classic Arena)
        if layout_type == 'corners':
            # Place blocks in the 4 corners, leaving space to walk
            for dx in [1, w - 2]:
                for dy in [1, h - 2]:
                    if (x + dx, y + dy) in self.floor_tiles:
                        self.floor_tiles.remove((x + dx, y + dy))

        # 2. Central Block (The "Donut" Room)
        elif layout_type == 'central_block':
            # Big chunk in the middle
            cw, ch = w // 3, h // 3
            cx, cy = x + (w - cw) // 2, y + (h - ch) // 2
            for i in range(cx, cx + cw):
                for j in range(cy, cy + ch):
                    if (i, j) in self.floor_tiles:
                        self.floor_tiles.remove((i, j))

        # 3. Pillars (Forest)
        elif layout_type == 'pillars':
            # Place 1x1 columns every 2 tiles
            for i in range(x + 2, x + w - 2, 2):
                for j in range(y + 2, y + h - 2, 2):
                    if (i, j) in self.floor_tiles:
                        self.floor_tiles.remove((i, j))

        # 4. Partition Wall (The "U" or "Split" Room)
        elif layout_type == 'partition':
            # Vertical wall in the middle, but leaving gaps at ends
            mid_x = x + w // 2
            for j in range(y + 1, y + h - 1):
                if j != y + h // 2:  # Leave a hole in the center
                    if (mid_x, j) in self.floor_tiles:
                        self.floor_tiles.remove((mid_x, j))

    def draw(self):
        """Draws the Mini-Map in the bottom left"""
        # 1. Draw Background (Black box)
        pg.draw.rect(self.game.screen, 'black', (*MINIMAP_POS, *MINIMAP_RES))

        # 2. Draw Walls
        for pos in self.world_map:
            x = pos[0] * MINIMAP_SCALE + MINIMAP_POS[0]
            y = pos[1] * MINIMAP_SCALE + MINIMAP_POS[1]
            pg.draw.rect(self.game.screen, MINIMAP_WALL_COLOR, (x, y, MINIMAP_SCALE, MINIMAP_SCALE))

        # 3. Draw NPCs (enemies and bosses)
        for npc in self.game.object_handler.npc_list:
            if npc.alive:
                x = npc.x * MINIMAP_SCALE + MINIMAP_POS[0]
                y = npc.y * MINIMAP_SCALE + MINIMAP_POS[1]
                if npc.is_boss:
                    pg.draw.circle(self.game.screen, (255, 0, 0), (int(x), int(y)), 5)  # Big Red Dot
                else:
                    pg.draw.circle(self.game.screen, (200, 0, 0), (int(x), int(y)), 3)  # Small Dot

        # 4. Draw Player
        player_x = self.game.player.x * MINIMAP_SCALE + MINIMAP_POS[0]
        player_y = self.game.player.y * MINIMAP_SCALE + MINIMAP_POS[1]
        pg.draw.circle(self.game.screen, MINIMAP_PLAYER_COLOR, (int(player_x), int(player_y)), 3)