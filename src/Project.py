import time
import urandom
import sys
import uselect
import network
import espnow
from machine import Pin
from time import ticks_diff, ticks_ms
import tm1637

# ==========================================
# 1. ESP-NOW SETUP
# ==========================================
BROADCAST_PEER = b'\xff\xff\xff\xff\xff\xff'

station = network.WLAN(network.STA_IF)
station.active(True)
station.disconnect()

esp = espnow.ESPNow()
esp.active(True)
try:
    esp.add_peer(BROADCAST_PEER)
except Exception:
    pass

# ==========================================
# 2. ROBUST TIMER CLASS
# ==========================================
class Timer:
    def __init__(self, duration_ms=None, one_shot=True):
        self._start_time = None
        self._duration_ms = duration_ms
        self._is_running = False
        self._one_shot = one_shot
        self._on_timer_end = None

    def start(self):
        self._start_time = ticks_ms()
        self._is_running = True

    def stop(self):
        self._is_running = False
        self._start_time = None

    @property
    def on_timer_end(self):
        return self._on_timer_end

    @on_timer_end.setter
    def on_timer_end(self, callback):
        self._on_timer_end = callback

    @property
    def elapsed_ms(self):
        # Fix: Explicitly check for None to avoid "0" timestamp issues
        if self._start_time is None or not self._is_running:
            return 0
        return ticks_diff(ticks_ms(), self._start_time)
    
    @property
    def has_ended(self):
        if self._duration_ms is None or not self._is_running:
            return False
        return self.elapsed_ms >= self._duration_ms

    def update(self):
        if not self._is_running:
            return
        
        if self.has_ended:
            # Trigger callback
            if callable(self._on_timer_end):
                self._on_timer_end()
            
            # Handle restart or stop
            if self._one_shot:
                self.stop()
            else:
                self.start() # Reset start time for repeating timers

# ==========================================
# 3. HARDWARE & GAME CONFIG
# ==========================================
# --- Buttons ---
try:
    btn_start = Pin("A0", Pin.IN, Pin.PULL_UP)
    btn_reset = Pin("A1", Pin.IN, Pin.PULL_UP)
except: pass

# --- Displays ---
try:
    display_time = tm1637.TM1637(clk=Pin("D2"), dio=Pin("D3"))
    display_score = tm1637.TM1637(clk=Pin("D4"), dio=Pin("D5"))
    display_time.brightness(2)
    display_score.brightness(2)
except: pass

# --- Hall Sensors ---
sensor_pins = ["A2", "SCL", "A6", "D6", "RX"]
hall_sensors = []
for p in sensor_pins:
    try: hall_sensors.append(Pin(p, Pin.IN))
    except: pass

GAME_DURATION_MS = 30000
FISH_DURATION_MS = 5000 
NUM_FISH = 5

