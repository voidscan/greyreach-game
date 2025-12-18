#!/usr/bin/env python3
import pygame
import sys
import random
import math

# --- 1. Game Setup Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CAPTION = "Cellular Scape: Swirl-Shield Mode"
FPS = 60

# Tile Map Constants
TILE_SIZE = 50
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# --- GAME CONSTANTS ---
TOTAL_LEVELS = 10
CORES_NEEDED = 3
# --------------------

# Colors
BLACK = (0, 0, 0)
WALL_COLOR = (80, 80, 80)
FLOOR_COLOR = (40, 40, 40)
NANOBOT_COLOR = (255, 255, 0)
SENTINEL_COLOR = (255, 0, 0)
BULLET_COLOR = (100, 200, 255) 
CRATE_COLOR = (150, 90, 40)
CORE_COLOR = (0, 255, 150)
DOOR_COLOR = (255, 150, 0)
SHIELD_COLOR = (0, 200, 255)
CROSSHAIR_COLOR = (255, 255, 255)
MENU_SELECT_COLOR = (150, 255, 150)
AMMO_COLOR = (255, 100, 255)
HEALTH_COLOR = (0, 255, 0)
SWIRL_COLOR = (255, 100, 0) # Orange/Red for the damaging shield

# Physics and Movement
MOVE_SPEED = 5
LIGHT_RADIUS = 200 
SENTINEL_SPEED = 2
BULLET_SPEED = 10 
FIRE_COOLDOWN = 15 
CRATE_HEALTH = 3

# Shield Constants
SHIELD_RADIUS = 30 # Size of the protective field
SWIRL_AMMO_COST = 5 # Ammo consumed per second (5/60 per frame)

# Nanobot particle color (glowing yellow)
NANOBOT_PARTICLE_COLOR = (255, 255, 150)

# --- 2. Initialize Pygame ---
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(CAPTION)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 30)
font_large = pygame.font.Font(None, 70)

AIM_POINT = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# --- 2b. Sound Assets and Loading ---
try:
    # Use Channel 0 exclusively for the Swirl Sound to manage its playback state.
    SWIRL_CHANNEL = pygame.mixer.Channel(0)

    # Use 'shoot.wav.mp3' for shooting
    SOUND_LASER = pygame.mixer.Sound('shoot.wav.mp3')      
    # Use 'explode.wav.mp3' for explosion/death
    SOUND_EXPLOSION = pygame.mixer.Sound('explode.wav.mp3')
    # Use 'swirl.wav.mp3' for the looping shield sound
    SOUND_SWIRL_LOOP = pygame.mixer.Sound('swirl.wav.mp3') 
    
    # Using 'energy-90321.mp3' or 'power sad.mp3' for effects/powerups
    SOUND_HIT = pygame.mixer.Sound('energy-90321.mp3')       
    SOUND_POWERUP = pygame.mixer.Sound('power sad.mp3')   
    SOUND_GAMEOVER = pygame.mixer.Sound('energy-90321.mp3')  
    SOUND_WIN = pygame.mixer.Sound('power sad.mp3')       
    
    # Music loading (using 'game sound.mp3' as confirmed main sound)
    pygame.mixer.music.load('game sound.mp3')            
    
    # Optional: Set volumes
    SOUND_LASER.set_volume(0.3)
    SOUND_HIT.set_volume(0.5)
    SOUND_POWERUP.set_volume(0.7)
    SOUND_EXPLOSION.set_volume(0.8)
    SOUND_SWIRL_LOOP.set_volume(0.4)
    pygame.mixer.music.set_volume(0.5)

except pygame.error as e:
    print(f"Warning: Could not load sound files. Ensure all audio files are present and match the names. Error: {e}")
    # Create dummy objects to avoid crashing if sounds are missing
    class DummySound:
        def play(self, loops=0): pass
        def stop(self): pass
        def set_volume(self, vol): pass
    
    class DummyChannel:
        def play(self, sound, loops=-1): pass
        def stop(self): pass
        def get_busy(self): return False

    SOUND_LASER = SOUND_HIT = SOUND_POWERUP = SOUND_EXPLOSION = SOUND_SWIRL_LOOP = SOUND_GAMEOVER = SOUND_WIN = DummySound()
    SWIRL_CHANNEL = DummyChannel() # Dummy channel for error handling

    class DummyMusic:
        def load(self, f): pass
        def play(self, loops=-1): pass
        def stop(self): pass
        def set_volume(self, vol): pass
    pygame.mixer.music = DummyMusic()

# --- 3. Asset and Map Generation (Level Setup Function) ---

def is_valid(x, y):
    return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

