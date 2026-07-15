import os
import random
import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.core.audio import SoundLoader
from kivy.core.text import Label as CoreLabel

# Screen configuration for Landscape
Window.size = (800, 600)

MAP_THEMES = {
    1: {"bg": (40/255, 150/255, 40/255), "road": (70/255, 70/255, 70/255), "tree": (30/255, 120/255, 30/255), "name": "Level 1: Green Valley"},
    2: {"bg": (210/255, 180/255, 140/255), "road": (90/255, 85/255, 80/255), "tree": (120/255, 110/255, 60/255), "name": "Level 2: Desert Highway"},
    3: {"bg": (240/255, 248/255, 255/255), "road": (60/255, 65/255, 75/255), "tree": (175/255, 200/255, 220/255), "name": "Level 3: Snow Mountain"},
    4: {"bg": (20/255, 15/255, 35/255), "road": (30/255, 30/255, 40/255), "tree": (255/255, 20/255, 147/255), "name": "Level 4: Neon Cyber City"},
    5: {"bg": (0, 100/255, 150/255), "road": (100/255, 100/255, 105/255), "tree": (50/255, 50/255, 50/255), "name": "Level 5: Mega Ocean Bridge"}
}

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)
        self.current_state = "MENU"
        self.current_level = 1
        
        # Game constants & variables
        self.car_x, self.car_y = 375, 100 # Android uses bottom-left as (0,0)
        self.base_car_speed = 8
        self.car_speed = self.base_car_speed
        self.car_width, self.car_height = 50, 80
        
        self.TOTAL_RACERS = 10
        self.player_distance = 0.0
        self.race_length = 6000.0
        
        self.lanes = [270, 375, 480]
        self.opponents = []
        self.opponent_colors = [(0,0,1), (1,0.4,0), (0.5,0,0.5), (0,1,1), (1,0.7,0.7)]
        
        self.game_timer = 60
        self.time_left = 60
        
        self.police_x, self.police_y = 375, 20
        self.police_speed_x = 4
        
        self.heli_x, self.heli_y = 400, 750
        self.heli_active = False
        self.heli_wobble = 0
        
        self.bullet_active = False
        self.bullet_x, self.bullet_y = 0, 0
        self.bullet_warning_timer = 0
        self.bullet_warning_x = 0
        
        self.nitro_energy = 50.0
        self.super_nitro_timer = 0
        self.nitro_active = False
        self.coins_list = []
        
        self.heli_sound_played = False
        self.police_sound_played = False
        self.end_sound_played = False
        
        self.road_stripes_y = 0
        self.player_position = 10
        
        # Setup Scenery
        self.trees = [{'x': random.randint(30, 170) if i%2==0 else random.randint(580, 720), 'y': random.randint(0, 600), 'side': 'left' if i%2==0 else 'right'} for i in range(6)]
        
        # Safe Sound Loaders
        self.sound_are_baap_re = SoundLoader.load("are_baap_re.mp3")
        self.sound_khopdi_tod = SoundLoader.load("khopdi_tod.mp3")
        self.sound_moye_moye = SoundLoader.load("moye_moye.mp3")
        self.sound_meow = SoundLoader.load("meow.mp3")
        
        # Key & Touch bounds binding
        Window.bind(on_key_down=self.on_key_down)
        
        # Main Game Loop ticking at 60 FPS
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        Clock.schedule_interval(self.update_timer, 1.0)
        
        self.start_level(1)

    def start_level(self, level_num):
        self.current_level = level_num
        self.car_x, self.car_y = 375, 100
        self.police_x, self.police_y = 375, 20
        self.heli_x, self.heli_y = 400, 750
        self.heli_active = False
        self.bullet_active = False
        self.bullet_warning_timer = 0
        self.player_distance = 0.0
        self.nitro_energy = 50.0
        self.super_nitro_timer = 0
        self.coins_list = []
        self.player_position = self.TOTAL_RACERS
        self.time_left = self.game_timer
        
        self.heli_sound_played = False
        self.police_sound_played = False
        self.end_sound_played = False
        
        # Reset sounds safely
        for s in [self.sound_are_baap_re, self.sound_khopdi_tod, self.sound_moye_moye, self.sound_meow]:
            if s: s.stop()
            
        self.init_opponents()

    def init_opponents(self):
        self.opponents = []
        for i in range(self.TOTAL_RACERS - 1):
            self.opponents.append({
                'id': i,
                'distance': 400.0 + (i * 480.0) + random.uniform(-80, 80),
                'speed': 8.5 + (i * 0.35),
                'color': self.opponent_colors[i % len(self.opponent_colors)],
                'x': random.choice(self.lanes),
                'y': 800
            })

    def spawn_coin(self):
        if len(self.coins_list) < 4:
            lane = random.choice(self.lanes) + 15
            coin_type = 'blue' if random.randint(1, 4) == 1 else 'yellow'
            self.coins_list.append({'x': lane, 'y': random.randint(650, 800), 'type': coin_type})

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if self.current_state == "MENU" and key == 40: # Enter Key
            self.start_level(1)
            self.current_state = "GAME"
        elif self.current_state == "GAME_OVER":
            if key == 114: # 'R' Key
                self.start_level(self.current_level)
                self.current_state = "GAME"
            elif key == 109: # 'M' Key
                self.current_state = "MENU"
        elif self.current_state == "VICTORY":
            if key == 110: # 'N' Key
                if self.current_level < 5:
                    self.start_level(self.current_level + 1)
                    self.current_state = "GAME"
                else:
                    self.current_state = "MENU"
            elif key == 114: # 'R' Key
                self.start_level(self.current_level)
                self.current_state = "GAME"

    # Android controls via Touch screen regions
    def on_touch_down(self, touch):
        if self.current_state == "MENU":
            self.start_level(1)
            self.current_state = "GAME"
            return True
        elif self.current_state == "GAME_OVER":
            self.start_level(self.current_level)
            self.current_state = "GAME"
            return True
        elif self.current_state == "VICTORY":
            if self.current_level < 5:
                self.start_level(self.current_level + 1)
            else:
                self.current_state = "MENU"
            self.current_state = "GAME"
            return True
            
        if self.current_state == "GAME":
            if touch.x < 400: # Touch left half to move left
                if self.car_x > 250: self.car_x -= 35
            else: # Touch right half to move right
                if self.car_x < 550 - self.car_width: self.car_x += 35
            
            # Double tap triggers Nitro Boost
            if touch.is_double_tap and self.nitro_energy > 0:
                self.nitro_active = True
        return True

    def on_touch_up(self, touch):
        self.nitro_active = False
        return True

    def update_timer(self, dt):
        if self.current_state == "GAME":
            self.time_left -= 1
            if self.time_left <= 0:
                if self.player_position <= 3: self.current_state = "VICTORY"
                else: self.current_state = "GAME_OVER"

    def update(self, dt):
        if self.current_state != "GAME":
            self.draw_canvas()
            return
            
        # Speeds and dynamics calculations
        if self.super_nitro_timer > 0:
            self.super_nitro_timer -= 1
            line_speed = (10 + self.current_level) * 2.2
        elif self.nitro_active and self.nitro_energy > 0:
            self.nitro_energy -= 0.35
            line_speed = (10 + self.current_level) * 1.6
        else:
            line_speed = 10 + self.current_level
            self.nitro_active = False

        self.player_distance += (line_speed * 0.5)

        if self.player_distance >= self.race_length:
            if self.player_position <= 3: self.current_state = "VICTORY"
            else: self.current_state = "GAME_OVER"

        # Moving scenery down
        self.road_stripes_y = (self.road_stripes_y - line_speed) % 600
        for tree in self.trees:
            tree['y'] -= line_speed
            if tree['y'] < -50:
                tree['y'] = 650
                tree['x'] = random.randint(30, 170) if tree['side'] == 'left' else random.randint(580, 720)

        # AI Opponents updates
        player_pos_calc = self.TOTAL_RACERS
        for op in self.opponents:
            op['distance'] += (op['speed'] * 0.5)
            if op['distance'] <= self.player_distance: player_pos_calc -= 1
            op['y'] = self.car_y + (op['distance'] - self.player_distance)

        self.player_position = max(1, min(self.TOTAL_RACERS, player_pos_calc))

        # Coins movements and collisions
        for coin in self.coins_list[:]:
            coin['y'] -= line_speed
            if coin['y'] < -50: self.coins_list.remove(coin)
            # Collision Box Check
            elif (self.car_x < coin['x'] + 20 and self.car_x + self.car_width > coin['x'] and
                  self.car_y < coin['y'] + 20 and self.car_y + self.car_height > coin['y']):
                if coin['type'] == 'yellow': self.nitro_energy = min(100.0, self.nitro_energy + 25)
                else: self.super_nitro_timer = 300
                self.coins_list.remove(coin)

        if random.randint(1, 100) < 5: self.spawn_coin()

        # Police movements & sound triggers
        if self.police_x < self.car_x: self.police_x += self.police_speed_x
        elif self.police_x > self.car_x: self.police_x -= self.police_speed_x
        
        if self.police_y < self.car_y - 20: self.police_y += 1
        
        if not self.police_sound_played and self.sound_khopdi_tod:
            self.sound_khopdi_tod.play()
            self.police_sound_played = True

        # Helicopter meme management
        if self.player_distance >= 1500: self.heli_active = True
        if self.heli_active:
            if self.heli_y > 450: self.heli_y -= 2
            if not self.heli_sound_played and self.sound_are_baap_re:
                self.sound_are_baap_re.play()
                self.heli_sound_played = True
                
            self.heli_wobble += 0.05
            self.heli_x += ((self.car_x + math.sin(self.heli_wobble)*30) - self.heli_x) * 0.04

        # Global hitboxes checks for crash conditions
        if abs(self.car_x - self.police_x) < 45 and abs(self.car_y - self.police_y) < 75:
            self.current_state = "GAME_OVER"
            
        for op in self.opponents:
            if 0 < op['y'] < 600 and abs(self.car_x - op['x']) < 45 and abs(self.car_y - op['y']) < 75:
                self.current_state = "GAME_OVER"

        # Safe sound trigger on end game
        if self.current_state == "GAME_OVER" and not self.end_sound_played:
            if self.sound_moye_moye: self.sound_moye_moye.play()
            self.end_sound_played = True
        elif self.current_state == "VICTORY" and not self.end_sound_played:
            if self.sound_meow: self.sound_meow.play()
            self.end_sound_played = True

        self.draw_canvas()

    def draw_canvas(self):
        self.canvas.clear()
        theme = MAP_THEMES[self.current_level]
        
        with self.canvas:
            # Background Canvas Drawing
            Color(*theme["bg"])
            Rectangle(pos=(0, 0), size=(800, 600))
            
            if self.current_state == "MENU":
                Color(1, 215/255, 0) # Gold
                # Kivy doesn't have inline fonts like pygame, we use core engine tags or labels
                return

            # Road Layout Paint
            Color(*theme["road"])
            Rectangle(pos=(250, 0), size=(300, 600))
            
            # Boundary lines
            Color(1,1,1)
            Rectangle(pos=(243, 0), size=(7, 600))
            Rectangle(pos=(550, 0), size=(7, 600))
            
            # Center Stripes
            Color(1, 1, 0 if self.current_level == 4 else 1)
            for y in range(0, 600, 150):
                Rectangle(pos=(395, (y + self.road_stripes_y) % 600), size=(10, 50))
                
            # Render Scenery
            for tree in self.trees:
                Color(139/255, 69/255, 19/255) # Brown
                Rectangle(pos=(tree['x'] + 15, tree['y']), size=(10, 20))
                Color(*theme["tree"])
                Ellipse(pos=(tree['x'], tree['y'] + 15), size=(40, 40))

            # Coins Render
            for coin in self.coins_list:
                Color(1, 1, 0 if coin['type'] == 'yellow' else 1)
                Ellipse(pos=(coin['x'], coin['y']), size=(20, 20))

            # AI Racers Render
            for op in self.opponents:
                if -100 < op['y'] < 700:
                    Color(*op['color'])
                    Rectangle(pos=(op['x'], op['y']), size=(50, 80))

            # Police Car Render
            Color(0,0,0)
            Rectangle(pos=(self.police_x, self.police_y), size=(50, 80))
            Color(0,0,1) # Light bar
            Rectangle(pos=(self.police_x + 10, self.police_y + 75), size=(30, 5))

            # Player Asset Render Engine
            if self.super_nitro_timer > 0 or self.nitro_active:
                Color(1, 0.5, 0) # Flame effect
                Rectangle(pos=(self.car_x + 10, self.car_y - 20), size=(30, 20))
                
            Color(0.4, 0.8, 1) # Blue Player Car
            Rectangle(pos=(self.car_x, self.car_y), size=(self.car_width, self.car_height))

            # Helicopter Mode Paint
            if self.heli_active:
                Color(0.2, 0.2, 0.2)
                Ellipse(pos=(self.heli_x - 30, self.heli_y - 20), size=(110, 40))

class MemeCarGameApp(App):
    def build(self):
        return GameWidget()

if __name__ == '__main__':
    MemeCarGameApp().run()
