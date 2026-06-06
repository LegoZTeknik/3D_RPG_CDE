import pygame
import json
import os
import math
from enum import Enum

# ==========================================
#            MAP EDITOR (ENHANCED UI)
# ==========================================

class TileType(Enum):
    EMPTY = 0; WALL_BRICK = 1; WALL_STONE = 2; WALL_WOOD = 3
    DOOR = 4; DOOR_SILVER = 5; DOOR_GOLD = 6
    TREE = 10; DEAD_TREE = 11; BUSH = 12; ROCK = 13
    STANDING_TORCH = 14; WALL_TORCH = 15
    ITEM_DAGGER = 20; ITEM_KEY = 21; ITEM_KEY_SILVER = 22; ITEM_KEY_GOLD = 23
    ITEM_KEY_DUNGEON = 24; ITEM_HEALTH_POTION = 25; ITEM_FOOD = 26; ITEM_ARTIFACT = 27
    PLAYER_SPAWN = 50; ENEMY_GHOST = 60

MAP_SIZE = 48
MAP_DATA_FILE = "map_data.json"

class MapEditor:
    def __init__(self):
        pygame.init()
        self.editor_width, self.editor_height = 1400, 900
        self.left_panel_w, self.right_panel_w = 220, 280
        self.screen = pygame.display.set_mode((self.editor_width, self.editor_height))
        pygame.display.set_caption("RPGW3D Map Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 11)
        self.font_large = pygame.font.SysFont("georgia", 16, bold=True)
        self.font_msg = pygame.font.SysFont("georgia", 14, bold=True)
        self.font_title = pygame.font.SysFont("georgia", 12, bold=True)
        
        # Map data
        self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.active_tile = TileType.WALL_BRICK.value
        self.camera_x, self.camera_y = self.left_panel_w + 50, 50
        self.zoom = 1.0
        
        # Level system
        self.current_level = 1
        self.current_floor = "STONE"
        self.floors = ["DIRT", "STONE", "SAND", "GRASS"]
        
        # UI state
        self.save_message = ""
        self.save_message_timer = 0
        self.selected_tool = None
        self.selected_enemy = "ghost"
        
        # Mouse state
        self.mouse_down = False
        self.is_panning = False
        self.p_start_m = (0, 0)
        self.p_start_c = (0, 0)
        
        # Setup buttons
        self.setup_buttons()
        self.load_map()

    def setup_buttons(self):
        """Setup all UI buttons"""
        self.system_buttons = [
            {"label": "SAVE MAP", "rect": pygame.Rect(10, 40, 200, 35), "action": "save"},
            {"label": "Undo", "rect": pygame.Rect(110, 40, 90, 35), "action": "undo"},
            {"label": "CLEAR", "rect": pygame.Rect(10, 80, 95, 35), "action": "clear"},
            {"label": "WIPE SAVE", "rect": pygame.Rect(110, 80, 100, 35), "action": "wipe"},
            {"label": "LVL UP", "rect": pygame.Rect(10, 120, 95, 35), "action": "lvl_up"},
            {"label": "LVL DOWN", "rect": pygame.Rect(110, 120, 100, 35), "action": "lvl_down"},
        ]
        
        self.tool_buttons = [
            {"label": "Erase", "rect": pygame.Rect(10, 180, 95, 35), "action": "erase", "tool": "erase"},
            {"label": "Fill", "rect": pygame.Rect(110, 180, 100, 35), "action": "fill", "tool": "fill"},
            {"label": "P Spawn", "rect": pygame.Rect(10, 220, 200, 35), "action": "spawn", "tool": "spawn"},
        ]
        
        self.enemy_buttons = [
            {"label": "👻 Ghost", "rect": pygame.Rect(10, 290, 200, 35), "action": "enemy", "enemy": "ghost"},
        ]
        
        # Right panel sections
        self.items_grid = self.create_grid(20, 100, 260, 5, [
            ("🗡️", "Dagger"), ("🔑", "Key"), ("🔴", "Red Key"), ("💜", "Purple Key"), ("💛", "Gold Key"),
            ("❤️", "Health"), ("🍖", "Food"), ("⚡", "Artifact"), ("", ""), ("", ""),
        ])
        
        self.world_objects_grid = self.create_grid(20, 240, 260, 5, [
            ("🌿", "Bush"), ("🌳", "Tree"), ("☠️", "Dead Tree"), ("🪨", "Rock"), ("💎", "Torch"),
            ("🔦", "W-Torch"), ("", ""), ("", ""), ("", ""), ("", ""),
        ])
        
        self.walls_grid = self.create_grid(20, 380, 260, 5, [
            ("🧱", "Brick"), ("⬜", "Stone"), ("🟤", "Wood"), ("🟨", "Brick D"), ("🟦", "Silver D"),
            ("🟨", "Gold D"), ("🪜", "Stairs"), ("🔴", "Cracked B"), ("🟠", "Cracked S"), ("🟣", "Cracked W"),
        ])
        
        self.floor_grid = self.create_grid(20, 520, 260, 4, [
            ("🟫", "Dirt"), ("⬜", "Stone"), ("🟨", "Sand"), ("🟩", "Grass"),
        ])

    def create_grid(self, x, y, width, cols, items):
        """Create a grid of item buttons"""
        grid = []
        item_w = (width - 20) // cols
        item_h = 35
        
        for idx, (icon, label) in enumerate(items):
            row = idx // cols
            col = idx % cols
            btn_x = x + 10 + col * (item_w + 5)
            btn_y = y + row * (item_h + 5)
            grid.append({
                "label": label,
                "icon": icon,
                "rect": pygame.Rect(btn_x, btn_y, item_w, item_h),
                "index": idx
            })
        
        return grid

    def load_map(self):
        """Load map from file"""
        if os.path.exists(MAP_DATA_FILE):
            try:
                with open(MAP_DATA_FILE, "r") as f:
                    data = json.load(f)
                    if "map" in data:
                        map_data = data["map"]
                        if len(map_data) == MAP_SIZE and all(len(row) == MAP_SIZE for row in map_data):
                            self.map = map_data
                            print(f"✓ Map loaded successfully")
            except Exception as e:
                print(f"✗ Failed to load map: {e}")

    def save_map(self):
        """Save map to file"""
        try:
            with open(MAP_DATA_FILE, "w") as f:
                json.dump({"map": self.map, "size": MAP_SIZE, "level": self.current_level}, f, indent=2)
            self.save_message = "✓ Map Saved!"
            self.save_message_timer = 120
            print(f"✓ Map saved successfully")
        except Exception as e:
            print(f"✗ Failed to save map: {e}")
            self.save_message = "✗ Save Failed!"
            self.save_message_timer = 120

    def handle_button_click(self, pos):
        """Handle button clicks"""
        # System buttons
        for btn in self.system_buttons:
            if btn["rect"].collidepoint(pos):
                if btn["action"] == "save":
                    self.save_map()
                elif btn["action"] == "clear":
                    self.map = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
                elif btn["action"] == "lvl_up":
                    self.current_level += 1
                elif btn["action"] == "lvl_down":
                    self.current_level = max(1, self.current_level - 1)
        
        # Tool buttons
        for btn in self.tool_buttons:
            if btn["rect"].collidepoint(pos):
                self.selected_tool = btn.get("tool")
        
        # Enemy buttons
        for btn in self.enemy_buttons:
            if btn["rect"].collidepoint(pos):
                self.selected_enemy = btn.get("enemy")
        
        # Items grid
        for item in self.items_grid:
            if item["rect"].collidepoint(pos) and item["label"]:
                # Map items to tile types
                item_map = {
                    "Dagger": TileType.ITEM_DAGGER.value,
                    "Key": TileType.ITEM_KEY.value,
                    "Red Key": TileType.ITEM_KEY_SILVER.value,
                    "Purple Key": TileType.ITEM_KEY_GOLD.value,
                    "Gold Key": TileType.ITEM_KEY_DUNGEON.value,
                    "Health": TileType.ITEM_HEALTH_POTION.value,
                    "Food": TileType.ITEM_FOOD.value,
                    "Artifact": TileType.ITEM_ARTIFACT.value,
                }
                self.active_tile = item_map.get(item["label"], 0)
        
        # World objects grid
        world_map = {
            "Bush": TileType.BUSH.value,
            "Tree": TileType.TREE.value,
            "Dead Tree": TileType.DEAD_TREE.value,
            "Rock": TileType.ROCK.value,
            "Torch": TileType.STANDING_TORCH.value,
            "W-Torch": TileType.WALL_TORCH.value,
        }
        for item in self.world_objects_grid:
            if item["rect"].collidepoint(pos) and item["label"]:
                self.active_tile = world_map.get(item["label"], 0)
        
        # Walls grid
        walls_map = {
            "Brick": TileType.WALL_BRICK.value,
            "Stone": TileType.WALL_STONE.value,
            "Wood": TileType.WALL_WOOD.value,
            "Brick D": TileType.DOOR.value,
            "Silver D": TileType.DOOR_SILVER.value,
            "Gold D": TileType.DOOR_GOLD.value,
        }
        for item in self.walls_grid:
            if item["rect"].collidepoint(pos) and item["label"]:
                self.active_tile = walls_map.get(item["label"], 0)
        
        # Floor grid (just for selection, doesn't change map directly)
        for item in self.floor_grid:
            if item["rect"].collidepoint(pos) and item["label"]:
                self.current_floor = item["label"].upper()

    def draw_left_panel(self):
        """Draw left panel with buttons"""
        # Panel background
        pygame.draw.rect(self.screen, (30, 30, 35), (0, 0, self.left_panel_w, self.editor_height))
        pygame.draw.line(self.screen, (200, 180, 100), (self.left_panel_w - 2, 0), (self.left_panel_w - 2, self.editor_height), 3)
        
        # Title
        title = self.font_title.render("SYSTEM", True, (200, 180, 100))
        self.screen.blit(title, (10, 15))
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw system buttons
        for btn in self.system_buttons:
            hover = btn["rect"].collidepoint(mouse_pos)
            bg_color = (50, 100, 150) if hover else (40, 50, 70)
            pygame.draw.rect(self.screen, bg_color, btn["rect"])
            pygame.draw.rect(self.screen, (200, 180, 100), btn["rect"], 2)
            
            text = self.font.render(btn["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)
        
        # Tools title
        tools_title = self.font_title.render("TOOLS", True, (200, 180, 100))
        self.screen.blit(tools_title, (10, 160))
        
        # Draw tool buttons
        for btn in self.tool_buttons:
            hover = btn["rect"].collidepoint(mouse_pos)
            bg_color = (100, 50, 50) if hover else (40, 50, 70)
            pygame.draw.rect(self.screen, bg_color, btn["rect"])
            pygame.draw.rect(self.screen, (200, 180, 100), btn["rect"], 2)
            
            text = self.font.render(btn["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)
        
        # Enemies title
        enemies_title = self.font_title.render("ENEMIES", True, (200, 180, 100))
        self.screen.blit(enemies_title, (10, 270))
        
        # Draw enemy buttons
        for btn in self.enemy_buttons:
            hover = btn["rect"].collidepoint(mouse_pos)
            bg_color = (150, 50, 50) if hover else (40, 50, 70)
            pygame.draw.rect(self.screen, bg_color, btn["rect"])
            pygame.draw.rect(self.screen, (200, 180, 100), btn["rect"], 2)
            
            text = self.font.render(btn["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

    def draw_right_panel(self):
        """Draw right panel with item grids"""
        # Panel background
        pygame.draw.rect(self.screen, (30, 30, 35), (self.editor_width - self.right_panel_w, 0, self.right_panel_w, self.editor_height))
        pygame.draw.line(self.screen, (200, 180, 100), (self.editor_width - self.right_panel_w + 2, 0), (self.editor_width - self.right_panel_w + 2, self.editor_height), 3)
        
        mouse_pos = pygame.mouse.get_pos()
        start_x = self.editor_width - self.right_panel_w + 10
        
        # Items section
        items_title = self.font_title.render("ITEMS", True, (200, 180, 100))
        self.screen.blit(items_title, (start_x, 20))
        
        for item in self.items_grid:
            hover = item["rect"].collidepoint(mouse_pos)
            bg_color = (100, 100, 50) if hover else (60, 60, 65)
            pygame.draw.rect(self.screen, bg_color, item["rect"])
            pygame.draw.rect(self.screen, (150, 150, 150), item["rect"], 1)
            
            if item["icon"]:
                icon_text = self.font_large.render(item["icon"], True, (255, 255, 255))
                self.screen.blit(icon_text, (item["rect"].centerx - 10, item["rect"].centery - 12))
        
        # World Objects section
        world_title = self.font_title.render("WORLD OBJECTS", True, (200, 180, 100))
        self.screen.blit(world_title, (start_x, 180))
        
        for item in self.world_objects_grid:
            hover = item["rect"].collidepoint(mouse_pos)
            bg_color = (100, 100, 50) if hover else (60, 60, 65)
            pygame.draw.rect(self.screen, bg_color, item["rect"])
            pygame.draw.rect(self.screen, (150, 150, 150), item["rect"], 1)
            
            if item["icon"]:
                icon_text = self.font_large.render(item["icon"], True, (255, 255, 255))
                self.screen.blit(icon_text, (item["rect"].centerx - 10, item["rect"].centery - 12))
        
        # Walls & Doors section
        walls_title = self.font_title.render("WALLS & DOORS", True, (200, 180, 100))
        self.screen.blit(walls_title, (start_x, 340))
        
        for item in self.walls_grid:
            hover = item["rect"].collidepoint(mouse_pos)
            bg_color = (100, 100, 50) if hover else (60, 60, 65)
            pygame.draw.rect(self.screen, bg_color, item["rect"])
            pygame.draw.rect(self.screen, (150, 150, 150), item["rect"], 1)
            
            if item["icon"]:
                icon_text = self.font_large.render(item["icon"], True, (255, 255, 255))
                self.screen.blit(icon_text, (item["rect"].centerx - 10, item["rect"].centery - 12))
        
        # Floor Brush section
        floor_title = self.font_title.render("FLOOR BRUSH", True, (200, 180, 100))
        self.screen.blit(floor_title, (start_x, 500))
        
        for item in self.floor_grid:
            hover = item["rect"].collidepoint(mouse_pos)
            is_selected = item["label"].upper() == self.current_floor
            bg_color = (200, 200, 100) if is_selected else (100, 100, 50) if hover else (60, 60, 65)
            pygame.draw.rect(self.screen, bg_color, item["rect"])
            pygame.draw.rect(self.screen, (200, 200, 100) if is_selected else (150, 150, 150), item["rect"], 2 if is_selected else 1)
            
            if item["icon"]:
                icon_text = self.font_large.render(item["icon"], True, (255, 255, 255))
                self.screen.blit(icon_text, (item["rect"].centerx - 10, item["rect"].centery - 12))

    def draw_top_bar(self):
        """Draw top information bar"""
        pygame.draw.rect(self.screen, (50, 50, 50), (self.left_panel_w, 0, self.editor_width - self.left_panel_w - self.right_panel_w, 40))
        pygame.draw.line(self.screen, (200, 180, 100), (self.left_panel_w, 40), (self.editor_width - self.right_panel_w, 40), 2)
        
        info_text = self.font_title.render(f"Level: {self.current_level} | Floor: {self.current_floor}", True, (200, 180, 100))
        self.screen.blit(info_text, (self.left_panel_w + 15, 10))

    def draw_map_canvas(self):
        """Draw the map canvas"""
        canvas_x = self.left_panel_w
        canvas_y = 40
        canvas_w = self.editor_width - self.left_panel_w - self.right_panel_w
        canvas_h = self.editor_height - 40
        
        # Canvas background
        pygame.draw.rect(self.screen, (40, 40, 40), (canvas_x, canvas_y, canvas_w, canvas_h))
        
        # Draw grid
        cell = int(24 * self.zoom)
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                px = canvas_x + self.camera_x + x * cell
                py = canvas_y + self.camera_y + y * cell
                
                if px < canvas_x or px > canvas_x + canvas_w or py < canvas_y or py > canvas_y + canvas_h:
                    continue
                
                val = self.map[y][x]
                rect = pygame.Rect(px, py, cell, cell)
                
                if val == 0:
                    pygame.draw.rect(self.screen, (60, 60, 60), rect, 1)
                else:
                    # Color coding for different tile types
                    if val in [1, 2, 3, 4, 5, 6]:  # Walls & doors
                        color = (150, 100, 80)
                    elif val == 50:  # Player spawn
                        color = (0, 255, 0)
                    elif val == 60:  # Enemy
                        color = (255, 0, 0)
                    else:  # Objects & items
                        color = (100, 150, 100)
                    
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

    def draw_bottom_bar(self):
        """Draw bottom status bar"""
        pygame.draw.rect(self.screen, (30, 30, 30), (self.left_panel_w, self.editor_height - 30, self.editor_width - self.left_panel_w - self.right_panel_w, 30))
        pygame.draw.line(self.screen, (200, 180, 100), (self.left_panel_w, self.editor_height - 30), (self.editor_width - self.right_panel_w, self.editor_height - 30), 2)
        
        # Get active tile name
        active_name = "Empty"
        for tile_type in TileType:
            if tile_type.value == self.active_tile:
                active_name = tile_type.name.replace("_", " ")
                break
        
        status_text = self.font.render(f"Currently Selected: {active_name}", True, (200, 180, 100))
        self.screen.blit(status_text, (self.left_panel_w + 10, self.editor_height - 25))
        
        # Draw save message
        if self.save_message_timer > 0:
            self.save_message_timer -= 1
            msg_color = (100, 255, 100) if "✓" in self.save_message else (255, 100, 100)
            msg_text = self.font_msg.render(self.save_message, True, msg_color)
            self.screen.blit(msg_text, (self.editor_width // 2 - msg_text.get_width() // 2, self.editor_height - 60))

    def run(self):
        """Main editor loop"""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    running = False
                
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_s:
                        self.save_map()
                
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        # Check if clicking on left/right panels (UI)
                        if mouse_pos[0] < self.left_panel_w or mouse_pos[0] > self.editor_width - self.right_panel_w:
                            self.handle_button_click(mouse_pos)
                        else:
                            self.mouse_down = True
                            self.p_start_m = mouse_pos
                            self.p_start_c = (self.camera_x, self.camera_y)
                    elif e.button in (2, 3):
                        self.is_panning = True
                        self.p_start_m = mouse_pos
                        self.p_start_c = (self.camera_x, self.camera_y)
                    elif e.button == 4:
                        self.zoom = min(3.0, self.zoom + 0.1)
                    elif e.button == 5:
                        self.zoom = max(0.5, self.zoom - 0.1)
                
                elif e.type == pygame.MOUSEBUTTONUP:
                    if e.button == 1:
                        self.mouse_down = False
                    elif e.button in (2, 3):
                        self.is_panning = False
                
                elif e.type == pygame.MOUSEMOTION:
                    if self.is_panning:
                        self.camera_x = self.p_start_c[0] + mouse_pos[0] - self.p_start_m[0]
                        self.camera_y = self.p_start_c[1] + mouse_pos[1] - self.p_start_m[1]
                    elif self.mouse_down:
                        # Paint on map
                        canvas_x = self.left_panel_w
                        canvas_y = 40
                        canvas_w = self.editor_width - self.left_panel_w - self.right_panel_w
                        canvas_h = self.editor_height - 70
                        
                        if canvas_x < mouse_pos[0] < canvas_x + canvas_w and canvas_y < mouse_pos[1] < canvas_y + canvas_h:
                            cell = int(24 * self.zoom)
                            gx = int((mouse_pos[0] - canvas_x - self.camera_x) // cell)
                            gy = int((mouse_pos[1] - canvas_y - self.camera_y) // cell)
                            
                            if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                                if self.selected_tool == "erase":
                                    self.map[gy][gx] = 0
                                elif self.selected_tool == "fill":
                                    self.map[gy][gx] = self.active_tile
                                elif self.selected_tool == "spawn":
                                    self.map[gy][gx] = TileType.PLAYER_SPAWN.value
                                else:
                                    self.map[gy][gx] = self.active_tile
            
            # Draw everything
            self.screen.fill((20, 20, 20))
            self.draw_map_canvas()
            self.draw_left_panel()
            self.draw_right_panel()
            self.draw_top_bar()
            self.draw_bottom_bar()
            
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    editor = MapEditor()
    editor.run()
