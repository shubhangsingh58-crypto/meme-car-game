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
    2: {"bg": (210/255, 180/255, 140/255), "road": (90/255, 85/255, 80/255), "tree": (120/255, 110/255, 60/255), "name": "Level 2: Desert Highway"}
}

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)
        self.current_state = "MENU" # SAFE START STATE
        self.current_level = 1
        
        self.car_x, self.car_y = 0, 100
        self.car_width, self.car_height = 50, 85
        
        self.TOTAL_RACERS = 10
        self.player_distance = 0.0
        self.race_length = 6000.0
        
        self.lanes = []
        self.opponents = []
        self.opponent_colors = [(0,0,1), (1,0.4,0), (0.5,0,0.5)]
        
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
        
        self.road_stripes_y = 0
        self.player_position = 10
        self.trees = []
        
        # Audio handlers
        self.sound_are_baap_re = SoundLoader.load("are_baap_re.mp3")
        self.sound_khopdi_tod = SoundLoader.load("khopdi_tod.mp3")
        self.sound_moye_moye = SoundLoader.load("moye_moye.mp3")
        self.sound_meow = SoundLoader.load("meow.mp3")
        
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        Clock.schedule_interval(self.update_timer, 1.0)
        
        self.bind(size=self.setup_responsive_layout)

    def setup_responsive_layout(self, *args):
        if self.width < 150: return # Stop execution if screen bounds are not initialized
        
        self.road_left = self.width * 0.3
        self.road_width = self.width * 0.4
        lane_w = self.road_width / 3
        
        self.lanes = [
            self.road_left + (lane_w * 0.5) - (self.car_width * 0.5),
            self.road_left + (lane_w * 1.5) - (self.car_width * 0.5),
            self.road_left + (lane_w * 2.5) - (self.car_width * 0.5)
        ]
        
        # Safely align positions only if engine hasn't processed data
        if self.player_distance == 0.0:
            self.car_x = self.lanes[1]
            self.police_x = self.lanes[1]
            self.heli_x = self.width / 2
            self.heli_y = self.height + 100
            
        self.trees = []
        for i in range(6):
            if i % 2 == 0:
                tx = random.randint(10, max(20, int(self.road_left - 60)))
                side = 'left'
            else:
                tx = random.randint(int(self.road_left + self.road_width + 10), max(int(self.road_left + self.road_width + 20), int(self.width - 60)))
                side = 'right'
            self.trees.append({'x': tx, 'y': random.randint(0, int(self.height)), 'side': side})

    def start_level(self, level_num):
        if self.width < 150: return
        self.current_level = level_num
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
        if len(self.coins_list) < 3 and len(self.lanes) > 0:
            cx = random.choice(self.lanes) + (self.car_width/2 - 12)
            ctype = 'blue' if random.randint(1, 5) == 1 else 'yellow'
            self.coins_list.append({'x': cx, 'y': self.height + 50, 'type': ctype})

    def on_touch_down(self, touch):
        if self.current_state in ["MENU", "GAME_OVER", "VICTORY"]:
            if self.width > 150:
                self.start_level(1)
                self.current_state = "GAME"
            return True
            
        if self.current_state == "GAME":
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
        if self.width < 150: return
        if self.current_state != "GAME":
            self.draw_canvas()
            return
            
        line_speed = 10 + self.current_level
        if self.nitro_active and self.nitro_energy > 0:
            self.nitro_energy -= 0.3
            line_speed = (10 + self.current_level) * 1.5
        else:
            self.nitro_active = False

        self.player_distance += (line_speed * 0.4)

        if self.player_distance >= self.race_length:
            if self.player_position <= 3: self.current_state = "VICTORY"
            else: self.current_state = "GAME_OVER"

        self.road_stripes_y = (self.road_stripes_y - line_speed) % self.height
        for tree in self.trees:
            tree['y'] -= line_speed
            if tree['y'] < -60:
                tree['y'] = self.height + 20

        player_pos_calc = self.TOTAL_RACERS
        for op in self.opponents:
            op['distance'] += (op['speed'] * 0.4)
            if op['distance'] <= self.player_distance: player_pos_calc -= 1
            op['y'] = self.car_y + (op['distance'] - self.player_distance)

        self.player_position = max(1, min(self.TOTAL_RACERS, player_pos_calc))

        for coin in self.coins_list[:]:
            coin['y'] -= line_speed
            if coin['y'] < -50: self.coins_list.remove(coin)
            elif abs(self.car_x + self.car_width/2 - coin['x'] - 12) < 35 and abs(self.car_y + self.car_height/2 - coin['y'] - 12) < 50:
                if coin['type'] == 'yellow': self.nitro_energy = min(100.0, self.nitro_energy + 20)
                self.coins_list.remove(coin)

        if random.randint(1, 100) < 4: self.spawn_coin()

        if self.police_x < self.car_x: self.police_x += self.police_speed_x
        elif self.police_x > self.car_x: self.police_x -= self.police_speed_x
        if self.police_y < self.car_y - 15: self.police_y += 0.5

        if self.player_distance >= 1200: self.heli_active = True
        if self.heli_active:
            if self.heli_y > self.height * 0.65: self.heli_y -= 1.5
            self.heli_wobble += 0.05
            self.heli_x += ((self.car_x + math.sin(self.heli_wobble) * 40) - self.heli_x) * 0.05

        # Strictly verify coordinate system before declaring a crash
        if self.player_distance > 50:
            if abs(self.car_x - self.police_x) < 35 and abs(self.car_y - self.police_y) < 65:
                self.current_state = "GAME_OVER"
                if self.sound_moye_moye: self.sound_moye_moye.play()
                
            for op in self.opponents:
                if -80 < op['y'] < self.height + 50:
                    if abs(self.car_x - op['x']) < 35 and abs(self.car_y - op['y']) < 65:
                        self.current_state = "GAME_OVER"
                        if self.sound_moye_moye: self.sound_moye_moye.play()

        self.draw_canvas()

    def draw_canvas(self):
        self.canvas.clear()
        theme = MAP_THEMES[1]
        
        with self.canvas:
            Color(*theme["bg"])
            Rectangle(pos=(0, 0), size=(self.width, self.height))
            
            if self.current_state == "MENU":
                self.render_text("MEME CAR RACING", self.width/2, self.height*0.6, 32, (1,1,0))
                self.render_text("Tap Anywhere to Start", self.width/2, self.height*0.4, 20, (1,1,1))
                return
            elif self.current_state == "GAME_OVER":
                self.render_text("MOYE MOYE! GAME OVER", self.width/2, self.height*0.6, 30, (1,0,0))
                self.render_text("Tap to Restart", self.width/2, self.height*0.4, 20, (1,1,1))
                return
            elif self.current_state == "VICTORY":
                self.render_text("VICTORY! MEOW MEOW", self.width/2, self.height*0.6, 30, (0,1,0))
                self.render_text("Tap to Continue", self.width/2, self.height*0.4, 20, (1,1,1))
                return

            Color(*theme["road"])
            Rectangle(pos=(self.road_left, 0), size=(self.road_width, self.height))
            
            Color(1, 1, 1)
            Rectangle(pos=(self.road_left - 4, 0), size=(4, self.height))
            Rectangle(pos=(self.road_left + self.road_width, 0), size=(4, self.height))
            
            lane_w = self.road_width / 3
            for y in range(0, int(self.height) + 120, 120):
                curr_y = (y + self.road_stripes_y) % self.height
                Rectangle(pos=(self.road_left + lane_w - 2, curr_y), size=(4, 45))
                Rectangle(pos=(self.road_left + (lane_w * 2) - 2, curr_y), size=(4, 45))
                
            for tree in self.trees:
                Color(139/255, 69/255, 19/255)
                Rectangle(pos=(tree['x'] + 16, tree['y']), size=(8, 16))
                Color(*theme["tree"])
                Ellipse(pos=(tree['x'], tree['y'] + 12), size=(40, 40))

            for coin in self.coins_list:
                Color(1, 0.9, 0)
                Ellipse(pos=(coin['x'], coin['y']), size=(22, 22))

            for op in self.opponents:
                if -100 < op['y'] < self.height + 100:
                    Color(*op['color'])
                    Rectangle(pos=(op['x'], op['y']), size=(self.car_width, self.car_height))

            Color(0.1, 0.1, 0.1)
            Rectangle(pos=(self.police_x, self.police_y), size=(self.car_width, self.car_height))

            if self.nitro_active:
                Color(1, 0.4, 0)
                Rectangle(pos=(self.car_x + 12, self.car_y - 25), size=(26, 25))
                
            Color(0.2, 0.65, 1)
            Rectangle(pos=(self.car_x, self.car_y), size=(self.car_width, self.car_height))

            if self.heli_active:
                Color(0.15, 0.15, 0.15, 0.8)
                Ellipse(pos=(self.heli_x - 45, self.heli_y - 20), size=(90, 40))

            hud_str = f"Rank: {self.player_position}/10 | Dist: {int(self.player_distance)}m | Time: {self.time_left}s | Nitro: {int(self.nitro_energy)}%"
            self.render_text(hud_str, self.width / 2, self.height - 35, 16, (1, 1, 1), center=True)

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