def generate_level(level_num):
    """Generates a map, ensuring a valid path exists from start to the door."""
    
    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for x in range(GRID_WIDTH):
        grid[0][x] = 1; grid[GRID_HEIGHT - 1][x] = 1
    for y in range(GRID_HEIGHT):
        grid[y][0] = 1; grid[y][GRID_WIDTH - 1] = 1

    all_floor_tiles = []
    for y in range(1, GRID_HEIGHT - 1):
        for x in range(1, GRID_WIDTH - 1):
            all_floor_tiles.append((x, y))

    if not all_floor_tiles:
        start_pos = (1, 1)
        door_tile = (GRID_WIDTH - 2, GRID_HEIGHT - 2)
    else:
        start_tile = random.choice(all_floor_tiles)
        all_floor_tiles.remove(start_tile)
        start_pos = start_tile

        far_tiles = sorted(all_floor_tiles, key=lambda p: math.hypot(p[0] - start_pos[0], p[1] - start_pos[1]), reverse=True)
        door_tile = far_tiles[0] if far_tiles else (GRID_WIDTH - 2, GRID_HEIGHT - 2)
        if door_tile in all_floor_tiles: all_floor_tiles.remove(door_tile)

    grid[start_pos[1]][start_pos[0]] = 0
    grid[door_tile[1]][door_tile[0]] = 0

    num_walls = 15 + level_num * 2
    for _ in range(num_walls):
        wx = random.randint(2, GRID_WIDTH - 3)
        wy = random.randint(2, GRID_HEIGHT - 3)
        if (wx, wy) != start_pos and (wx, wy) != door_tile:
            if random.random() < 0.5: 
                for x in range(wx, wx + random.randint(2, 4)):
                    if 0 < x < GRID_WIDTH - 1 and (x, wy) != start_pos and (x, wy) != door_tile: grid[wy][x] = 1
            else:
                for y in range(wy, wy + random.randint(2, 4)):
                    if 0 < y < GRID_HEIGHT - 1 and (wx, y) != start_pos and (wx, y) != door_tile: grid[y][wx] = 1
    
    spawn_tiles = [(x, y) for x, y in all_floor_tiles if grid[y][x] == 0]

    enemies_pos = []
    crates_pos = []
    cores_pos = []
    
    for _ in range(2 + level_num):
        if spawn_tiles:
            ex, ey = random.choice(spawn_tiles)
            enemies_pos.append((ex * TILE_SIZE + TILE_SIZE // 2, ey * TILE_SIZE + TILE_SIZE // 2))
            spawn_tiles.remove((ex, ey))
                
    for _ in range(5 + level_num * 2):
        if spawn_tiles:
            cx, cy = random.choice(spawn_tiles)
            crates_pos.append((cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2))
            spawn_tiles.remove((cx, cy))
            
    for _ in range(CORES_NEEDED):
        if spawn_tiles:
            cx, cy = random.choice(spawn_tiles)
            cores_pos.append((cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2))
            spawn_tiles.remove((cx, cy))
            
    return grid, start_pos, enemies_pos, crates_pos, cores_pos, door_tile

# --- 4. Game Objects (Classes) ---

class Particle:
    def __init__(self, x, y, color=(200, 200, 200), max_life=50, speed=0.5):
        self.x = x; self.y = y; self.radius = random.randint(1, 3)
        self.color = color; self.velocity = [random.uniform(-speed, speed), random.uniform(-speed, speed)]
        self.alpha = random.randint(150, 255); self.life = 0; self.max_life = max_life
    def update(self):
        self.x += self.velocity[0]; self.y += self.velocity[1]; self.life += 1
        self.alpha = max(0, 255 - (self.life * (255 / self.max_life)))
        return self.life >= self.max_life
    def draw(self, screen):
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color_rgba = self.color + (int(self.alpha),) if len(self.color) == 3 else self.color
        pygame.draw.circle(surface, color_rgba, (self.radius, self.radius), self.radius)
        screen.blit(surface, (self.x - self.radius, self.y - self.radius))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_sentinel):
        super().__init__()
        self.target = target_sentinel
        size = 8; self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BULLET_COLOR + (150,), (size//2, size//2), size//2) 
        pygame.draw.circle(self.image, (255, 255, 255), (size//2, size//2), size//3)
        
        self.rect = self.image.get_rect(center=start_pos); self.speed = BULLET_SPEED
        self.vx, self.vy = 0, 0 

    def update(self):
        if self.target and self.target.alive():
            target_x, target_y = self.target.rect.center
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
                self.rect.x += self.vx
                self.rect.y += self.vy
            else: 
                self.kill()
        else:
            self.rect.x += self.vx
            self.rect.y += self.vy
            if not screen.get_rect().colliderect(self.rect): self.kill()
        
        if random.random() < 0.3:
             global particles
             particles.append(Particle(self.rect.centerx, self.rect.centery, color=BULLET_COLOR, max_life=10, speed=1))


class Sentinel(pygame.sprite.Sprite):
    def __init__(self, start_pos):
        super().__init__(); size = TILE_SIZE * 0.5
        self.image = pygame.Surface((size, size)); self.image.fill(SENTINEL_COLOR)
        self.rect = self.image.get_rect(); self.rect.center = start_pos
        self.alive_status = True 
    def kill(self):
        self.alive_status = False
        super().kill()
    def alive(self):
        return self.alive_status
    def update(self, nanobot, game_map):
        dist = math.hypot(self.rect.centerx - nanobot.rect.centerx, self.rect.centery - nanobot.rect.centery)
        if dist < LIGHT_RADIUS * 1.5:
            angle = math.atan2(nanobot.rect.centery - self.rect.centery, nanobot.rect.centerx - self.rect.centerx)
            target_vx = SENTINEL_SPEED * math.cos(angle); target_vy = SENTINEL_SPEED * math.sin(angle)
            new_x = self.rect.x + target_vx; new_y = self.rect.y + target_vy
            self.rect.x = new_x; 
            if self.check_collision(game_map): self.rect.x = new_x - target_vx
            self.rect.y = new_y
            if self.check_collision(game_map): self.rect.y = new_y - target_vy
    def check_collision(self, game_map):
        center_tile_x = int(self.rect.centerx // TILE_SIZE); center_tile_y = int(self.rect.centery // TILE_SIZE)
        return (0 <= center_tile_y < GRID_HEIGHT and 0 <= center_tile_x < GRID_WIDTH and game_map[center_tile_y][center_tile_x] == 1)

class Crate(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(); size = TILE_SIZE * 0.7
        self.image = pygame.Surface((size, size)); self.image.fill(CRATE_COLOR)
        pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 2)
        self.rect = self.image.get_rect(center=pos); self.health = CRATE_HEALTH
    def hit(self, particles):
        self.health -= 1
        for _ in range(5): particles.append(Particle(self.rect.centerx, self.rect.centery, color=CRATE_COLOR, max_life=10, speed=1))
        
        if self.health <= 0:
            self.kill()
            for _ in range(10): particles.append(Particle(self.rect.centerx, self.rect.centery, color=CRATE_COLOR, max_life=30, speed=2))
            
            loot_roll = random.random()
            if loot_roll < 0.2: 
                return PowerUp(self.rect.center)
            elif loot_roll < 0.45:
                return AmmoPowerUp(self.rect.center)
            elif loot_roll < 0.65:
                return HealthPowerUp(self.rect.center)
        return None
        
class PowerCore(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(); size = TILE_SIZE * 0.4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, CORE_COLOR, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=pos)
        
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(); size = TILE_SIZE * 0.5
        self.type = random.choice(['shield', 'multishot'])
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = SHIELD_COLOR if self.type == 'shield' else BULLET_COLOR
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=pos)

class AmmoPowerUp(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(); size = TILE_SIZE * 0.5
        self.type = 'ammo'
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, AMMO_COLOR, self.image.get_rect(), 0)
        pygame.draw.line(self.image, (255, 255, 255), (size*0.2, size*0.5), (size*0.8, size*0.5), 3)
        self.rect = self.image.get_rect(center=pos)

class HealthPowerUp(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(); size = TILE_SIZE * 0.5
        self.type = 'health'
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, HEALTH_COLOR, (size*0.2, size*0.4, size*0.6, size*0.2), 0)
        pygame.draw.rect(self.image, HEALTH_COLOR, (size*0.4, size*0.2, size*0.2, size*0.6), 0)
        self.rect = self.image.get_rect(center=pos)
        
class LevelDoor(pygame.sprite.Sprite):
    def __init__(self, tile_pos):
        super().__init__(); size = TILE_SIZE
        self.image = pygame.Surface((size, size)); self.image.fill(DOOR_COLOR)
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 3)
        self.rect = self.image.get_rect(x=tile_pos[0] * TILE_SIZE, y=tile_pos[1] * TILE_SIZE)
        
    def draw(self, screen): # <-- ADDED THE MISSING DRAW METHOD
        """Draws the door to the screen."""
        screen.blit(self.image, self.rect)


class Nanobot(pygame.sprite.Sprite):
    def __init__(self, start_pos_tile):
        super().__init__()
        size = TILE_SIZE * 0.6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.centerx = start_pos_tile[0] * TILE_SIZE + TILE_SIZE // 2
        self.rect.centery = start_pos_tile[1] * TILE_SIZE + TILE_SIZE // 2
        self.velocity_x = 0; self.velocity_y = 0; self.cooldown_timer = 0
        self.max_health = 100; self.current_health = 100
        self.ammo_count = 100
        self.shield_active = False; self.multi_shot_active = False
        self.shield_timer = 0; self.multi_shot_timer = 0
        self.facing_angle = 0 
        self.gun_angle = 0 
        self.is_swirling = False 
        self.swirl_angle = 0 

    def apply_powerup(self, p_type):
        if p_type == 'shield': self.shield_active = True; self.shield_timer = 300
        elif p_type == 'multishot': self.multi_shot_active = True; self.multi_shot_timer = 600
        elif p_type == 'ammo': self.ammo_count = min(999, self.ammo_count + 50)
        elif p_type == 'health': self.current_health = min(self.max_health, self.current_health + 25)
        SOUND_POWERUP.play() # Play general powerup sound

    def update(self, game_map):
        global SWIRL_CHANNEL 
        
        new_x = self.rect.x + self.velocity_x; new_y = self.rect.y + self.velocity_y
        self.rect.x = new_x; 
        if self.check_collision(game_map): self.rect.x = new_x - self.velocity_x
        self.rect.y = new_y; 
        if self.check_collision(game_map): self.rect.y = new_y - self.velocity_y
        if self.cooldown_timer > 0: self.cooldown_timer -= 1
        if self.shield_timer > 0: self.shield_timer -= 1; 
        if self.shield_timer == 0: self.shield_active = False
        if self.multi_shot_timer > 0: self.multi_shot_timer -= 1;
        if self.multi_shot_timer == 0: self.multi_shot_active = False
        
        # Swirl-Shield update: Ammo drain, animation, and SOUND control
        if self.is_swirling:
            if self.ammo_count > 0:
                self.ammo_count = max(0, self.ammo_count - SWIRL_AMMO_COST / FPS)
            if self.ammo_count <= 0:
                self.is_swirling = False
            
            self.swirl_angle = (self.swirl_angle + 10) % 360 
            
            # Start the loop if it's not already playing on its dedicated channel
            if not SWIRL_CHANNEL.get_busy(): # Check the Channel, not the Sound object
                SWIRL_CHANNEL.play(SOUND_SWIRL_LOOP, -1) # Play indefinitely on Channel 0
        else:
            # Stop sound when swirling stops
            if SWIRL_CHANNEL.get_busy(): # Check the Channel
                SWIRL_CHANNEL.stop() 

        # Gun angle (aims at crosshair)
        aim_dx = AIM_POINT[0] - self.rect.centerx
        aim_dy = AIM_POINT[1] - self.rect.centery
        self.gun_angle = math.atan2(aim_dy, aim_dx)
        
        # Add glow particles
        if random.random() < 0.2: 
             global particles
             particles.append(Particle(self.rect.centerx, self.rect.centery, color=NANOBOT_PARTICLE_COLOR, max_life=15, speed=1))


    def check_collision(self, game_map):
        points = [self.rect.midtop, self.rect.midbottom, self.rect.midleft, self.rect.midright]
        for px, py in points:
            tile_x = int(px // TILE_SIZE); tile_y = int(py // TILE_SIZE)
            if (0 <= tile_y < GRID_HEIGHT and 0 <= tile_x < GRID_WIDTH and game_map[tile_y][tile_x] == 1): return True
        return False
        
    def handle_input(self, keys, mouse_pos):
        self.velocity_x = 0; self.velocity_y = 0
        
        if keys[pygame.K_a]: self.velocity_x = -MOVE_SPEED
        if keys[pygame.K_d]: self.velocity_x = MOVE_SPEED
        if keys[pygame.K_w]: self.velocity_y = -MOVE_SPEED
        if keys[pygame.K_s]: self.velocity_y = MOVE_SPEED
        
        # Mouse movement input
        mouse_down = pygame.mouse.get_pressed()[0]
        if not (self.velocity_x or self.velocity_y) and mouse_down:
            dx = mouse_pos[0] - self.rect.centerx
            dy = mouse_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist > 10:
                self.velocity_x = (dx / dist) * MOVE_SPEED
                self.velocity_y = (dy / dist) * MOVE_SPEED

        # Update movement angle 
        if self.velocity_x or self.velocity_y:
            self.facing_angle = math.atan2(self.velocity_y, self.velocity_x)
        
    def fire_weapon(self, target_sentinel, bullets_group, all_sprites_group, can_fire=False):
        # Can only fire if not swirling, cooldown is 0, has ammo, and has a target
        if self.cooldown_timer == 0 and target_sentinel and self.ammo_count > 0 and can_fire and not self.is_swirling:
            
            self.ammo_count -= 1
            SOUND_LASER.play() # Play laser sound

            new_bullet = Bullet(self.rect.center, target_sentinel)
            bullets_group.add(new_bullet); all_sprites_group.add(new_bullet)
            
            if self.multi_shot_active and self.ammo_count > 0:
                self.ammo_count -= 1
                for _ in range(2):
                    offset_x = random.randint(-10, 10); offset_y = random.randint(-10, 10)
                    start_pos_offset = (self.rect.centerx + offset_x, self.rect.centery + offset_y)
                    new_bullet = Bullet(start_pos_offset, target_sentinel)
                    bullets_group.add(new_bullet); all_sprites_group.add(new_bullet)
            
            self.cooldown_timer = FIRE_COOLDOWN

    def draw(self, screen):
        center_x, center_y = self.rect.center
        body_color = NANOBOT_COLOR
        line_thickness = 3
        head_radius = 8
        body_length = 20
        limb_length = 15
        gun_length = 15 

        # Draw the Swirl-Shield
        if self.is_swirling:
            shield_radius = SHIELD_RADIUS
            
            s = pygame.Surface((shield_radius*2, shield_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, SWIRL_COLOR + (50,), (shield_radius, shield_radius), shield_radius)
            screen.blit(s, (center_x - shield_radius, center_y - shield_radius))
            
            # Draw the swirling lines 
            for i in range(4):
                angle = math.radians(self.swirl_angle + i * 90)
                swirl_x_outer = center_x + shield_radius * math.cos(angle)
                swirl_y_outer = center_y + shield_radius * math.sin(angle)
                swirl_x_inner = center_x + (shield_radius / 3) * math.cos(angle - math.pi/2)
                swirl_y_inner = center_y + (shield_radius / 3) * math.sin(angle - math.pi/2)
                
                pygame.draw.line(screen, SWIRL_COLOR, (swirl_x_inner, swirl_y_inner), (swirl_x_outer, swirl_y_outer), 4)

        # Draw Nanobot Body
        
        body_start = (center_x, center_y - head_radius)
        body_end = (center_x, center_y + body_length - head_radius)
        pygame.draw.line(screen, body_color, body_start, body_end, line_thickness)

        pygame.draw.circle(screen, body_color, body_start, head_radius, 0)
        pygame.draw.circle(screen, (0, 0, 0), body_start, head_radius, 1)

        # Legs 
        leg_angle_offset = math.pi / 4
        leg_end_x1 = body_end[0] + limb_length * math.cos(self.facing_angle + leg_angle_offset)
        leg_end_y1 = body_end[1] + limb_length * math.sin(self.facing_angle + leg_angle_offset)
        pygame.draw.line(screen, body_color, body_end, (leg_end_x1, leg_end_y1), line_thickness)

        leg_end_x2 = body_end[0] + limb_length * math.cos(self.facing_angle - leg_angle_offset)
        leg_end_y2 = body_end[1] + limb_length * math.sin(self.facing_angle - leg_angle_offset)
        pygame.draw.line(screen, body_color, body_end, (leg_end_x2, leg_end_y2), line_thickness)

        # Right Arm (Gun Arm) 
        arm_end_x2 = body_start[0] + limb_length * math.cos(self.gun_angle)
        arm_end_y2 = body_start[1] + limb_length * math.sin(self.gun_angle)
        pygame.draw.line(screen, body_color, body_start, (arm_end_x2, arm_end_y2), line_thickness)

        gun_end_x = arm_end_x2 + gun_length * math.cos(self.gun_angle)
        gun_end_y = arm_end_y2 + gun_length * math.sin(self.gun_angle)
        pygame.draw.line(screen, BULLET_COLOR, (arm_end_x2, arm_end_y2), (gun_end_x, gun_end_y), 4)

        # Left Arm 
        arm_angle_left = self.facing_angle + math.pi / 2.5
        arm_end_x1 = body_start[0] + limb_length * math.cos(arm_angle_left)
        arm_end_y1 = body_start[1] + limb_length * math.sin(arm_angle_left)
        pygame.draw.line(screen, body_color, body_start, (arm_end_x1, arm_end_y1), line_thickness)


        # Draw Shield Overlay if active (The smaller temporary powerup shield)
        if self.shield_active:
             pygame.draw.circle(screen, SHIELD_COLOR + (100,), self.rect.center, 20, 0)

def calculate_visible_tiles(nanobot_center, game_map):
    visible_tiles = set()
    nx, ny = nanobot_center
    for ty in range(GRID_HEIGHT):
        for tx in range(GRID_WIDTH):
            center_x = tx * TILE_SIZE + TILE_SIZE // 2
            center_y = ty * TILE_SIZE + TILE_SIZE // 2
            if math.hypot(center_x - nx, center_y - ny) < LIGHT_RADIUS * 1.5:
                 if game_map[ty][tx] == 0: visible_tiles.add((tx, ty))
                 if game_map[ty][tx] == 1 and math.hypot(center_x - nx, center_y - ny) < TILE_SIZE * 1.5: visible_tiles.add((tx, ty))
    return visible_tiles

def apply_lighting(screen, nanobot, visible_tiles):
    dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
    dark_overlay.fill((0, 0, 0, 255)) 

    for tx, ty in visible_tiles:
        rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        s = pygame.Surface((TILE_SIZE, TILE_SIZE)).convert_alpha()
        s.fill((40, 40, 40, 180)) 
        dark_overlay.blit(s, rect.topleft)

    light_source = pygame.Surface((LIGHT_RADIUS * 2, LIGHT_RADIUS * 2), pygame.SRCALPHA)
    center = (LIGHT_RADIUS, LIGHT_RADIUS)
    
    pygame.draw.circle(light_source, (50, 100, 200, 50), center, LIGHT_RADIUS) 
    pygame.draw.circle(light_source, (150, 200, 255, 100), center, LIGHT_RADIUS * 0.7) 
    pygame.draw.circle(light_source, (255, 255, 255, 180), center, LIGHT_RADIUS * 0.3)

    light_pos = (nanobot.rect.centerx - LIGHT_RADIUS, nanobot.rect.centery - LIGHT_RADIUS)
    dark_overlay.blit(light_source, light_pos, special_flags=pygame.BLEND_RGBA_MIN)
    screen.blit(dark_overlay, (0, 0))

def draw_crosshair(screen):
    center_x = AIM_POINT[0]
    center_y = AIM_POINT[1]
    size = 10
    width = 2
    
    pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x - size, center_y), (center_x - width, center_y), width)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x + width, center_y), (center_x + size, center_y), width)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x, center_y - size), (center_x, center_y - width), width)
    pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x, center_y + width), (center_x, center_y + size), width)
    pygame.draw.circle(screen, CROSSHAIR_COLOR, (center_x, center_y), width)

