import pygame
import random
import sys
import time
import json
import os
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---- INIT ----
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 1000, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Treasure Hunter")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("comicsans", 30)
FONT_SMALL = pygame.font.SysFont("comicsans", 20)

# ---- COLORS ----
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (200, 200, 50)
GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)
DARK_RED = (150, 0, 0)

# ---- GAME VARIABLES ----
player_speed = 6
slow_speed = 3
item_size = 50
obstacle_size = 50
highscore_file = os.path.join(BASE_DIR, "highscore.json")
achievements_file = os.path.join(BASE_DIR, "achievements.json")
highscore = 0
achievement_scroll_offset = 0

# ---- VISUAL EFFECTS ----
screen_shake = 0
screen_flash = 0
flash_color = (255, 255, 255)
particles = []

# ---- BOSS HEALTH SYSTEM ----
boss_player_health = 3
max_boss_player_health = 3
boss_hearts = []

# ---- LOAD SPRITES ----
background_img = pygame.image.load(
    os.path.join(BASE_DIR, "sprites", "sand_sprite.jpg")
).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

cactus_img = pygame.image.load(
    os.path.join(BASE_DIR, "sprites", "cactus_sprite.png")
).convert_alpha()
cactus_img = pygame.transform.scale(cactus_img, (obstacle_size, obstacle_size))

coin_img = pygame.image.load(
    os.path.join(BASE_DIR, "sprites", "coin_sprite.png")
).convert_alpha()
coin_img = pygame.transform.scale(coin_img, (item_size, item_size))

player_sheet = pygame.image.load(
    os.path.join(BASE_DIR, "sprites", "player_walk.png")
).convert_alpha()

player_shadow = pygame.image.load(
    os.path.join(BASE_DIR, "sprites", "player_shadow.png")
).convert_alpha()

# ---- Load heart sprite (create a simple one if not available) ----
heart_path = os.path.join(BASE_DIR, "sprites", "heart_sprite.png")
try:
    heart_img = pygame.image.load(heart_path).convert_alpha()
    heart_img = pygame.transform.scale(heart_img, (30, 30))
except:
    heart_img = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.polygon(heart_img, RED, [
        (15, 5), (20, 10), (25, 5), (20, 15),
        (15, 25), (10, 15), (5, 5), (10, 10)
    ])

# ---- LOAD SOUNDS ----
coin_sound = pygame.mixer.Sound(
    os.path.join(BASE_DIR, "sounds", "coin.mp3")
)

death_path = os.path.join(BASE_DIR, "sounds", "death.mp3")
death_sound = pygame.mixer.Sound(death_path) if os.path.exists(death_path) else None

bg_music = os.path.join(BASE_DIR, "sounds", "background_song.mp3")

# ---- BACKGROUND MUSIC ----
pygame.mixer.music.load(bg_music)
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# ---- BOSS SPRITE LOADING ----
boss_sprite_path = os.path.join(BASE_DIR, "sprites", "boss_sprite.png")
try:
    boss_idle_sheet = pygame.image.load(boss_sprite_path).convert_alpha()
    print(f"Successfully loaded boss sprite sheet: {boss_idle_sheet.get_width()}x{boss_idle_sheet.get_height()}")
except Exception as e:
    boss_idle_sheet = None
    print(f"Could not load boss sprite sheet: {e}. Using placeholder animation.")


# ---- SCREENS ----
MENU, TIME_SELECT, PLAYING, PAUSED, GAME_OVER, TIME_OVER, NEW_HIGHSCORE, CONTROLS, HIGHSCORES, DIFFICULTY_SELECT, ACHIEVEMENTS, TUTORIAL = (
    "menu", "time_select", "playing", "paused", "game_over", "time_over", "new_highscore", "controls", "highscores", "difficulty_select", "achievements", "tutorial"
)
screen = MENU

# ---- BACKGROUND MUSIC ----
pygame.mixer.music.load(bg_music)
pygame.mixer.music.set_volume(0.5)  
pygame.mixer.music.play(-1)

# ---- DIFFICULTY SETTINGS ----
difficulty_settings = {
    "easy": {"player_speed": 7, "obstacle_speed": 2, "spawn_rate": 0.5},
    "normal": {"player_speed": 6, "obstacle_speed": 3, "spawn_rate": 1},
    "hard": {"player_speed": 5, "obstacle_speed": 4, "spawn_rate": 1.5},
    "insane": {"player_speed": 4, "obstacle_speed": 5, "spawn_rate": 2}
}
current_difficulty = "normal"

# ---- ACHIEVEMENTS ----
default_achievements = {
    "first_blood": {"name": "First Blood", "desc": "Collect first coin", "unlocked": False},
    "combo_master": {"name": "Combo Master", "desc": "Get 10x combo", "unlocked": False},
    "speed_demon": {"name": "Speed Demon", "desc": "Complete level in 30s", "unlocked": False},
    "perfectionist": {"name": "Perfectionist", "desc": "Complete level without touching obstacles", "unlocked": False},
    "boss_slayer": {"name": "Boss Slayer", "desc": "Defeat a boss in endless mode", "unlocked": False},
    "combo_god": {"name": "Combo God", "desc": "Get 20x combo", "unlocked": False},
    "coin_collector": {"name": "Coin Collector", "desc": "Collect 100 coins total", "unlocked": False},
    "survivor": {"name": "Survivor", "desc": "Reach level 10 in endless mode", "unlocked": False},
    "time_warrior": {"name": "Time Warrior", "desc": "Complete 5-minute time attack", "unlocked": False},
    "difficulty_master": {"name": "Difficulty Master", "desc": "Complete game on insane difficulty", "unlocked": False}
}

# Load achievements from file
if os.path.exists(achievements_file):
    with open(achievements_file, "r") as f:
        achievements = json.load(f)
    # Ensure all default achievements exist
    for key, value in default_achievements.items():
        if key not in achievements:
            achievements[key] = value
else:
    achievements = default_achievements.copy()

# Track achievement progress
total_coins_collected = 0

