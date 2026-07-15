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
        
        # Sizing and Positioning defaults (Will adapt instantly via bind)
        self.car_x, self.car_y = 0, 100
        self.car_width, self.car_height = 50, 85
        
        self.TOTAL_RACERS = 10
        self.player_distance = 0.0
        self.race_length = 6000.0
        
        self.lanes = []
        self.opponents = []
        self.opponent_colors = [(0,0,1), (1,0.4,0), (0.5,0,0.5), (0,1,1), (1,0.7,0.7)]
        
        self.game_timer = 60
        self.time_left = 60
        
        self.police_x, self.police_y = 0, 30
        self.police_speed_x = 4
        
        self.heli_x, self.heli_y = 0, 0
        self.heli_active = False
        self.heli_wobble = 0
        
        self.nitro_energy = 50.0
        self.super_nitro_timer = 0
        self.nitro_active = False
        self.coins_list = []
        
        self.heli_sound_played = False
        self.police_sound_played = False
        self.end_sound_played = False
        
        self.road_stripes_y = 0
        self.player_position = 10
        self.trees = []
        
        # Load meme sounds safely
        self.sound_are_baap_re = SoundLoader.load("are_baap_re.mp3")
        self.sound_khopdi_tod = SoundLoader.load("khopdi_tod.mp3")
        self.sound_moye_moye = SoundLoader.load("moye_moye.mp3")
        self.sound_meow = SoundLoader.load("meow.mp3")
        
        # Game loop clocks
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        Clock.schedule_interval(self.update_timer, 1.0)
        
        # Bind screen resizing dynamically
        self.bind(size=self.setup_responsive_layout)

    def setup_responsive_layout(self, *args):
        if self.width < 100: return
        
        # Road takes 40% center area of any screen size
        self.road_left = self.width * 0.3
        self.road_width = self.width * 0.4
        lane_w = self.road_width / 3
        
        # Midpoint of each lane
        self.lanes = [
            self.road_left + (lane_w * 0.5) - (self.car_width * 0.5),
            self.road_left + (lane_w * 1.5) - (self.car_width * 0.5),
            self.road_left + (lane_w * 2.5) - (self.car_width * 0.5)
        ]
        
        # Reposition cars safely if game is active
        if self.current_state == "MENU":
            self.car_x = self.lanes[1]
            self.police_x = self.lanes[1]
            self.heli_x = self.width / 2
            self.heli_y = self.height + 100
            
        # Responsive Trees on Grass boundaries
        self.trees = []
        for i in range(8):
            if i % 2 == 0:
                tx = random.randint(10, max(20, int(self.road_left - 60)))
                side = 'left'
            else:
                tx = random.randint(int(self.road_left + self.road_width + 10), max(int(self.road_left + self.road_width + 20), int(self.width - 60)))
                side = 'right'
            self.trees.append({'x': tx, 'y': random.randint(0, int(self.height)), 'side': side})

    def start_level(self, level_num):
        self.current_level = level_num
        self.setup_responsive_layout()
        self.car_x = self.lanes[1]
        self.car_y = 100
        self.police_x = self.lanes[1]
        self.police_y = 30
        self.heli_y = self.height + 150
        self.heli_active = False
        self.player_distance = 0.0
        self.nitro_energy = 50.0
        self.super_nitro_timer = 0
        self.coins_list = []
        self.player_position = self.TOTAL_RACERS
        self.time_left = self.game_timer
        
        self.heli_sound_played = False
        self.police_sound_played = False
        self.end_sound_played = False
        
        for s in [self.sound_are_baap_re, self.sound_khopdi_tod, self.sound_moye_moye, self.sound_meow]:
            if s: s.stop()
            
        self.init_opponents()

    def init_opponents(self):
        self.opponents = []
        for i in range(self.TOTAL_RACERS - 1):
            self.opponents.append({
                'id': i,
                'distance': 500.0 + (i * 500.0) + random.uniform(-60, 60),
                'speed': 8.2 + (i * 0.4),
                'color': self.opponent_colors[i % len(self.opponent_colors)],
                'x': random.choice(self.lanes),
                'y': self.height + 200
            })

    def spawn_coin(self):
        if len(self.coins_list) < 4 and len(self.lanes) > 0:
            cx = random.choice(self.lanes) + (self.car_width/2 - 12)
            ctype = 'blue' if random.randint(1, 5) == 1 else 'yellow'
            self.coins_list.append({'x': cx, 'y': self.height + 50, 'type': ctype})

    def on_touch_down(self, touch):
        if self.current_state == "MENU":
            self.start_level(1)
            self.current_state = "GAME"
            return True
        elif self.current_state in ["GAME_OVER", "VICTORY"]:
            self.start_level(1)
            self.current_state = "GAME"
            return True
            
        if self.current_state == "GAME":
            # Left Half Touch -> Shift left lane / Right Half Touch -> Shift right lane
            current_lane_idx = 1
            min_dist = 99999
            for idx, lx in enumerate(self.lanes):
                if abs(self.car_x - lx) < min_dist:
                    min_dist = abs(self.car_x - lx)
                    current_lane_idx = idx
                    
            if touch.x < self.width / 2:
                if current_lane_idx > 0: self.car_x = self.lanes[current_lane_idx - 1]
            else:
                if current_lane_idx < 2: self.car_x = self.lanes[current_lane_idx + 1]
                
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
        if self.width < 100: return
        if self.current_state != "GAME":
            self.draw_canvas()
            return
            
        # Speed dynamics
        if self.super_nitro_timer > 0:
            self.super_nitro_timer -= 1
            line_speed = (10 + self.current_level) * 2.0
        elif self.nitro_active and self.nitro_energy > 0:
            self.nitro_energy -= 0.3
            line_speed = (10 + self.current_level) * 1.5
        else:
            line_speed = 10 + self.current_level
            self.nitro_active = False

        self.player_distance += (line_speed * 0.4)

        if self.player_distance >= self.race_length:
            if self.player_position <= 3: self.current_state = "VICTORY"
            else: self.current_state = "GAME_OVER"

        # Background scrolling
        self.road_stripes_y = (self.road_stripes_y - line_speed) % self.height
        for tree in self.trees:
            tree['y'] -= line_speed
            if tree['y'] < -60:
                tree['y'] = self.height + 20
                if tree['side'] == 'left':
                    tree['x'] = random.randint(10, max(20, int(self.road_left - 60)))
                else:
                    tree['x'] = random.randint(int(self.road_left + self.road_width + 10), max(int(self.road_left + self.road_width + 20), int(self.width - 60)))

        # AI Loop & Position Tracking
        player_pos_calc = self.TOTAL_RACERS
        for op in self.opponents:
            op['distance'] += (op['speed'] * 0.4)
            if op['distance'] <= self.player_distance: player_pos_calc -= 1
            op['y'] = self.car_y + (op['distance'] - self.player_distance)

        self.player_position = max(1, min(self.TOTAL_RACERS, player_pos_calc))

        # Coins rendering bounds & collisions
        for coin in self.coins_list[:]:
            coin['y'] -= line_speed
            if coin['y'] < -50: self.coins_list.remove(coin)
            elif abs(self.car_x + self.car_width/2 - coin['x'] - 12) < 35 and abs(self.car_y + self.car_height/2 - coin['y'] - 12) < 50:
                if coin['type'] == 'yellow': self.nitro_energy = min(100.0, self.nitro_energy + 20)
                else: self.super_nitro_timer = 250
                self.coins_list.remove(coin)

        if random.randint(1, 100) < 4: self.spawn_coin()

        # Police processing logic
        if self.police_x < self.car_x: self.police_x += self.police_speed_x
        elif self.police_x > self.car_x: self.police_x -= self.police_speed_x
        if self.police_y < self.car_y - 15: self.police_y += 0.5
        
        if not self.police_sound_played and self.sound_khopdi_tod:
            self.sound_khopdi_tod.play()
            self.police_sound_played = True

        # Helicopter activation & mapping tracking
        if self.player_distance >= 1200: self.heli_active = True
        if self.heli_active:
            if self.heli_y > self.height * 0.65: self.heli_y -= 1.5
            if not self.heli_sound_played and self.sound_are_baap_re:
                self.sound_are_baap_re.play()
                self.heli_sound_played = True
            self.heli_wobble += 0.05
            self.heli_x += ((self.car_x + math.sin(self.heli_wobble) * 40) - self.heli_x) * 0.05

        # Precise Crash Collision Checks
        if abs(self.car_x - self.police_x) < 40 and abs(self.car_y - self.police_y) < 70:
            self.current_state = "GAME_OVER"
            
        for op in self.opponents:
            if -80 < op['y'] < self.height + 50:
                if abs(self.car_x - op['x']) < 40 and abs(self.car_y - op['y']) < 70:
                    self.current_state = "GAME_OVER"

        # Stop/Play state sounds triggers
        if self.current_state in ["GAME_OVER", "VICTORY"] and not self.end_sound_played:
            if self.current_state == "GAME_OVER" and self.sound_moye_moye: self.sound_moye_moye.play()
            if self.current_state == "VICTORY" and self.sound_meow: self.sound_meow.play()
            self.end_sound_played = True

        self.draw_canvas()

    def draw_canvas(self):
        self.canvas.clear()
        theme = MAP_THEMES[self.current_level]
        
        with self.canvas:
            # Full Screen Responsive Map Grass Background
            Color(*theme["bg"])
            Rectangle(pos=(0, 0), size=(self.width, self.height))
            
            # State Management Rendering
            if self.current_state == "MENU":
                self.render_text("MEME CAR RACING", self.width/2, self.height*0.6, 36, (1,1,0))
                self.render_text("Tap Anywhere to Start", self.width/2, self.height*0.4, 22, (1,1,1))
                return
            elif self.current_state == "GAME_OVER":
                self.render_text("MOYE MOYE! GAME OVER", self.width/2, self.height*0.6, 34, (1,0,0))
                self.render_text("Tap to Restart", self.width/2, self.height*0.4, 22, (1,1,1))
                return
            elif self.current_state == "VICTORY":
                self.render_text("VICTORY! MEOW MEOW", self.width/2, self.height*0.6, 34, (0,1,0))
                self.render_text("Tap to Continue", self.width/2, self.height*0.4, 22, (1,1,1))
                return

            # Centered Scaled Road Layout
            Color(*theme["road"])
            Rectangle(pos=(self.road_left, 0), size=(self.road_width, self.height))
            
            # White Road Boundaries
            Color(1, 1, 1)
            Rectangle(pos=(self.road_left - 4, 0), size=(4, self.height))
            Rectangle(pos=(self.road_left + self.road_width, 0), size=(4, self.height))
            
            # Dashed lane divider lines
            Color(1, 1, 0 if self.current_level == 4 else 1)
            lane_w = self.road_width / 3
            for y in range(0, int(self.height) + 120, 120):
                curr_y = (y + self.road_stripes_y) % self.height
                Rectangle(pos=(self.road_left + lane_w - 2, curr_y), size=(4, 45))
                Rectangle(pos=(self.road_left + (lane_w * 2) - 2, curr_y), size=(4, 45))
                
            # Scenery Processing
            for tree in self.trees:
                Color(139/255, 69/255, 19/255)
                Rectangle(pos=(tree['x'] + 16, tree['y']), size=(8, 16))
                Color(*theme["tree"])
                Ellipse(pos=(tree['x'], tree['y'] + 12), size=(40, 40))

            # Coins Render Engine
            for coin in self.coins_list:
                Color(0, 0.7, 1) if coin['type'] == 'blue' else Color(1, 0.9, 0)
                Ellipse(pos=(coin['x'], coin['y']), size=(24, 24))

            # AI Opponents Render Engine
            for op in self.opponents:
                if -100 < op['y'] < self.height + 100:
                    Color(*op['color'])
                    Rectangle(pos=(op['x'], op['y']), size=(self.car_width, self.car_height))

            # Police Car Rendering
            Color(0.1, 0.1, 0.1)
            Rectangle(pos=(self.police_x, self.police_y), size=(self.car_width, self.car_height))
            Color(0, 0, 1) # Flashing lightbar
            Rectangle(pos=(self.police_x + 10, self.police_y + self.car_height - 6), size=(30, 6))

            # Nitro Fire Flame Graphic Effect
            if self.super_nitro_timer > 0 or self.nitro_active:
                Color(1, 0.3 + (0.4 if self.super_nitro_timer > 0 else 0), 0)
                Rectangle(pos=(self.car_x + 12, self.car_y - 25), size=(26, 25))
                
            # Main Player Car Graphics
            Color(0.2, 0.65, 1)
            Rectangle(pos=(self.car_x, self.car_y), size=(self.car_width, self.car_height))

            # Helicopter Render Engine
            if self.heli_active:
                Color(0.15, 0.15, 0.15, 0.8)
                Ellipse(pos=(self.heli_x - 45, self.heli_y - 20), size=(90, 40))
                Color(0, 0, 0) # Blades
                Line(points=[self.heli_x - 60, self.heli_y, self.heli_x + 60, self.heli_y], width=2)

            # In-Game Dashboard HUD Text
            hud_str = f"Rank: {self.player_position}/10 | Dist: {int(self.player_distance)}m | Time: {self.time_left}s | Nitro: {int(self.nitro_energy)}%"
            self.render_text(hud_str, self.width / 2, self.height - 35, 18, (1, 1, 1), center=True)
            self.render_text(theme["name"], 120, self.height - 35, 16, (1, 1, 0), center=False)

    def render_text(self, text, x, y, size, color, center=True):
        lbl = CoreLabel(text=text, font_size=size, color=(color[0], color[1], color[2], 1))
        lbl.refresh()
        texture = lbl.texture
        if center:
            Rectangle(texture=texture, pos=(x - texture.width/2, y - texture.height/2), size=texture.size)
        else:
            Rectangle(texture=texture, pos=(x, y), size=texture.size)

class MemeCarGameApp(App):
    def build(self):
        return GameWidget()

if __name__ == '__main__':
    MemeCarGameApp().run()