def draw_level_menu(screen, current_selection):
    screen.fill(BLACK)
    
    title = font_large.render("CELLULAR SCAPE", True, CORE_COLOR)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
    
    subtitle = font.render("--- Select Mission Level (1-10) ---", True, (200, 200, 200))
    screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 130))
    
    levels_per_row = 5
    start_y = 200
    button_width = 80
    button_height = 50
    padding = 20
    
    total_width = levels_per_row * button_width + (levels_per_row - 1) * padding
    start_x = SCREEN_WIDTH // 2 - total_width // 2

    for i in range(1, TOTAL_LEVELS + 1):
        row = (i - 1) // levels_per_row
        col = (i - 1) % levels_per_row
        
        x = start_x + col * (button_width + padding)
        y = start_y + row * (button_height + padding)
        
        rect = pygame.Rect(x, y, button_width, button_height)
        
        color = MENU_SELECT_COLOR if i == current_selection else WALL_COLOR
        text_color = BLACK if i == current_selection else (255, 255, 255)
        
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        
        level_text = font.render(str(i), True, text_color)
        screen.blit(level_text, (rect.centerx - level_text.get_width() // 2, rect.centery - level_text.get_height() // 2))
        
        
    start_info = font.render("Press ENTER or Tap to start the selected level.", True, (150, 150, 255))
    screen.blit(start_info, (SCREEN_WIDTH // 2 - start_info.get_width() // 2, SCREEN_HEIGHT - 50))

def draw_hud(screen, nanobot, current_cores):
    # Health Bar
    health_bar_width = 150
    health_bar_height = 20
    health_ratio = nanobot.current_health / nanobot.max_health
    
    health_rect = pygame.Rect(20, 20, health_bar_width, health_bar_height)
    fill_rect = pygame.Rect(20, 20, health_bar_width * health_ratio, health_bar_height)
    
    pygame.draw.rect(screen, BLACK, health_rect, 0)
    pygame.draw.rect(screen, HEALTH_COLOR, fill_rect, 0)
    pygame.draw.rect(screen, (255, 255, 255), health_rect, 2)
    
    health_text = font.render(f"HP: {nanobot.current_health}", True, (255, 255, 255))
    screen.blit(health_text, (health_rect.x + 5, health_rect.y + 1))
    
    # Ammo Counter
    ammo_text = font.render(f"AMMO: {int(nanobot.ammo_count)}", True, AMMO_COLOR)
    screen.blit(ammo_text, (20, 50))
    
    # Core Counter
    core_text = font.render(f"CORES: {current_cores} / {CORES_NEEDED}", True, CORE_COLOR)
    screen.blit(core_text, (SCREEN_WIDTH - core_text.get_width() - 20, 20))
    
    # Level Counter
    level_text = font.render(f"LEVEL {current_level} / {TOTAL_LEVELS}", True, DOOR_COLOR)
    screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 50))
    
    # Status Effects
    status_y = 80
    if nanobot.shield_active:
        shield_text = font.render(f"SHIELD: {nanobot.shield_timer // 60}s", True, SHIELD_COLOR)
        screen.blit(shield_text, (20, status_y)); status_y += 30
    if nanobot.multi_shot_active:
        multi_text = font.render(f"MULTISHOT: {nanobot.multi_shot_timer // 60}s", True, BULLET_COLOR)
        screen.blit(multi_text, (20, status_y)); status_y += 30
    if nanobot.is_swirling:
        swirl_text = font.render("SWIRL-SHIELD ACTIVE", True, SWIRL_COLOR)
        screen.blit(swirl_text, (SCREEN_WIDTH // 2 - swirl_text.get_width() // 2, SCREEN_HEIGHT - 30))

# --- 6. Game State & Initialization ---
sentinels = pygame.sprite.Group()
bullets = pygame.sprite.Group()
crates = pygame.sprite.Group()
cores = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
door = None

def setup_level(level_num):
    global nanobot, current_cores
    
    game_map, nanobot_start_tile, enemies_pos, crates_pos, cores_pos, door_tile = generate_level(level_num)
    
    # Clear all groups
    sentinels.empty(); bullets.empty(); crates.empty(); cores.empty(); all_sprites.empty();
    
    global nanobot
    if nanobot is None or level_num == 1:
        nanobot = Nanobot(nanobot_start_tile)
    else:
        # Reset Nanobot position and basic stats for new level
        nanobot.rect.centerx = nanobot_start_tile[0] * TILE_SIZE + TILE_SIZE // 2
        nanobot.rect.centery = nanobot_start_tile[1] * TILE_SIZE + TILE_SIZE // 2
        # Keep accumulated health/ammo from previous level
        nanobot.current_health = min(nanobot.max_health, nanobot.current_health + 20) # Small health bonus on level start
        nanobot.ammo_count = min(999, nanobot.ammo_count + 50) # Small ammo bonus
        nanobot.shield_active = False; nanobot.multi_shot_active = False
        nanobot.shield_timer = 0; nanobot.multi_shot_timer = 0
        nanobot.is_swirling = False 
        
        # Stop swirl sound on level load if it was somehow playing
        global SWIRL_CHANNEL
        if SWIRL_CHANNEL.get_busy(): SWIRL_CHANNEL.stop()


    for pos in enemies_pos: sentinels.add(Sentinel(pos))
    for pos in crates_pos: crates.add(Crate(pos))
    for pos in cores_pos: cores.add(PowerCore(pos))
        
    global door
    door = LevelDoor(door_tile)
    
    all_sprites.add(nanobot, sentinels, crates, cores, door) 
    current_cores = 0
    
    return game_map, nanobot

# Game State Variables
GAME_STATE = 'MENU'
current_level = 1
selected_level = 1
nanobot = None
game_map = None
particles = []
current_cores = 0
last_mouse_click = (False, False, False)

running = True
music_playing = False

# --- 7. Main Game Loop ---
while running:
    
    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()
    
    # Check if we should activate the Swirl-Shield Mode
    activate_swirl = keys[pygame.K_SPACE] and nanobot and nanobot.ammo_count > 0 
    
    # 7.1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if GAME_STATE == 'MENU':
            if not music_playing:
                 pygame.mixer.music.play(-1) # Start BG music loop
                 music_playing = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_LEFT:
                    selected_level = max(1, selected_level - 1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT:
                    selected_level = min(TOTAL_LEVELS, selected_level + 1)
                elif event.key == pygame.K_RETURN:
                    current_level = selected_level
                    game_map, nanobot = setup_level(current_level)
                    GAME_STATE = 'PLAYING'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                levels_per_row = 5; start_y = 200; button_width = 80; button_height = 50; padding = 20
                total_width = levels_per_row * button_width + (levels_per_row - 1) * padding
                start_x = SCREEN_WIDTH // 2 - total_width // 2
                
                for i in range(1, TOTAL_LEVELS + 1):
                    row = (i - 1) // levels_per_row; col = (i - 1) % levels_per_row
                    x = start_x + col * (button_width + padding)
                    y = start_y + row * (button_height + padding)
                    rect = pygame.Rect(x, y, button_width, button_height)
                    
                    if rect.collidepoint(event.pos):
                        selected_level = i
                        current_level = selected_level
                        game_map, nanobot = setup_level(current_level)
                        GAME_STATE = 'PLAYING'
                        break
                    
        elif GAME_STATE == 'GAME_OVER' or GAME_STATE == 'GAME_WIN':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                GAME_STATE = 'MENU'
                selected_level = 1
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                GAME_STATE = 'MENU'
                selected_level = 1
    
    last_mouse_click = mouse_click

    if GAME_STATE == 'MENU':
        draw_level_menu(screen, selected_level)
        pygame.display.flip()
        clock.tick(FPS)
        continue

    if GAME_STATE == 'GAME_OVER' or GAME_STATE == 'GAME_WIN':
        if music_playing:
            pygame.mixer.music.stop()
            music_playing = False
        
        # Play Game Over/Win sound once
        if GAME_STATE == 'GAME_OVER' and not SOUND_GAMEOVER.get_busy():
            SOUND_GAMEOVER.play()
        elif GAME_STATE == 'GAME_WIN' and not SOUND_WIN.get_busy():
            SOUND_WIN.play()
            
        # Stop swirl sound if it was active
        if SWIRL_CHANNEL.get_busy(): SWIRL_CHANNEL.stop()

        screen.fill(BLACK)
        message = "SYSTEM FAILURE (GAME OVER)" if GAME_STATE == 'GAME_OVER' else "VICTORY ACHIEVED!"
        color = SENTINEL_COLOR if GAME_STATE == 'GAME_OVER' else CORE_COLOR
        text = font_large.render(message, True, color)
        restart_text = font.render("Press SPACE or Tap to return to Level Select", True, (200, 200, 200))
        
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        
        pygame.display.flip()
        clock.tick(10)
        continue

    # --- GAME_STATE == 'PLAYING' ---
    if not music_playing:
         pygame.mixer.music.play(-1) 
         music_playing = True

    # --- Input Handler ---
    nanobot.handle_input(keys, mouse_pos)
    
    # 1. Swirl-Shield Logic (Space bar overrides firing)
    nanobot.is_swirling = activate_swirl
    
    # 2. Targeting and Firing Logic
    target_enemy = None
    min_dist = float('inf')
    for sentinel in sentinels:
        dist = math.hypot(nanobot.rect.centerx - sentinel.rect.centerx, nanobot.rect.centery - sentinel.rect.centery)
        if dist < min_dist and dist < 400: 
            min_dist = dist
            target_enemy = sentinel
            
    # Fire only if mouse button is down AND we are not using the swirl shield
    if mouse_click[0] and not nanobot.is_swirling:
        nanobot.fire_weapon(target_enemy, bullets, all_sprites, can_fire=True) 

    # 3. Update all sprites
    nanobot.update(game_map)
    sentinels.update(nanobot, game_map)
    bullets.update()
    
    # Particle updates
    particles = [p for p in particles if not p.update()]
    
    # 4. Collision Checks
    
    # Check for Sentinel collision with Nanobot
    hit_sentinels = pygame.sprite.spritecollide(nanobot, sentinels, False)
    for sentinel in hit_sentinels:
        if nanobot.is_swirling:
            # Shield is active: Destroy sentinel, Nanobot takes NO damage
            sentinel.kill()
            SOUND_EXPLOSION.play()
            for _ in range(30): particles.append(Particle(sentinel.rect.centerx, sentinel.rect.centery, color=SWIRL_COLOR, max_life=40, speed=4))
        elif nanobot.shield_active:
            # Power-up shield is active: Take NO damage, use up power-up shield
            nanobot.shield_timer = 0; nanobot.shield_active = False
            sentinel.kill()
            SOUND_EXPLOSION.play()
        else:
            # Take damage normally
            nanobot.current_health -= 10
            SOUND_HIT.play()
            if nanobot.current_health <= 0: GAME_STATE = 'GAME_OVER'
            sentinel.kill()

    # Bullet collisions (Bullets hit and kill bad guys)
    for bullet in bullets:
        hit_sentinels = pygame.sprite.spritecollide(bullet, sentinels, True) 
        if hit_sentinels:
            bullet.kill()
            SOUND_HIT.play() 
            for _ in range(20): 
                particles.append(Particle(bullet.rect.centerx, bullet.rect.centery, color=BULLET_COLOR, max_life=50, speed=3))
        
        # Bullets also hit crates
        hit_crates = pygame.sprite.spritecollide(bullet, crates, False) 
        if hit_crates:
            bullet.kill()
            SOUND_HIT.play()
            for crate in hit_crates:
                powerup = crate.hit(particles)
                if powerup: all_sprites.add(powerup) 

    # Core collection
    collected_cores = pygame.sprite.spritecollide(nanobot, cores, True)
    if collected_cores:
        current_cores += len(collected_cores)
        SOUND_POWERUP.play()

    # PowerUp collection
    collected_powerups = pygame.sprite.spritecollide(nanobot, all_sprites, True)
    for item in collected_powerups:
        if isinstance(item, PowerUp) or isinstance(item, AmmoPowerUp) or isinstance(item, HealthPowerUp): 
             nanobot.apply_powerup(item.type)
            

    if current_cores >= CORES_NEEDED and pygame.sprite.collide_rect(nanobot, door):
        if current_level < TOTAL_LEVELS:
            SOUND_WIN.play() # Use the win sound for leveling up too
            current_level += 1
            game_map, nanobot = setup_level(current_level)
            # Stop swirl loop manually on level transition
            if SWIRL_CHANNEL.get_busy(): SWIRL_CHANNEL.stop()
        else: GAME_STATE = 'GAME_WIN'
            
    # 5. Visual Updates
    screen.fill(BLACK)

    # Draw Map
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if game_map[y][x] == 1:
                pygame.draw.rect(screen, WALL_COLOR, rect)
            else:
                pygame.draw.rect(screen, FLOOR_COLOR, rect)

    # Draw Door (FIXED: Calls the new .draw() method)
    door.draw(screen)

    # Draw Entities
    crates.draw(screen)
    cores.draw(screen)
    bullets.draw(screen)
    sentinels.draw(screen)

    # Draw Nanobot last (so limbs are on top)
    nanobot.draw(screen)
    
    # Draw Particles
    for p in particles: p.draw(screen)
    
    # Lighting and Fog of War
    visible_tiles = calculate_visible_tiles(nanobot.rect.center, game_map)
    apply_lighting(screen, nanobot, visible_tiles)

    # Draw UI/HUD
    draw_crosshair(screen)
    draw_hud(screen, nanobot, current_cores)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