# ---- BOSS ANIMATION SYSTEM ----
class BossAnimation:
    def __init__(self):
        self.state = "idle"  # idle, attack, hurt, defeated
        self.frame_index = 0
        self.animation_speed = 0.15  # Controls animation speed
        self.last_update = time.time()
        self.idle_frames = []
        self.attack_frames = []
        self.hurt_frames = []
        self.defeated_frames = []
        
        # Load animation frames
        self.load_frames()
    
    def load_frames(self):
        # Load idle frames from sprite sheet (4 frames, 71x81 each, side by side)
        if boss_idle_sheet:
            try:
                sheet_width = boss_idle_sheet.get_width()
                sheet_height = boss_idle_sheet.get_height()
                
                print(f"Processing sprite sheet: {sheet_width}x{sheet_height}")
                print(f"Expected frame size: 71x81 pixels")
                
                # Calculate how many 81x71 frames we have (81 wide, 71 tall)
                frame_count = sheet_width // 81  # Each frame is 81 pixels wide
                print(f"Found approximately {frame_count} frames at 81px width")
                
                # Make sure we don't exceed available frames
                frame_count = min(frame_count, 4)  # Max 4 frames for safety
                
                for i in range(frame_count):
                    try:
                        # Extract each 81x71 frame
                        frame = boss_idle_sheet.subsurface((i * 81, 0, 81, 71))
                        # Scale up for better visibility - maintain aspect ratio
                        # Scale to approximately 150px tall (71 -> ~150)
                        scale_factor = 150 / 71
                        new_width = int(81 * scale_factor)
                        new_height = int(71 * scale_factor)
                        frame = pygame.transform.scale(frame, (new_width, new_height))
                        self.idle_frames.append(frame)
                        print(f"  Loaded frame {i}: 81x71 -> {new_width}x{new_height}")
                    except Exception as e:
                        print(f"  Error loading frame {i}: {e}")
                        # Add placeholder for missing frame
                        placeholder = pygame.Surface((162, 150), pygame.SRCALPHA)
                        pygame.draw.circle(placeholder, (100 + i*40, 0, 200), (81, 75), 70)
                        self.idle_frames.append(placeholder)
                
                print(f"Successfully loaded {len(self.idle_frames)} boss frames")
                
            except Exception as e:
                print(f"Error processing sprite sheet: {e}")
                self.create_placeholder_frames()
        else:
            print("No boss sprite sheet available, creating placeholder frames")
            self.create_placeholder_frames()
        
        # Create attack and hurt frames by tinting idle frames
        for frame in self.idle_frames:
            # Attack frames (red tint)
            attack_frame = frame.copy()
            red_overlay = pygame.Surface((frame.get_width(), frame.get_height()), pygame.SRCALPHA)
            red_overlay.fill((255, 50, 50, 80))
            attack_frame.blit(red_overlay, (0, 0))
            self.attack_frames.append(attack_frame)
            
            # Hurt frames (blue tint)
            hurt_frame = frame.copy()
            blue_overlay = pygame.Surface((frame.get_width(), frame.get_height()), pygame.SRCALPHA)
            blue_overlay.fill((100, 100, 255, 80))
            hurt_frame.blit(blue_overlay, (0, 0))
            self.hurt_frames.append(hurt_frame)
            
            # Defeated frames (dark tint)
            defeated_frame = frame.copy()
            dark_overlay = pygame.Surface((frame.get_width(), frame.get_height()), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 150))
            defeated_frame.blit(dark_overlay, (0, 0))
            self.defeated_frames.append(defeated_frame)
    
    def create_placeholder_frames(self):
        # Simple placeholder frames scaled to match 81x71 -> 162x150
        for i in range(4):
            frame = pygame.Surface((162, 150), pygame.SRCALPHA)
            # Simple boss shape
            pygame.draw.circle(frame, (180, 0, 255), (81, 75), 70)
            pygame.draw.circle(frame, (150, 0, 200), (81, 75), 60)
            
            # Animated eyes
            eye_offset = 2 * math.sin(i * math.pi / 2)
            pygame.draw.circle(frame, WHITE, (65, 65), 12)
            pygame.draw.circle(frame, WHITE, (97, 65), 12)
            pygame.draw.circle(frame, BLACK, (65 + eye_offset, 65), 6)
            pygame.draw.circle(frame, BLACK, (97 + eye_offset, 65), 6)
            
            self.idle_frames.append(frame)
        
        # Create attack and hurt frames from idle
        self.attack_frames = [frame.copy() for frame in self.idle_frames]
        self.hurt_frames = [frame.copy() for frame in self.idle_frames]
        self.defeated_frames = [frame.copy() for frame in self.idle_frames]
    
    def update(self, state):
        current_time = time.time()
        
        # Change state if needed
        if state != self.state:
            self.state = state
            self.frame_index = 0
        
        # Update animation frame
        if current_time - self.last_update > self.animation_speed:
            self.last_update = current_time
            
            frames = self.get_current_frames()
            if frames:
                self.frame_index = (self.frame_index + 1) % len(frames)
    
    def get_current_frames(self):
        if self.state == "idle":
            return self.idle_frames
        elif self.state == "attack":
            return self.attack_frames
        elif self.state == "hurt":
            return self.hurt_frames
        elif self.state == "defeated":
            return self.defeated_frames
        return self.idle_frames
    
    def get_current_frame(self):
        frames = self.get_current_frames()
        if frames and self.frame_index < len(frames):
            return frames[self.frame_index]
        return self.idle_frames[0] if self.idle_frames else None