# ==========================================
# 4. GAME LOGIC
# ==========================================
class FishingGame:
    def __init__(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        self.last_start_val = 1
        self.last_reset_val = 1
        self.sensor_triggered = False 

        # --- TIMERS ---
        # Main Game Timer (30s)
        self.game_timer = Timer(GAME_DURATION_MS, one_shot=True)
        self.game_timer.on_timer_end = self.end_game

        # Fish Timer (5s)
        self.fish_timer = Timer(FISH_DURATION_MS, one_shot=True)
        self.fish_timer.on_timer_end = self.fish_timeout

        # Display Update Timer (Refresh screen every 100ms)
        self.display_timer = Timer(100, one_shot=False)
        self.display_timer.on_timer_end = self.update_displays

        # Serial Input
        self.poll_obj = uselect.poll()
        self.poll_obj.register(sys.stdin, uselect.POLLIN)
        
        self.reset_game()

    def send_espnow_msg(self, msg):
        try: esp.send(BROADCAST_PEER, msg)
        except: pass

    def reset_game(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        
        self.game_timer.stop()
        self.fish_timer.stop()
        self.display_timer.stop()
        
        self.send_espnow_msg("OFF")
        print("--- READY ---")
        
        # Show Start/Ready screen
        display_time.numbers(0, 0, colon=True)
        display_score.show("Strt")

    def start_game(self):
        if self.state != "PLAYING":
            print("Countdown...")
            
            # --- START ANIMATION ---
            # 1. Blink "Strt"
            for _ in range(2):
                display_score.show("Strt")
                self.send_espnow_msg("ALL")
                time.sleep(0.3)
                display_score.show("    ")
                self.send_espnow_msg("OFF")
                time.sleep(0.3)
            
            # 2. Count 3, 2, 1
            for i in range(3, 0, -1):
                display_time.number(i)
                display_score.number(i)
                self.send_espnow_msg("ALL")
                time.sleep(0.6)
                
                display_time.show("    ")
                display_score.show("    ")
                self.send_espnow_msg("OFF")
                time.sleep(0.4)

            # 3. Go
            display_time.show(" Go ")
            display_score.show(" Go ")
            self.send_espnow_msg("ALL")
            time.sleep(0.5)
            self.send_espnow_msg("OFF")

            # --- START TIMERS NOW ---
            self.state = "PLAYING"
            self.score = 0
            print("!!! GO !!!")
            
            self.game_timer.start()
            self.display_timer.start()
            
            display_score.number(self.score)
            self.spawn_new_fish()

    def spawn_new_fish(self):
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(0, NUM_FISH - 1)
        
        # Reset the 5-second limit for the new fish
        self.fish_timer.start()
        self.sensor_triggered = False
        
        self.send_espnow_msg(str(self.current_fish + 1))
        print(f"Fish #{self.current_fish + 1}")

    def catch_fish(self):
        if self.state != "PLAYING": return

        self.score += 1
        print(f"CAUGHT! Score: {self.score}")
        display_score.number(self.score)
        
        # Stop timer momentarily to prevent timeout while catching
        self.fish_timer.stop()
        
        self.send_espnow_msg("OFF")
        time.sleep(0.1) 
        self.spawn_new_fish()

    def fish_timeout(self):
        print(f"Missed Fish #{self.current_fish + 1}")
        self.send_espnow_msg("OFF")
        time.sleep(0.1)
        self.spawn_new_fish()

    def end_game(self):
        self.state = "GAME_OVER"
        self.current_fish = -1
        
        self.game_timer.stop()
        self.fish_timer.stop()
        self.display_timer.stop()
        
        print(f"GAME OVER. Score: {self.score}")
        
        # --- END ANIMATION ---
        for _ in range(4):
            display_time.show("End ")
            display_score.number(self.score)
            self.send_espnow_msg("ALL")
            time.sleep(0.4)
            
            display_time.show("    ")
            display_score.show("    ")
            self.send_espnow_msg("OFF")
            time.sleep(0.4)

        display_time.show("End ")
        display_score.number(self.score)
        self.send_espnow_msg("OFF")

    def update_displays(self):
        if self.state == "PLAYING":
            elapsed = self.game_timer.elapsed_ms
            time_left_ms = GAME_DURATION_MS - elapsed
            
            # Ensure we don't display negative numbers
            if time_left_ms < 0: time_left_ms = 0
            
            time_left_sec = time_left_ms // 1000
            display_time.numbers(0, time_left_sec, colon=True)

    def check_inputs(self):
        # 1. Buttons
        curr_start = btn_start.value()
        curr_reset = btn_reset.value()
        if curr_start == 0 and self.last_start_val == 1:
            if self.state in ["IDLE", "GAME_OVER"]: self.start_game()
        if curr_reset == 0 and self.last_reset_val == 1:
            self.reset_game()
        self.last_start_val = curr_start
        self.last_reset_val = curr_reset

        # 2. Sensors
        if self.state == "PLAYING" and self.current_fish != -1:
            # Check the specific pin for the active fish
            if hall_sensors[self.current_fish].value() == 0:
                if not self.sensor_triggered:
                    self.sensor_triggered = True
                    self.catch_fish()
            else:
                self.sensor_triggered = False

        # 3. Serial
        if self.poll_obj.poll(0):
            ch = sys.stdin.read(1)
            if ch in '12345': 
                if int(ch)-1 == self.current_fish: self.catch_fish()
            elif ch == 's': self.start_game()
            elif ch == 'r': self.reset_game()

    def loop(self):
        while True:
            self.check_inputs()
            
            # Update all timers
            self.game_timer.update()
            self.fish_timer.update()
            self.display_timer.update()
            
            time.sleep(0.01)

# --- Run ---
game = FishingGame()
game.loop()