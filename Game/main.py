import pygame
import random
import sys
import time
import json
import os

# ---- INIT ----
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 1000, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Treasure Hunter")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("comicsans", 30)

# ---- COLORS ----
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (200, 200, 50)
GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)

# ---- GAME VARIABLES ----
player_speed = 6
slow_speed = 3
item_size = 50
obstacle_size = 50
highscore_file = "Game/highscore.json"
highscore = 0

# ---- LOAD SPRITES ----
background_img = pygame.image.load("Game/sprites/sand_sprite.jpg").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

cactus_img = pygame.image.load("Game/sprites/cactus_sprite.png").convert_alpha()
cactus_img = pygame.transform.scale(cactus_img, (obstacle_size, obstacle_size))

coin_img = pygame.image.load("Game/sprites/coin_sprite.png").convert_alpha()
coin_img = pygame.transform.scale(coin_img, (item_size, item_size))

player_sheet = pygame.image.load("Game/sprites/player_walk.png").convert_alpha()
player_shadow = pygame.image.load("Game/sprites/player_shadow.png").convert_alpha()
# ---- LOAD SOUNDS ----
coin_sound = pygame.mixer.Sound("Game/sounds/coin.mp3")
bg_music = "Game/sounds/background_song.mp3"



# ---- SCREENS ----
MENU, TIME_SELECT, PLAYING, PAUSED, GAME_OVER, TIME_OVER, NEW_HIGHSCORE, CONTROLS, HIGHSCORES = (
    "menu", "time_select", "playing", "paused", "game_over", "time_over", "new_highscore", "controls", "highscores"
)
screen = MENU

# ---- BACKGROUND MUSIC ----
pygame.mixer.music.load(bg_music)
pygame.mixer.music.set_volume(0.5)  
pygame.mixer.music.play(-1) 

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
        # Schaduw eerst tekenen
        shadow_x = self.rect.centerx - self.shadow.get_width() // 2
        shadow_y = self.rect.bottom - self.shadow.get_height() // 2 - 20
        win.blit(self.shadow, (shadow_x, shadow_y))

        # Huidige frame
        frame = self.frames[int(self.anim_index)]

        # Flip als nodig
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        # Speler tekenen — gecentreerd iets boven de schaduw
        draw_x = self.rect.centerx - frame.get_width() // 2 
        draw_y = self.rect.centery - frame.get_height() // 2 + 8  

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
    while len(obstacles) < num_obstacles:
        x = random.randint(0, WIDTH - obstacle_size)
        y = random.randint(0, HEIGHT - obstacle_size)
        new_obs = pygame.Rect(x, y, obstacle_size, obstacle_size)

        safe = True
        # check afstand tot speler
        safe_zone = player_rect.inflate(safe_radius*2, safe_radius*2)
        if new_obs.colliderect(safe_zone):
            safe = False

        # check afstand tot items
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

# ------------------------------------------------------------
#                        SCREENS
# ------------------------------------------------------------
def draw_menu():
    WIN.fill(BLUE)
    title = FONT.render("Treasure Hunter", True, WHITE)
    start = FONT.render("Press SPACE to Start", True, WHITE)
    controls = FONT.render("Press C for Controls", True, WHITE)
    highscores = FONT.render("Press S for Highscores", True, WHITE)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
    WIN.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT//2.2))
    WIN.blit(controls, (WIDTH//2 - controls.get_width()//2, HEIGHT//1.7))
    WIN.blit(highscores, (WIDTH//2 - highscores.get_width()//2, HEIGHT//1.4))
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


def draw_game():
    WIN.blit(background_img, (0, 0))

    for item in items:
        WIN.blit(coin_img, (item.x, item.y))

    for obs in obstacles:
        WIN.blit(cactus_img, (obs.x, obs.y))

    player.draw(WIN)
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
    
    pygame.display.update()


def draw_game_over():
    WIN.fill(RED)
    text = FONT.render("Game Over!", True, WHITE)
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    restart = FONT.render("Press SPACE to Restart", True, WHITE)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
    WIN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
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

while running:
    CLOCK.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    speed = slow_speed if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_SPACE] else player_speed

    if screen == MENU:
        draw_menu()
        if keys[pygame.K_SPACE]:
            screen = TIME_SELECT
        elif keys[pygame.K_c]:
            screen = CONTROLS
        elif keys[pygame.K_s]:
            screen = HIGHSCORES

    elif screen == CONTROLS:
        draw_controls()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU

    elif screen == HIGHSCORES:
        draw_highscores()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU

    elif screen == TIME_SELECT:
        draw_time_select()
        if keys[pygame.K_BACKSPACE]:
            screen = MENU
        elif keys[pygame.K_1]:
            time_limit = 60
            game_mode = "time_attack"
            screen = PLAYING
        elif keys[pygame.K_2]:
            time_limit = 120
            game_mode = "time_attack"
            screen = PLAYING
        elif keys[pygame.K_3]:
            time_limit = 300
            game_mode = "time_attack"
            screen = PLAYING
        elif keys[pygame.K_4]:
            game_mode = "endless"
            screen = PLAYING

        # ---- LOAD HIGHSCORE ----
        if screen == PLAYING:
            if os.path.exists(highscore_file):
                with open(highscore_file, "r") as f:
                    data = json.load(f)
                    # haal highscore op voor de huidige mode
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
            start_time = time.time()
            pause_offset = 0
            level = 1

    elif screen == PLAYING:
        # Check for pause key (ESC)
        if keys[pygame.K_ESCAPE] and not esc_key_pressed:
            esc_key_pressed = True
            screen = PAUSED
            pause_start = time.time()
            pygame.mixer.music.pause()  # Pause music
        elif not keys[pygame.K_ESCAPE]:
            esc_key_pressed = False

        # player update
        player.update(keys, speed)

        # collisions
        current_time = time.time()
        collected = [item for item in items if player.rect.colliderect(item)]
        for c in collected:
            items.remove(c)
            coin_sound.play()
            if current_time - last_collect_time - pause_offset <= combo_time:
                combo += 1
            else:
                combo = 1

            last_collect_time = current_time - pause_offset
            score += 1 * combo

        if current_time - last_collect_time - pause_offset > combo_time:
            combo = 0

        # Botsen met obstakels → GAME_OVER
        if any(player.rect.colliderect(obs) for obs in obstacles):
            screen = GAME_OVER

        # Tijd controleren (alleen voor time attack)
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

        # Level up
        if not items:
            level += 1
            new_obstacles = 15 + random.randint(0, 5) + level
            items, obstacles = generate_level(20, new_obstacles, player.rect, safe_radius=150)

        draw_game()

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
        
        if screen == GAME_OVER:
            draw_game_over()
        elif screen == TIME_OVER:
            draw_time_over()
        elif screen == NEW_HIGHSCORE:
            draw_new_highscore()

        if keys[pygame.K_SPACE]:
            screen = MENU

pygame.quit()
sys.exit()