# Update Boss class for variable sprite sizes
class Boss:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.animation = BossAnimation()
        
        # Get size from first animation frame
        first_frame = self.animation.get_current_frame()
        if first_frame:
            self.width = first_frame.get_width()
            self.height = first_frame.get_height()
        else:
            self.width = 162  # Default if no frames
            self.height = 150
            
        self.hp = 100
        self.max_hp = 100
        self.attack_timer = 0
        self.attack_interval = 2.0
        self.attack_pattern = 0
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                               self.width, self.height)
        self.projectiles = []
        self.rotation = 0
        self.last_coin_spawn = 0
        self.coin_spawn_interval = 2.0
        self.hearts_spawned = False
        self.last_hit_time = 0
        self.hurt_duration = 0.3
        self.is_attacking = False
        self.attack_animation_duration = 0.5
        self.attack_animation_timer = 0
        self.bob_offset = 0
        self.bob_speed = 0.05
        self.bob_amount = 3
        print(f"Boss created with size {self.width}x{self.height}")
        
    def update(self, dt, player_rect):
        # Update bobbing animation
        self.bob_offset = math.sin(time.time() * self.bob_speed * 10) * self.bob_amount
        
        # Slow rotation
        self.rotation += 0.1
        
        self.attack_timer += dt
        self.attack_animation_timer = max(0, self.attack_animation_timer - dt)
        
        # Update boss state
        current_time = time.time()
        
        if current_time - self.last_hit_time < self.hurt_duration:
            state = "hurt"
            self.is_attacking = False
        elif self.attack_animation_timer > 0:
            state = "attack"
            self.is_attacking = True
        else:
            state = "idle"
            self.is_attacking = False
        
        # Check if it's time to attack
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 3
            self.attack(player_rect)
            self.attack_animation_timer = self.attack_animation_duration
            state = "attack"
        
        # Update animation
        self.animation.update(state)
        
        # Update collision rect position
        self.rect.center = (int(self.x), int(self.y + self.bob_offset))
            
        # Update projectiles
        for proj in self.projectiles[:]:
            proj[0] += proj[2] * 5 * dt * 60
            proj[1] += proj[3] * 5 * dt * 60
            
            # Remove if out of bounds
            if (proj[0] < -50 or proj[0] > WIDTH + 50 or 
                proj[1] < -50 or proj[1] > HEIGHT + 50):
                if proj in self.projectiles:
                    self.projectiles.remove(proj)
    
    def take_damage(self, amount):
        self.hp -= amount
        self.last_hit_time = time.time()
                    
    def try_spawn_coin(self, items, player_rect):
        current_time = time.time()
        if current_time - self.last_coin_spawn >= self.coin_spawn_interval:
            self.last_coin_spawn = current_time
            
            # Spawn coins away from boss
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(100, 300)
                x = self.x + math.cos(angle) * distance
                y = self.y + math.sin(angle) * distance
                
                # Keep within screen
                x = max(item_size, min(WIDTH - item_size, x))
                y = max(item_size, min(HEIGHT - item_size, y))
                
                new_coin = pygame.Rect(x, y, item_size, item_size)
                
                # Don't spawn inside boss
                if (not new_coin.colliderect(self.rect) and 
                    not any(new_coin.colliderect(coin) for coin in items)):
                    items.append(new_coin)
                    break
    
    def spawn_hearts(self):
        global boss_hearts
        boss_hearts = []
        for _ in range(2):
            for _ in range(50):  # Try multiple positions
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(150, 400)
                x = self.x + math.cos(angle) * distance
                y = self.y + math.sin(angle) * distance
                
                x = max(15, min(WIDTH - 15, x))
                y = max(15, min(HEIGHT - 15, y))
                
                heart_rect = pygame.Rect(x - 15, y - 15, 30, 30)
                
                if not heart_rect.colliderect(self.rect):
                    boss_hearts.append({
                        'rect': heart_rect,
                        'x': x,
                        'y': y,
                        'collected': False
                    })
                    break
                    
    def attack(self, player_rect):
        if self.attack_pattern == 0:  # Circle
            for i in range(8):
                angle = (i / 8) * 2 * math.pi
                dx = math.cos(angle)
                dy = math.sin(angle)
                self.projectiles.append([self.x, self.y, dx, dy])
        elif self.attack_pattern == 1:  # Targeted
            dx = player_rect.centerx - self.x
            dy = player_rect.centery - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                dx /= dist
                dy /= dist
            self.projectiles.append([self.x, self.y, dx, dy])
        else:  # Spiral
            for i in range(4):
                angle = self.rotation * 0.0174533 + (i * math.pi / 2)
                dx = math.cos(angle)
                dy = math.sin(angle)
                self.projectiles.append([self.x, self.y, dx, dy])
                
    def draw(self, win):
        # Get current animation frame
        frame = self.animation.get_current_frame()
        
        if frame:
            # Calculate position with bobbing
            draw_x = self.x - frame.get_width() // 2
            draw_y = self.y - frame.get_height() // 2 + self.bob_offset
            
            # Apply slight rotation only during attack
            if self.animation.state == "attack":
                # More dramatic rotation during attack
                attack_rotation = self.rotation * 2
                rotated_frame = pygame.transform.rotate(frame, attack_rotation)
                rot_rect = rotated_frame.get_rect(center=(self.x, self.y + self.bob_offset))
                win.blit(rotated_frame, rot_rect)
            else:
                # Gentle rotation for idle/hurt states
                rotated_frame = pygame.transform.rotate(frame, self.rotation * 0.5)
                rot_rect = rotated_frame.get_rect(center=(self.x, self.y + self.bob_offset))
                win.blit(rotated_frame, rot_rect)
            
            # Visual effects based on state
            if self.animation.state == "attack":
                # Add attack glow effect
                glow_size = max(frame.get_width(), frame.get_height()) + 20
                glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                # Pulsing glow
                pulse = abs(math.sin(time.time() * 8)) * 30 + 70
                pygame.draw.circle(glow, (255, 100, 0, int(pulse)), 
                                 (glow_size // 2, glow_size // 2), 
                                 glow_size // 2)
                win.blit(glow, (self.x - glow_size // 2, 
                              self.y - glow_size // 2 + self.bob_offset))
            
            elif self.animation.state == "hurt":
                # Hurt flash effect
                current_time = time.time()
                time_since_hit = current_time - self.last_hit_time
                if time_since_hit < self.hurt_duration:
                    flash_alpha = int(150 * (1 - time_since_hit / self.hurt_duration))
                    flash = pygame.Surface((frame.get_width(), frame.get_height()), pygame.SRCALPHA)
                    pygame.draw.circle(flash, (255, 255, 255, flash_alpha), 
                                     (frame.get_width() // 2, frame.get_height() // 2), 
                                     min(frame.get_width(), frame.get_height()) // 2)
                    win.blit(flash, (draw_x, draw_y))
        
        # Draw health bar
        bar_width = 180
        bar_height = 15
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.height//2 - 30 + self.bob_offset  # Position above boss
        
        # Background
        pygame.draw.rect(win, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        # Health
        health_width = (self.hp / self.max_hp) * bar_width
        if self.hp > 50:
            health_color = (0, 255, 0)
        elif self.hp > 20:
            health_color = (255, 255, 0)
        else:
            health_color = (255, 0, 0)
        pygame.draw.rect(win, health_color, (bar_x, bar_y, health_width, bar_height), border_radius=3)
        # Border
        pygame.draw.rect(win, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=3)
        
        # Pulsing effect when low health
        if self.hp < 30:
            pulse = abs(math.sin(time.time() * 5)) * 50 + 50
            pulse_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
            pygame.draw.rect(pulse_surface, (255, 255, 255, int(pulse)), 
                           (0, 0, bar_width, bar_height), 3, border_radius=3)
            win.blit(pulse_surface, (bar_x, bar_y))
        
        # Draw projectiles
        for proj in self.projectiles:
            pygame.draw.circle(win, (255, 200, 200), (int(proj[0]), int(proj[1])), 10)
            pygame.draw.circle(win, RED, (int(proj[0]), int(proj[1])), 6)

# ---- PARTICLE SYSTEM ----
class Particle:
    def __init__(self, x, y, color, velocity, size, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vy += 0.1  # Gravity
        
    def draw(self, win):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = list(self.color)
        color.append(alpha)
        pygame.draw.circle(win, self.color[:3], (int(self.x), int(self.y)), 
                          int(self.size * (self.lifetime / self.max_lifetime)))

def create_particles(x, y, color, count=10):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        size = random.uniform(2, 8)
        lifetime = random.randint(20, 40)
        particles.append(Particle(x, y, color, (vx, vy), size, lifetime))

def create_coin_particles(x, y):
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        size = random.uniform(3, 6)
        lifetime = random.randint(30, 50)
        color = (random.randint(200, 255), random.randint(150, 200), 0)
        particles.append(Particle(x + 25, y + 25, color, (vx, vy), size, lifetime))

# ------------------------------------------------------------
#                        PLAYER CLASS
# ------------------------------------------------------------
class Player:
    def __init__(self, x, y, sprite_sheet, shadow_sprite, scale=3):
        self.x = x
        self.y = y
        self.scale = scale

        # Frames uit sheet snijden
        self.frames = []
        frame_width = 100
        frame_height = 100

        for i in range(8):
            frame = sprite_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            frame = pygame.transform.scale(
                frame, (frame_width * scale, frame_height * scale)
            )
            self.frames.append(frame)

        # Shadow opschalen (maar minder dan speler)
        self.shadow = pygame.transform.scale(
            shadow_sprite, (shadow_sprite.get_width() * scale, shadow_sprite.get_height() * scale)
        )

        # Animatie
        self.anim_index = 0
        self.anim_speed = 0.2

        self.dx = 0
        self.dy = 0
        self.facing_left = False

        self.rect = pygame.Rect(self.x, self.y, 8 * scale, 17 * scale)

    def update(self, keys, speed):
        self.dx = 0
        self.dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.dx = -speed
            self.facing_left = True

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.dx = speed
            self.facing_left = False

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.dy = -speed

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.dy = speed

        # Positie updaten
        self.x += self.dx
        self.y += self.dy

        # Borders controleren
        self.x = max(0, min(WIDTH - self.rect.width, self.x))
        self.y = max(0, min(HEIGHT - self.rect.height, self.y))

        # Collision box volgen
        self.rect.topleft = (self.x, self.y)

        # Animatie alleen bewegen
        if self.dx != 0 or self.dy != 0:
            self.anim_index += self.anim_speed
            if self.anim_index >= len(self.frames):
                self.anim_index = 0
        else:
            self.anim_index = 0

    def draw(self, win):
        # Apply screen shake
        shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        
        # Schaduw eerst tekenen
        shadow_x = self.rect.centerx - self.shadow.get_width() // 2 + shake_x
        shadow_y = self.rect.bottom - self.shadow.get_height() // 2 - 20 + shake_y
        win.blit(self.shadow, (shadow_x, shadow_y))

        # Huidige frame
        frame = self.frames[int(self.anim_index)]

        # Flip als nodig
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        # Speler tekenen — gecentreerd iets boven de schaduw
        draw_x = self.rect.centerx - frame.get_width() // 2 + shake_x
        draw_y = self.rect.centery - frame.get_height() // 2 + 8 + shake_y

        win.blit(frame, (draw_x, draw_y))

# ---- PLAYER INSTANCE ----
player = Player(WIDTH//2, HEIGHT//2, player_sheet, player_shadow)

# ------------------------------------------------------------
#                    LEVEL GENERATION
# ------------------------------------------------------------
def generate_level(num_items, num_obstacles, player_rect, safe_radius=100):
    obstacles = []
    items = []

    # items
    while len(items) < num_items:
        x = random.randint(0, WIDTH - item_size)
        y = random.randint(0, HEIGHT - item_size)
        new_item = pygame.Rect(x, y, item_size, item_size)

        # check dat het niet te dicht bij speler staat
        safe_zone = player_rect.inflate(safe_radius*2, safe_radius*2)
        if not new_item.colliderect(safe_zone) and not any(new_item.colliderect(i) for i in items):
            items.append(new_item)

    # obstacles
    safe_margin = 40
    max_attempts = 1000  # Prevent infinite loops
    attempts = 0
    
    while len(obstacles) < num_obstacles and attempts < max_attempts:
        attempts += 1
        x = random.randint(0, WIDTH - obstacle_size)
        y = random.randint(0, HEIGHT - obstacle_size)
        new_obs = pygame.Rect(x, y, obstacle_size, obstacle_size)

        safe = True
        # check afstand tot speler
        safe_zone = player_rect.inflate(safe_radius*2, safe_radius*2)
        if new_obs.colliderect(safe_zone):
            safe = False

        # check afstand tot items
        if safe:
            for item in items:
                item_safe = item.inflate(safe_margin * 2, safe_margin * 2)
                if new_obs.colliderect(item_safe):
                    safe = False
                    break

        # check afstand tot andere obstakels
        if safe and not any(new_obs.colliderect(o) for o in obstacles):
            obstacles.append(new_obs)

    return items, obstacles

items, obstacles = [], []
score = 0
combo = 0
combo_time = 1
last_collect_time = 0
start_time = 0
time_limit = 600
level = 1
pause_offset = 0  # Track time spent paused
game_mode = "time_attack"  # "time_attack" or "endless"
boss = None
level_start_time = 0
obstacles_touched = False  # For perfectionist achievement
game_initialized = False  # Track if game has been initialized

# ---- ACHIEVEMENT FUNCTIONS ----
def unlock_achievement(key):
    if key in achievements and not achievements[key]["unlocked"]:
        achievements[key]["unlocked"] = True
        # Save to file
        with open(achievements_file, "w") as f:
            json.dump(achievements, f)
        return True
    return False

def check_achievements():
    global total_coins_collected
    
    # First blood
    if score >= 1 and not achievements["first_blood"]["unlocked"]:
        if unlock_achievement("first_blood"):
            print(f"Achievement unlocked: {achievements['first_blood']['name']}")
    
    # Combo master
    if combo >= 10 and not achievements["combo_master"]["unlocked"]:
        if unlock_achievement("combo_master"):
            print(f"Achievement unlocked: {achievements['combo_master']['name']}")
    
    # Combo god
    if combo >= 20 and not achievements["combo_god"]["unlocked"]:
        if unlock_achievement("combo_god"):
            print(f"Achievement unlocked: {achievements['combo_god']['name']}")
    
    # Speed demon (complete level in 30 seconds)
    if level > 1:
        level_time = time.time() - level_start_time - pause_offset
        if level_time <= 30 and not achievements["speed_demon"]["unlocked"]:
            if unlock_achievement("speed_demon"):
                print(f"Achievement unlocked: {achievements['speed_demon']['name']}")
    
    # Perfectionist
    if not obstacles_touched and len(items) == 0 and not achievements["perfectionist"]["unlocked"]:
        if unlock_achievement("perfectionist"):
            print(f"Achievement unlocked: {achievements['perfectionist']['name']}")
    
    # Coin collector
    if total_coins_collected >= 100 and not achievements["coin_collector"]["unlocked"]:
        if unlock_achievement("coin_collector"):
            print(f"Achievement unlocked: {achievements['coin_collector']['name']}")
    
    # Survivor
    if level >= 10 and not achievements["survivor"]["unlocked"]:
        if unlock_achievement("survivor"):
            print(f"Achievement unlocked: {achievements['survivor']['name']}")
    
    # Time warrior
    if game_mode == "time_attack" and time_limit == 300 and score > 0 and not achievements["time_warrior"]["unlocked"]:
        if unlock_achievement("time_warrior"):
            print(f"Achievement unlocked: {achievements['time_warrior']['name']}")

# ------------------------------------------------------------
#                        SCREENS
# ------------------------------------------------------------
def draw_menu():
    WIN.fill(BLUE)
    title = FONT.render("Treasure Hunter", True, WHITE)
    start = FONT.render("Press SPACE to Start", True, WHITE)
    controls = FONT.render("Press C for Controls", True, WHITE)
    highscores = FONT.render("Press S for Highscores", True, WHITE)
    achievements_btn = FONT.render("Press A for Achievements", True, WHITE)
    difficulty_btn = FONT.render("Press D for Difficulty", True, WHITE)
    
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//6))
    WIN.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT//3))
    WIN.blit(controls, (WIDTH//2 - controls.get_width()//2, HEIGHT//2.5))
    WIN.blit(highscores, (WIDTH//2 - highscores.get_width()//2, HEIGHT//2.1))
    WIN.blit(achievements_btn, (WIDTH//2 - achievements_btn.get_width()//2, HEIGHT//1.8))
    WIN.blit(difficulty_btn, (WIDTH//2 - difficulty_btn.get_width()//2, HEIGHT//1.6))
    pygame.display.update()

def draw_pause_menu():
    WIN.fill(BLUE)
    title = FONT.render("Game Paused", True, WHITE)
    start = FONT.render("Press ESC to Continue", True, WHITE)
    stop = FONT.render("Press Q to Return to Menu", True, WHITE)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    WIN.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT//2))
    WIN.blit(stop, (WIDTH//2 - stop.get_width()//2, HEIGHT//1.5))
    pygame.display.update()

def draw_time_select():
    WIN.fill(GREEN)
    
    # Tutorial button at the top
    tutorial = FONT_SMALL.render("Press T for Tutorial", True, BLACK)
    WIN.blit(tutorial, (WIDTH//2 - tutorial.get_width()//2, HEIGHT//8))
    title = FONT.render("Choose Game Mode", True, BLACK)
    option1 = FONT.render("1. 1 Minute Time Attack", True, BLACK)
    option2 = FONT.render("2. 2 Minutes Time Attack", True, BLACK)
    option3 = FONT.render("3. 5 Minutes Time Attack", True, BLACK)
    option4 = FONT.render("4. Endless Mode", True, BLACK)
    back = FONT.render("Press BACKSPACE to Return", True, BLACK)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4.5))
    WIN.blit(option1, (WIDTH//2 - option1.get_width()//2, HEIGHT//3))
    WIN.blit(option2, (WIDTH//2 - option2.get_width()//2, HEIGHT//2.3))
    WIN.blit(option3, (WIDTH//2 - option3.get_width()//2, HEIGHT//1.9))
    WIN.blit(option4, (WIDTH//2 - option4.get_width()//2, HEIGHT//1.6))
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.25))
    pygame.display.update()

def draw_difficulty_select():
    WIN.fill(PURPLE)
    title = FONT.render("Select Difficulty", True, WHITE)
    
    difficulties = ["easy", "normal", "hard", "insane"]
    colors = [GREEN, BLUE, ORANGE, RED]
    
    y_offset = HEIGHT//3
    for i, diff in enumerate(difficulties):
        color = colors[i]
        if diff == current_difficulty:
            text = FONT.render(f"{i+1}. {diff.upper()} (CURRENT)", True, color)
        else:
            text = FONT.render(f"{i+1}. {diff.title()}", True, color)
        
        # Show difficulty stats
        stats = difficulty_settings[diff]
        stats_text = FONT_SMALL.render(
            f"Speed: {stats['player_speed']} | Obstacle Speed: {stats['obstacle_speed']} | Spawn: {stats['spawn_rate']}x", 
            True, WHITE
        )
        
        WIN.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
        WIN.blit(stats_text, (WIDTH//2 - stats_text.get_width()//2, y_offset + 30))
        y_offset += 80
    
    back = FONT.render("Press BACKSPACE to Return", True, WHITE)
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.15))
    pygame.display.update()

def draw_achievements():
    WIN.fill((50, 50, 100))
    title = FONT.render("Achievements", True, WHITE)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//10))
    
    unlocked_count = sum(1 for a in achievements.values() if a["unlocked"])
    total_count = len(achievements)
    progress = FONT.render(f"Unlocked: {unlocked_count}/{total_count}", True, WHITE)
    WIN.blit(progress, (WIDTH//2 - progress.get_width()//2, HEIGHT//7))
    
    y_offset = HEIGHT//4
    achievements_list = list(achievements.items())
    
    # Draw visible achievements based on scroll offset
    visible_count = 0
    for i, (key, ach) in enumerate(achievements_list):
        if i < achievement_scroll_offset:
            continue
        if visible_count >= 8:  # Only show 8 at a time
            break
            
        color = GREEN if ach["unlocked"] else GRAY
        name_text = FONT_SMALL.render(ach["name"], True, color)
        desc_text = FONT_SMALL.render(ach["desc"], True, WHITE)
        
        # Draw achievement box
        box_width = WIDTH - 100
        box_height = 60
        box_x = 50
        box_y = y_offset
        
        # Box background
        box_color = (30, 30, 60) if ach["unlocked"] else (20, 20, 40)
        pygame.draw.rect(WIN, box_color, (box_x, box_y, box_width, box_height), border_radius=10)
        pygame.draw.rect(WIN, color, (box_x, box_y, box_width, box_height), 2, border_radius=10)
        
        # Checkmark or lock icon
        icon_y = box_y + box_height // 2
        if ach["unlocked"]:
            pygame.draw.circle(WIN, GREEN, (box_x + 30, icon_y), 15)
            check = FONT_SMALL.render("✓", True, WHITE)
            WIN.blit(check, (box_x + 30 - check.get_width()//2, icon_y - check.get_height()//2))
        else:
            pygame.draw.circle(WIN, GRAY, (box_x + 30, icon_y), 15)
            lock = FONT_SMALL.render("?", True, WHITE)
            WIN.blit(lock, (box_x + 30 - lock.get_width()//2, icon_y - lock.get_height()//2))
        
        # Draw achievement name and description
        WIN.blit(name_text, (box_x + 60, box_y + 10))
        WIN.blit(desc_text, (box_x + 60, box_y + 35))
        
        y_offset += 70
        visible_count += 1
    
    # Scroll indicator
    if len(achievements) > 8:
        current_page = achievement_scroll_offset // 8 + 1
        total_pages = (len(achievements) + 7) // 8
        scroll_text = FONT_SMALL.render(f"Page {current_page}/{total_pages} - Use UP/DOWN to scroll", True, WHITE)
        WIN.blit(scroll_text, (WIDTH//2 - scroll_text.get_width()//2, HEIGHT//1.1))
    
    back = FONT.render("Press BACKSPACE to Return", True, WHITE)
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.05))
    pygame.display.update()

def draw_game():
    # Apply screen flash if active
    if screen_flash > 0:
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.set_alpha(screen_flash)
        flash_surface.fill(flash_color)
        WIN.blit(flash_surface, (0, 0))
    
    # Draw background
    WIN.blit(background_img, (0, 0))
    
    # Draw particles
    for particle in particles[:]:
        particle.update()
        particle.draw(WIN)
        if particle.lifetime <= 0:
            particles.remove(particle)

    # Draw items
    for item in items:
        bob_offset = math.sin(time.time() * 5) * 3
        WIN.blit(coin_img, (item.x, item.y + bob_offset))

    # Draw obstacles (only if boss is not active)
    if not boss:
        for obs in obstacles:
            WIN.blit(cactus_img, (obs.x, obs.y))

    # Draw boss if active
    if boss:
        boss.draw(WIN)
        
        # Draw hearts for healing during boss battle
        for heart in boss_hearts:
            if not heart['collected']:
                # Add a floating animation to hearts
                float_offset = math.sin(time.time() * 3) * 5
                WIN.blit(heart_img, (heart['rect'].x, heart['rect'].y + float_offset))

    # Draw player
    player.draw(WIN)
    
    # Draw UI
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    WIN.blit(score_text, (10, 10))
    
    if game_mode == "time_attack":
        elapsed = int(time.time() - start_time - pause_offset)
        timer_text = FONT.render(f"Time: {max(0, time_limit - elapsed)}", True, WHITE)
        WIN.blit(timer_text, (10, 40))
    
    combo_text = FONT.render(f"Combo x{combo}", True, ORANGE)
    WIN.blit(combo_text, (10, 70))
    
    level_text = FONT.render(f"Level: {level}", True, WHITE)
    WIN.blit(level_text, (10, 100))
    
    # Difficulty indicator
    diff_text = FONT_SMALL.render(f"Difficulty: {current_difficulty.title()}", True, WHITE)
    WIN.blit(diff_text, (10, 130))
    
    # Boss warning and player health during boss battle
    if boss:
        # Boss health
        boss_text = FONT.render(f"BOSS HP: {boss.hp}/{boss.max_hp}", True, RED)
        WIN.blit(boss_text, (WIDTH - boss_text.get_width() - 10, 10))
        
        # Player health during boss battle
        health_text = FONT.render(f"Your Health: ", True, WHITE)
        WIN.blit(health_text, (WIDTH - 200, 40))
        
        # Draw hearts for player health
        heart_spacing = 35
        start_x = WIDTH - 100
        for i in range(max_boss_player_health):
            heart_x = start_x + (i * heart_spacing)
            if i < boss_player_health:
                # Full heart
                WIN.blit(heart_img, (heart_x, 40))
            else:
                # Empty heart (draw in gray)
                empty_heart = heart_img.copy()
                empty_heart.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
                WIN.blit(empty_heart, (heart_x, 40))
    
    pygame.display.update()

def draw_tutorial():
    WIN.fill(GREEN)
    
    title = FONT.render("How to Play", True, BLACK)
    mode_title = FONT.render("Time Attack Modes:", True, BLACK)
    time_desc1 = FONT_SMALL.render("Collect as many coins as possible within the time limit", True, BLACK)
    time_desc2 = FONT_SMALL.render("Avoid cacti - touching them ends the game!", True, RED)
    time_desc3 = FONT_SMALL.render("Build combos by collecting coins quickly for bonus points", True, RED)
    endless_title = FONT.render("Endless Mode:", True, BLACK)
    endless_desc1 = FONT_SMALL.render("Survive as long as possible and reach higher levels", True, BLACK)
    endless_desc2 = FONT_SMALL.render("Every 5 levels, face a BOSS enemy!", True, RED)
    endless_desc3 = FONT_SMALL.render("During boss fights: Collect coins to damage the boss", True, RED)
    endless_desc4 = FONT_SMALL.render("Dodge boss projectiles - you have 3 hearts!", True, RED)
    endless_desc5 = FONT_SMALL.render("Collect heart items to restore health during boss battles", True, RED)
    controls_title = FONT_SMALL.render("Controls: Arrow Keys/WASD to move, CTRL/SPACE for slow mode", True, BLACK)
    back = FONT.render("Press BACKSPACE to Return", True, BLACK)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4.5))
    WIN.blit(mode_title, (WIDTH//2 - mode_title.get_width()//2, HEIGHT//3.5))
    WIN.blit(time_desc1, (WIDTH//2 - time_desc1.get_width()//2, HEIGHT//3))
    WIN.blit(time_desc2, (WIDTH//2 - time_desc2.get_width()//2, HEIGHT//2.7))
    WIN.blit(time_desc3, (WIDTH//2 - time_desc3.get_width()//2, HEIGHT//2.4))
    WIN.blit(endless_title, (WIDTH//2 - endless_title.get_width()//2, HEIGHT//2))
    WIN.blit(endless_desc1, (WIDTH//2 - endless_desc1.get_width()//2, HEIGHT//1.8))
    WIN.blit(endless_desc2, (WIDTH//2 - endless_desc2.get_width()//2, HEIGHT//1.7))
    WIN.blit(endless_desc3, (WIDTH//2 - endless_desc3.get_width()//2, HEIGHT//1.6))
    WIN.blit(endless_desc4, (WIDTH//2 - endless_desc4.get_width()//2, HEIGHT//1.5))
    WIN.blit(endless_desc5, (WIDTH//2 - endless_desc5.get_width()//2, HEIGHT//1.4))
    WIN.blit(controls_title, (WIDTH//2 - controls_title.get_width()//2, HEIGHT//1.2))
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.1))
    pygame.display.update()

def draw_game_over():
    WIN.fill(RED)
    text = FONT.render("Game Over!", True, WHITE)
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    level_text = FONT.render(f"Level Reached: {level}", True, WHITE)
    restart = FONT.render("Press SPACE to Restart", True, WHITE)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//4))
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//3))
    WIN.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2.5))
    WIN.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//1.5))
    pygame.display.update()

def draw_time_over():
    WIN.fill(YELLOW)
    text = FONT.render("Time Over!", True, BLACK)
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    restart = FONT.render("Press SPACE to Continue", True, WHITE)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    WIN.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//1.5))
    pygame.display.update()

def draw_new_highscore():
    WIN.fill(GREEN)
    text = FONT.render("New Highscore!", True, WHITE)
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    restart = FONT.render("Press SPACE to Continue", True, WHITE)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    WIN.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//1.5))
    pygame.display.update()

def draw_controls():
    WIN.fill(GRAY)
    title = FONT.render("Controls", True, WHITE)
    move = FONT.render("Move: Arrow Keys or WASD", True, WHITE)
    slow = FONT.render("Slow Mode: Hold CTRL or SPACE", True, WHITE)
    pause = FONT.render("Pause: ESC", True, WHITE)
    back = FONT.render("Press BACKSPACE to Return", True, WHITE)
    
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    WIN.blit(move, (WIDTH//2 - move.get_width()//2, HEIGHT//2.5))
    WIN.blit(slow, (WIDTH//2 - slow.get_width()//2, HEIGHT//2))
    WIN.blit(pause, (WIDTH//2 - pause.get_width()//2, HEIGHT//1.65))
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.3))
    pygame.display.update()

def draw_highscores():
    WIN.fill(ORANGE)
    title = FONT.render("Highscores", True, WHITE)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//6))
    
    # Load highscores
    if os.path.exists(highscore_file):
        with open(highscore_file, "r") as f:
            data = json.load(f)
    else:
        data = {}
    
    # Display highscores
    y_offset = HEIGHT//3.5
    time_labels = {"60": "1 Minute: ", "120": "2 Minutes: ", "300": "5 Minutes: ", "endless": "Endless Mode: "}
    
    for time_key in ["60", "120", "300", "endless"]:
        label = time_labels[time_key]
        score_val = data.get(time_key, 0)
        # For endless mode, show levels instead of score
        if time_key == "endless":
            text = FONT.render(f"{label}{score_val} Levels", True, WHITE)
        else:
            text = FONT.render(f"{label}{score_val}", True, WHITE)
        WIN.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
        y_offset += 60
    
    back = FONT.render("Press BACKSPACE to Return", True, WHITE)
    WIN.blit(back, (WIDTH//2 - back.get_width()//2, HEIGHT//1.15))
    pygame.display.update()

# ------------------------------------------------------------
#                        MAIN LOOP
# ------------------------------------------------------------
running = True
esc_key_pressed = False  # Debounce for ESC key
q_key_pressed = False  # Debounce for Q key
pause_start = 0  # Track when pause started
dt = 0  # Delta time for smooth animations
last_achievement_scroll_time = 0
scroll_delay = 0.15  # Delay between scrolls in seconds

while running:
    CLOCK.tick(60)
    dt = CLOCK.get_time() / 1000.0  # Convert to seconds
    
    # Update visual effects
    if screen_shake > 0:
        screen_shake -= 1
    if screen_flash > 0:
        screen_flash = max(0, screen_flash - 10)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Apply difficulty settings
    diff_settings = difficulty_settings[current_difficulty]
    player_speed = diff_settings["player_speed"]
    speed = slow_speed if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_SPACE] else player_speed

    # --- SCREEN HANDLING ---
    if screen == MENU:
        draw_menu()
        if keys[pygame.K_SPACE]:
            screen = TIME_SELECT
        elif keys[pygame.K_c]:
            screen = CONTROLS
        elif keys[pygame.K_s]:
            screen = HIGHSCORES
        elif keys[pygame.K_a]:
            screen = ACHIEVEMENTS
        elif keys[pygame.K_d]:
            screen = DIFFICULTY_SELECT

    elif screen == CONTROLS:
        draw_controls()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU

    elif screen == HIGHSCORES:
        draw_highscores()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU

    elif screen == ACHIEVEMENTS:
        # Handle scrolling with delay to prevent too fast scrolling
        current_time = time.time()
        if current_time - last_achievement_scroll_time > scroll_delay:
            if keys[pygame.K_UP]:
                achievement_scroll_offset = max(0, achievement_scroll_offset - 1)
                last_achievement_scroll_time = current_time
            if keys[pygame.K_DOWN]:
                achievement_scroll_offset = min(len(achievements) - 1, achievement_scroll_offset + 1)
                last_achievement_scroll_time = current_time
        
        draw_achievements()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU
            achievement_scroll_offset = 0 

    elif screen == DIFFICULTY_SELECT:
        draw_difficulty_select()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU
        elif keys[pygame.K_1]:
            current_difficulty = "easy"
        elif keys[pygame.K_2]:
            current_difficulty = "normal"
        elif keys[pygame.K_3]:
            current_difficulty = "hard"
        elif keys[pygame.K_4]:
            current_difficulty = "insane"

    elif screen == TIME_SELECT:
        draw_time_select()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU
        elif keys[pygame.K_t]:
            screen = TUTORIAL
        elif keys[pygame.K_1]:
            time_limit = 60
            game_mode = "time_attack"
            screen = PLAYING
            game_initialized = False  # ← Dit toevoegen!
        elif keys[pygame.K_2]:
            time_limit = 120
            game_mode = "time_attack"
            screen = PLAYING
            game_initialized = False  # ← Dit toevoegen!
        elif keys[pygame.K_3]:
            time_limit = 300
            game_mode = "time_attack"
            screen = PLAYING
            game_initialized = False  # ← Dit toevoegen!
        elif keys[pygame.K_4]:
            game_mode = "endless"
            screen = PLAYING
            game_initialized = False  # ← Dit toevoegen!

    elif screen == TUTORIAL:
        draw_tutorial()
        if keys[pygame.K_BACKSPACE]:
            screen = TIME_SELECT

    elif screen == PAUSED:
        draw_pause_menu()
        
        # Check for unpause (ESC key)
        if keys[pygame.K_ESCAPE] and not esc_key_pressed:
            esc_key_pressed = True
            screen = PLAYING
            pause_offset += time.time() - pause_start
            pygame.mixer.music.unpause()  # Resume music
        elif not keys[pygame.K_ESCAPE]:
            esc_key_pressed = False
        
        # Check for return to menu (Q key)
        if keys[pygame.K_q] and not q_key_pressed:
            q_key_pressed = True
            screen = MENU
            pygame.mixer.music.unpause()  # Resume music
        elif not keys[pygame.K_q]:
            q_key_pressed = False

    elif screen in [GAME_OVER, TIME_OVER, NEW_HIGHSCORE]:
        # Save highscore for endless mode when game over
        if screen == GAME_OVER and game_mode == "endless":
            if level > highscore:  # Compare levels, not score
                highscore = level
                if os.path.exists(highscore_file):
                    with open(highscore_file, "r") as f:
                        data = json.load(f)
                else:
                    data = {}
                data["endless"] = highscore
                with open(highscore_file, "w") as f:
                    json.dump(data, f)
                
                # Check difficulty master achievement
                if current_difficulty == "insane" and level >= 10:
                    unlock_achievement("difficulty_master")
        
        if screen == GAME_OVER:
            draw_game_over()
        elif screen == TIME_OVER:
            draw_time_over()
        elif screen == NEW_HIGHSCORE:
            draw_new_highscore()

        if keys[pygame.K_SPACE]:
            screen = MENU

    # --- PLAYING SCREEN ---
    elif screen == PLAYING:
        # Game initialization when first entering PLAYING
        if not game_initialized:
            game_initialized = True
            
            if os.path.exists(highscore_file):
                with open(highscore_file, "r") as f:
                    data = json.load(f)
                    if game_mode == "endless":
                        highscore = data.get("endless", 0)
                    else:
                        highscore = data.get(str(time_limit), 0)
            else:
                highscore = 0

            player.x = WIDTH // 2
            player.y = HEIGHT // 2
            player.rect.topleft = (player.x, player.y)

            items, obstacles = generate_level(20, 15, player.rect)
            score = 0
            combo = 0
            last_collect_time = 0
            start_time = time.time()  # ← Dit is cruciaal: starttijd resetten!
            pause_offset = 0
            level = 1
            boss = None
            level_start_time = time.time()
            obstacles_touched = False
            particles.clear()
            boss_player_health = max_boss_player_health
            boss_hearts.clear()
            
            print(f"Nieuwe game gestart! Tijdslimiet: {time_limit}s, Mode: {game_mode}")  # Debug

        # Check for pause key (ESC) - dit moet binnen PLAYING blijven
        if keys[pygame.K_ESCAPE] and not esc_key_pressed:
            esc_key_pressed = True
            screen = PAUSED
            pause_start = time.time()
            pygame.mixer.music.pause()  # Pause music
        elif not keys[pygame.K_ESCAPE]:
            esc_key_pressed = False

        # Player update
        player.update(keys, speed)
        
        # Update boss if active
        if boss:
            boss.update(dt, player.rect)
            
            # Spawn coins periodically during boss battle
            boss.try_spawn_coin(items, player.rect)
            
            # Spawn hearts at the start of boss battle if not already spawned
            if not boss.hearts_spawned:
                boss.spawn_hearts()
                boss.hearts_spawned = True
            
            # Check boss projectiles collision
            for proj in boss.projectiles[:]:
                proj_rect = pygame.Rect(proj[0] - 10, proj[1] - 10, 20, 20)
                if player.rect.colliderect(proj_rect):
                    # Remove the projectile
                    if proj in boss.projectiles:
                        boss.projectiles.remove(proj)
                    
                    # Decrease player health during boss battle
                    boss_player_health -= 1
                    
                    # Visual effect for getting hit
                    screen_shake = 15
                    screen_flash = 100
                    flash_color = RED
                    create_particles(player.rect.centerx, player.rect.centery, RED, 20)
                    
                    # Check if player is dead
                    if boss_player_health <= 0:
                        if death_sound:
                            death_sound.play()
                        screen = GAME_OVER
                        game_initialized = False
                        break

        # Coin collisions
        current_time = time.time()
        collected = [item for item in items if player.rect.colliderect(item)]
        for c in collected:
            items.remove(c)
            coin_sound.play()
            
            # Visual effect for collecting coin
            create_coin_particles(c.x, c.y)
            screen_shake = 5
            screen_flash = 30
            flash_color = YELLOW
            
            if current_time - last_collect_time - pause_offset <= combo_time:
                combo += 1
            else:
                combo = 1

            last_collect_time = current_time - pause_offset
            score += 1 * combo
            
            # Update total coins
            total_coins_collected += 1
            
            # If boss is active, damage boss when collecting coins
            if boss:
                boss.take_damage(5 * combo)  # Each coin damages boss

        # Check heart collection during boss battle
        if boss:
            for heart in boss_hearts[:]:
                if not heart['collected'] and player.rect.colliderect(heart['rect']):
                    heart['collected'] = True
                    boss_player_health = min(max_boss_player_health, boss_player_health + 1)
                    create_particles(heart['rect'].centerx, heart['rect'].centery, RED, 20)
                    screen_shake = 3
                    screen_flash = 50
                    flash_color = GREEN

        if current_time - last_collect_time - pause_offset > combo_time:
            combo = 0

        # Check obstacle collision (only if boss is not active)
        game_over_triggered = False
        if not boss:
            for obs in obstacles:
                if player.rect.colliderect(obs):
                    obstacles_touched = True
                    # Visual effect for hitting obstacle
                    screen_shake = 20
                    screen_flash = 150
                    flash_color = RED
                    create_particles(player.rect.centerx, player.rect.centery, RED, 30)
                    
                    if death_sound:
                        death_sound.play()
                    game_over_triggered = True
                    screen = GAME_OVER
                    game_initialized = False
                    break
        
        # Als game over getriggerd is, teken dan nog één keer het spel en ga dan verder
        if game_over_triggered:
            draw_game()  # Teken de visuele effecten
            continue  # Ga naar volgende frame (die dan GAME_OVER tekent)

        # Time check (only for time attack)
        if game_mode == "time_attack":
            elapsed = current_time - start_time - pause_offset
            if elapsed >= time_limit:
                if score > highscore:
                    highscore = score
                    if os.path.exists(highscore_file):
                        with open(highscore_file, "r") as f:
                            data = json.load(f)
                    else:
                        data = {}
                    data[str(time_limit)] = highscore  # update alleen huidige time_limit
                    with open(highscore_file, "w") as f:
                        json.dump(data, f)
                    screen = NEW_HIGHSCORE
                else:
                    screen = TIME_OVER
                game_initialized = False  # ← Dit toevoegen!
                continue  # Stop verdere verwerking deze frame

        # Level up
        if not items and not boss:
            level += 1
            level_start_time = time.time()
            obstacles_touched = False
            
            # Check for boss level (every 5 levels in endless mode)
            if game_mode == "endless" and level % 5 == 0:
                boss = Boss()
                # Reset player health for boss battle
                boss_player_health = max_boss_player_health
                # Clear all obstacles during boss battle
                obstacles.clear()
                # Clear existing coins
                items.clear()
                # Clear hearts
                boss_hearts.clear()
                # Unlock boss slayer achievement
                unlock_achievement("boss_slayer")
            else:
                new_obstacles = 15 + random.randint(0, 5) + level
                items, obstacles = generate_level(20, new_obstacles, player.rect, safe_radius=150)
        
        # Check if boss is defeated
        if boss and boss.hp <= 0:
            # Boss defeated visual effect
            create_particles(boss.x, boss.y, PURPLE, 50)
            create_particles(boss.x, boss.y, YELLOW, 30)
            screen_shake = 25
            screen_flash = 200
            flash_color = PURPLE
            
            boss = None
            boss_hearts.clear()  # Clear any remaining hearts
            # Generate next level after boss
            new_obstacles = 15 + random.randint(0, 5) + level
            items, obstacles = generate_level(20, new_obstacles, player.rect, safe_radius=150)
            # Add bonus score for defeating boss
            score += 100 * combo

        # Check achievements
        check_achievements()
        
        draw_game()

    else:
        game_initialized = False

# Save achievements before quitting
with open(achievements_file, "w") as f:
    json.dump(achievements, f)

pygame.quit()
sys.exit()
