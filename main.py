import pygame
import sys
import random
import os
import math

pygame.init()
pygame.mixer.init()  # Audio Engine Initialize

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Meme Racing Championship: Auto Sound Fix")

# --- COLORS ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 215, 0)
BLUE = (0, 150, 255)
ORANGE = (255, 100, 0)
BLACK = (0, 0, 0)
LIGHT_BLUE = (100, 200, 255)
BROWN = (139, 69, 19)
GRAY = (70, 70, 70)
GREEN = (40, 150, 40)

# --- MAP SPECIFIC COLORS ---
MAP_THEMES = {
    1: {"bg": (40, 150, 40), "road": (70, 70, 70), "tree": (30, 120, 30), "name": "Level 1: Green Valley"},
    2: {"bg": (210, 180, 140), "road": (90, 85, 80), "tree": (120, 110, 60), "name": "Level 2: Desert Highway"},
    3: {"bg": (240, 248, 255), "road": (60, 65, 75), "tree": (175, 200, 220), "name": "Level 3: Snow Mountain"},
    4: {"bg": (20, 15, 35), "road": (30, 30, 40), "tree": (255, 20, 147), "name": "Level 4: Neon Cyber City"},
    5: {"bg": (0, 100, 150), "road": (100, 100, 105), "tree": (50, 50, 50), "name": "Level 5: Mega Ocean Bridge"}
}

# --- FONTS ---
font = pygame.font.SysFont("Arial", 24, bold=True)
large_font = pygame.font.SysFont("Arial", 50, bold=True)

# --- STATES ---
STATE_MENU = "MENU"
STATE_GAME = "GAME"
STATE_GAME_OVER = "GAME_OVER"
STATE_VICTORY = "VICTORY"
current_state = STATE_MENU

current_level = 1  

# --- GAME VARIABLES ---
car_x, car_y = 375, 480          
base_car_speed = 8             
car_speed = base_car_speed
car_width, car_height = 50, 80

TOTAL_RACERS = 10
player_distance = 0.0
race_length = 6000.0  

opponents = []
lanes = [270, 375, 480] 
opponent_colors = [BLUE, ORANGE, (128,0,128), (0,255,255), (255,192,203)]

game_timer = 60 
timer_start_ticks = 0

police_x, police_y = 375, 570                  
police_speed_x = 4              
police_width, police_height = 50, 80

heli_x, heli_y = WIDTH // 2, -150                   
heli_active = False
heli_wobble = 0

bullet_active = False
bullet_rect = pygame.Rect(0, 0, 0, 0)
bullet_warning_timer = 0
bullet_warning_x, bullet_warning_y = 0, 0

nitro_energy = 50         
super_nitro_timer = 0     
nitro_active = False
coins_list = []           

# --- SOUND MEME FLAGS ---
heli_sound_played = False
police_sound_played = False
end_sound_played = False

# --- SCENERY ---
trees = [{'x': random.randint(30, 170) if i%2==0 else random.randint(580, 720), 'y': random.randint(0, 600), 'side': 'left' if i%2==0 else 'right'} for i in range(6)]
road_stripes_y = 0
line_y1, line_y2, line_y3 = 0, 200, 400
base_line_speed = 10            
line_speed = base_line_speed
player_position = 10

# --- SMART SOUND LOADER (Handles both single and double .mp3 extensions) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_sound_safe(base_name):
    # Try all possible extensions Windows might have created
    possible_names = [base_name + ".mp3.mp3", base_name + ".mp3", base_name]
    for name in possible_names:
        for folder in [BASE_DIR, os.path.join(BASE_DIR, ".."), os.path.join(BASE_DIR, "cargame")]:
            path = os.path.join(folder, name)
            if os.path.exists(path):
                try:
                    return pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Error loading {name}: {e}")
    return None

# Safe load sounds
sound_are_baap_re = load_sound_safe("are_baap_re")
sound_khopdi_tod = load_sound_safe("khopdi_tod")
sound_moye_moye = load_sound_safe("moye_moye")
sound_meow = load_sound_safe("meow")

# --- IMAGE LOADING & PRE-RENDERING ---
def load_car_image(possible_names):
    for name in possible_names:
        for folder in [BASE_DIR, os.path.join(BASE_DIR, ".."), os.path.join(BASE_DIR, "cargame")]:
            path = os.path.join(folder, name)
            if os.path.exists(path): return pygame.image.load(path).convert_alpha()
    return None

HAS_IMAGES = False
player_normal_surf = None
player_boost_surf = None
enemy_surf = None

img_base = load_car_image(["player_car.png.png", "player_car.png"])
img_enemy = load_car_image(["enemy_car.png.png", "enemy_car.png"])

if img_base and img_enemy:
    try:
        player_normal_surf = pygame.transform.scale(img_base, (car_width, car_height))
        enemy_surf = pygame.transform.scale(img_enemy, (50, 80))
        
        player_boost_surf = player_normal_surf.copy()
        boost_glow = pygame.Surface((car_width, car_height), pygame.SRCALPHA)
        boost_glow.fill((0, 100, 255, 70)) 
        player_boost_surf.blit(boost_glow, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        HAS_IMAGES = True
    except:
        HAS_IMAGES = False

def init_opponents():
    global opponents
    opponents = []
    for i in range(TOTAL_RACERS - 1):
        opponents.append({
            'id': i,
            'distance': 400.0 + (i * 480.0) + random.uniform(-80, 80),
            'speed': 8.5 + (i * 0.35), 
            'color': opponent_colors[i % len(opponent_colors)],
            'x': random.choice(lanes),
            'y': -500 
        })

def spawn_coin():
    if len(coins_list) < 4:
        lane = random.choice(lanes) + 15
        coin_type = 'blue' if random.randint(1, 4) == 1 else 'yellow' 
        coins_list.append({'rect': pygame.Rect(lane, random.randint(-200, -50), 20, 20), 'type': coin_type})

def start_level(level_num):
    global car_x, car_y, line_y1, line_y2, line_y3, base_line_speed, police_x, police_y
    global heli_x, heli_y, heli_active, bullet_active, bullet_warning_timer, player_distance
    global nitro_energy, super_nitro_timer, coins_list, player_position, timer_start_ticks, current_level
    global heli_sound_played, police_sound_played, end_sound_played
    
    current_level = level_num
    car_x, car_y = 375, 480                 
    police_x, police_y = 375, 570
    heli_x, heli_y = WIDTH // 2, -150
    heli_active = False
    bullet_active = False
    bullet_warning_timer = 0
    player_distance = 0.0
    nitro_energy = 50 
    super_nitro_timer = 0
    coins_list = []
    player_position = TOTAL_RACERS
    timer_start_ticks = pygame.time.get_ticks()
    
    # Flags & Sounds Reset
    heli_sound_played = False
    police_sound_played = False
    end_sound_played = False
    pygame.mixer.stop() 
    
    init_opponents()
    line_y1, line_y2, line_y3 = 0, 200, 400
    base_line_speed = 10 + current_level  
    
    for _ in range(4): spawn_coin()

start_level(1)
clock = pygame.time.Clock()  
running = True

while running:
    clock.tick(60) 

    # --- 1. EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if current_state == STATE_MENU:
                if event.key == pygame.K_RETURN:
                    start_level(1)
                    current_state = STATE_GAME
            elif current_state == STATE_GAME_OVER:
                if event.key == pygame.K_r:
                    start_level(current_level) 
                    current_state = STATE_GAME
                elif event.key == pygame.K_m:
                    current_state = STATE_MENU
            elif current_state == STATE_VICTORY:
                if event.key == pygame.K_n: 
                    if current_level < 5:
                        start_level(current_level + 1)
                        current_state = STATE_GAME
                    else:
                        current_state = STATE_MENU 
                elif event.key == pygame.K_r:
                    start_level(current_level)
                    current_state = STATE_GAME

    # --- 2. GAME LOOP LOGIC ---
    if current_state == STATE_GAME:
        keys = pygame.key.get_pressed()
        
        seconds_passed = (pygame.time.get_ticks() - timer_start_ticks) // 1000
        time_left = max(0, game_timer - seconds_passed)
        if time_left <= 0:
            if player_position <= 3: current_state = STATE_VICTORY
            else: current_state = STATE_GAME_OVER

        if super_nitro_timer > 0: super_nitro_timer -= 1
        
        if super_nitro_timer > 0: 
            nitro_active = True
            car_speed = base_car_speed * 1.7
            line_speed = base_line_speed * 2.2
        elif keys[pygame.K_SPACE] and nitro_energy > 0: 
            nitro_active = True
            nitro_energy -= 0.35  
            car_speed = base_car_speed * 1.3
            line_speed = base_line_speed * 1.6
        else:
            nitro_active = False
            car_speed = base_car_speed
            line_speed = base_line_speed

        player_distance += (line_speed * 0.5)

        if player_distance >= race_length:
            if player_position <= 3: current_state = STATE_VICTORY
            else: current_state = STATE_GAME_OVER

        if keys[pygame.K_LEFT] and car_x > 250: car_x -= car_speed
        if keys[pygame.K_RIGHT] and car_x < 550 - car_width: car_x += car_speed

        # --- POLICE MEME TRIGGER ---
        if police_x < car_x: police_x += police_speed_x
        elif police_x > car_x: police_x -= police_speed_x
        police_y += 3 if nitro_active else (-0.2 if police_y > car_y + 90 else 0)
        
        if police_y < HEIGHT and not police_sound_played:
            if sound_khopdi_tod: 
                sound_khopdi_tod.play()
            police_sound_played = True

        # --- HELICOPTER MEME TRIGGER ---
        if player_distance >= 1500: heli_active = True
        if heli_active:
            if heli_y < 130: heli_y += 2
            
            if not heli_sound_played:
                if sound_are_baap_re: 
                    sound_are_baap_re.play()
                heli_sound_played = True
                
            heli_wobble += 0.05
            heli_x += ((car_x + math.sin(heli_wobble)*30) - heli_x) * 0.04 

            if not bullet_active and bullet_warning_timer == 0 and random.randint(1, 100) < 2:
                bullet_warning_x, bullet_warning_y = car_x + 10, car_y + 10
                bullet_warning_timer = 60 
            
            if bullet_warning_timer > 0:
                bullet_warning_timer -= 1
                if bullet_warning_timer == 0:
                    bullet_active = True
                    bullet_rect = pygame.Rect(bullet_warning_x, -50, 20, 40)
            
            if bullet_active:
                bullet_rect.y += 22
                if bullet_rect.y > HEIGHT: bullet_active = False

        line_y1 = (line_y1 + line_speed) % HEIGHT
        line_y2 = (line_y2 + line_speed) % HEIGHT
        line_y3 = (line_y3 + line_speed) % HEIGHT
        road_stripes_y = (road_stripes_y + line_speed) % 40

        for tree in trees:
            tree['y'] += line_speed
            if tree['y'] > HEIGHT:
                tree['y'] = -50
                tree['x'] = random.randint(30, 170) if tree['side'] == 'left' else random.randint(580, 720)

        player_pos_calc = TOTAL_RACERS 
        for op in opponents:
            op['distance'] += (op['speed'] * 0.5)
            if op['distance'] <= player_distance: player_pos_calc -= 1
            op['y'] = car_y - (op['distance'] - player_distance)

        player_position = max(1, min(TOTAL_RACERS, player_pos_calc))

        for coin in coins_list[:]:
            coin['rect'].y += line_speed
            if coin['rect'].y > HEIGHT: coins_list.remove(coin)
            elif pygame.Rect(car_x, car_y, car_width, car_height).colliderect(coin['rect']):
                if coin['type'] == 'yellow': nitro_energy = min(100, nitro_energy + 25)
                else: super_nitro_timer = 300 
                coins_list.remove(coin)

        if random.randint(1, 100) < 5: spawn_coin()

        if pygame.Rect(car_x, car_y, car_width, car_height).colliderect(pygame.Rect(police_x, police_y, police_width, police_height)):
            current_state = STATE_GAME_OVER
        if bullet_active and pygame.Rect(car_x, car_y, car_width, car_height).colliderect(bullet_rect):
            current_state = STATE_GAME_OVER
        for op in opponents:
            if 0 < op['y'] < HEIGHT and pygame.Rect(car_x, car_y, car_width, car_height).colliderect(pygame.Rect(op['x'], op['y'], 50, 80)):
                current_state = STATE_GAME_OVER

    # --- GAME END MEME TRIGGERS ---
    if current_state == STATE_GAME_OVER and not end_sound_played:
        pygame.mixer.stop()
        if sound_moye_moye: 
            sound_moye_moye.play()
        end_sound_played = True
        
    elif current_state == STATE_VICTORY and not end_sound_played:
        pygame.mixer.stop()
        if sound_meow: 
            sound_meow.play()
        end_sound_played = True

    # --- 3. RENDERING ENGINE ---
    theme = MAP_THEMES[current_level]
    screen.fill(theme["bg"])

    if current_state == STATE_MENU:
        screen.blit(large_font.render("RACING CHAMPIONSHIP", True, YELLOW), (WIDTH//2 - 250, HEIGHT//2 - 100))
        screen.blit(font.render("Press ENTER to Start Career Mode", True, WHITE), (WIDTH//2 - 170, HEIGHT//2))
        screen.blit(font.render("Clear Levels by entering TOP 3 before 60s!", True, LIGHT_BLUE), (WIDTH//2 - 210, HEIGHT//2 + 50))

    elif current_state in [STATE_GAME, STATE_GAME_OVER, STATE_VICTORY]:
        pygame.draw.rect(screen, theme["road"], (250, 0, 300, 600))
        
        for y in range(-40, HEIGHT + 40, 40):
            stripe_color = (200, 200, 200) if current_level == 5 else (WHITE if (y // 40) % 2 == 0 else RED)
            pygame.draw.rect(screen, stripe_color, (243, y + road_stripes_y, 7, 20))
            pygame.draw.rect(screen, stripe_color, (550, y + road_stripes_y, 7, 20))

        cline_color = YELLOW if current_level == 4 else WHITE
        pygame.draw.rect(screen, cline_color, (395, line_y1, 10, 40))
        pygame.draw.rect(screen, cline_color, (395, line_y2, 10, 40))
        pygame.draw.rect(screen, cline_color, (395, line_y3, 10, 40))

        if current_level != 5:
            for tree in trees:
                pygame.draw.rect(screen, BROWN, (tree['x'] + 15, tree['y'] + 30, 10, 20))
                pygame.draw.circle(screen, theme["tree"], (tree['x'] + 20, tree['y'] + 20), 20)
        else: 
            for y in range(0, HEIGHT, 150):
                pygame.draw.rect(screen, (50, 50, 50), (200, (y + road_stripes_y*2)%600, 43, 20))
                pygame.draw.rect(screen, (50, 50, 50), (557, (y + road_stripes_y*2)%600, 43, 20))

        for coin in coins_list:
            pygame.draw.circle(screen, YELLOW if coin['type'] == 'yellow' else BLUE, (coin['rect'].x + 10, coin['rect'].y + 10), 10)
            pygame.draw.circle(screen, WHITE, (coin['rect'].x + 10, coin['rect'].y + 10), 5, 1)

        if bullet_warning_timer > 0:
            pygame.draw.circle(screen, RED, (bullet_warning_x + 10, bullet_warning_y + 20), 25, 3)

        for op in opponents:
            if -100 < op['y'] < HEIGHT + 100:
                if HAS_IMAGES: screen.blit(enemy_surf, (op['x'], op['y']))
                else:
                    pygame.draw.rect(screen, op['color'], (op['x'], op['y'], 50, 80))
                    pygame.draw.rect(screen, WHITE, (op['x'] + 10, op['y'] + 15, 30, 20))

        pygame.draw.rect(screen, BLACK, (police_x, police_y, police_width, police_height))
        pygame.draw.rect(screen, WHITE, (police_x + 5, police_y + 20, police_width - 10, 30))
        pygame.draw.rect(screen, RED if pygame.time.get_ticks() % 400 < 200 else BLUE, (police_x + 10, police_y + 2, 30, 6))

        if bullet_active: pygame.draw.rect(screen, YELLOW, bullet_rect)

        if nitro_active:
            f_color = LIGHT_BLUE if super_nitro_timer > 0 else ORANGE
            f_len = random.randint(25, 45) if super_nitro_timer > 0 else random.randint(15, 30)
            pygame.draw.polygon(screen, f_color, [(car_x + 7, car_y + car_height), (car_x + 2, car_y + car_height + f_len), (car_x + 13, car_y + car_height)])
            pygame.draw.polygon(screen, f_color, [(car_x + car_width - 13, car_y + car_height), (car_x + car_width - 2, car_y + car_height + f_len), (car_x + car_width - 7, car_y + car_height)])

        if HAS_IMAGES:
            if super_nitro_timer > 0: screen.blit(player_boost_surf, (car_x, car_y))
            else: screen.blit(player_normal_surf, (car_x, car_y))
        else:
            pygame.draw.rect(screen, LIGHT_BLUE if super_nitro_timer > 0 else RED, (car_x, car_y, car_width, car_height))

        if heli_active:
            pygame.draw.ellipse(screen, (50, 50, 50), (heli_x - 30, heli_y - 20, 110, 40))
            pygame.draw.ellipse(screen, BLUE, (heli_x + 40, heli_y - 12, 30, 20))
            b_offset = int(math.sin(pygame.time.get_ticks() * 0.15) * 60)
            pygame.draw.line(screen, WHITE, (heli_x + 25 - b_offset, heli_y - 25), (heli_x + 25 + b_offset, heli_y - 25), 4)

        # Minimap 
        mx, my, mw, mh = 750, 150, 16, 300
        pygame.draw.rect(screen, BLACK, (mx - 4, my - 4, mw + 8, mh + 8), 2)
        pygame.draw.rect(screen, GRAY, (mx, my, mw, mh))
        pygame.draw.rect(screen, GREEN, (mx, my + mh - 8, mw, 8)) 
        pygame.draw.rect(screen, RED, (mx, my, mw, 8)) 
        
        pygame.draw.circle(screen, YELLOW, (mx + 8, my + mh - int((player_distance / race_length) * mh)), 5)
        for op in opponents:
            pygame.draw.circle(screen, RED, (mx + 8, max(my, min(my+mh, my + mh - int((op['distance'] / race_length) * mh)))), 3)

        screen.blit(large_font.render(f"Pos: {player_position}/10", True, YELLOW), (10, 10))
        screen.blit(font.render(theme["name"], True, WHITE), (10, 55))
        
        time_color = RED if time_left <= 10 else WHITE
        screen.blit(font.render(f"⏱️ Time Left: {time_left}s", True, time_color), (10, 85))

        prog_p = min(100, int((player_distance / race_length) * 100))
        pygame.draw.rect(screen, BLACK, (10, 120, 180, 18))
        pygame.draw.rect(screen, GREEN, (10, 120, int(prog_p * 1.8), 18))
        
        pygame.draw.rect(screen, BLACK, (10, 150, 180, 18))
        pygame.draw.rect(screen, ORANGE, (10, 150, int(nitro_energy * 1.8), 18))

        if current_state == STATE_GAME_OVER:
            overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(200); overlay.fill(BLACK); screen.blit(overlay, (0,0))
            screen.blit(large_font.render("GAME OVER / STAGE FAILED", True, RED), (WIDTH//2 - 270, HEIGHT//2 - 60))
            screen.blit(font.render("Press 'R' to Retry Level", True, WHITE), (WIDTH//2 - 110, HEIGHT//2 + 10))
        
        elif current_state == STATE_VICTORY:
            overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(210); overlay.fill(BLACK); screen.blit(overlay, (0,0))
            if current_level < 5:
                screen.blit(large_font.render(f"LEVEL {current_level} CLEARED!", True, YELLOW), (WIDTH//2 - 180, HEIGHT//2 - 60))
                screen.blit(font.render("Press 'N' for NEXT MAP STAGE 🏁", True, WHITE), (WIDTH//2 - 170, HEIGHT//2 + 10))
            else:
                screen.blit(large_font.render("🏆 ULTIMATE CHAMPION! 🏆", True, YELLOW), (WIDTH//2 - 250, HEIGHT//2 - 60))
                screen.blit(font.render("You conquered all tracks! Press 'R' to Restart", True, WHITE), (WIDTH//2 - 200, HEIGHT//2 + 10))

    pygame.display.update()

pygame.quit()
sys.exit()