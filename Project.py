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
# 1. ESP-NOW SETUP (SENDER)
# ==========================================
# We use the Broadcast Address so we don't need to know the Receiver's MAC
BROADCAST_PEER = b'\xff\xff\xff\xff\xff\xff'

station = network.WLAN(network.STA_IF)
station.active(True)
station.disconnect() # Disconnect from any WiFi AP to use ESP-NOW cleanly

esp = espnow.ESPNow()
esp.active(True)
try:
    esp.add_peer(BROADCAST_PEER)
    print("ESP-NOW Initialized in Broadcast Mode")
except Exception as e:
    print(f"ESP-NOW Init Error (Peer might already exist): {e}")

# ==========================================
# 2. TIMER CLASS
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

    @property
    def duration_ms(self):
        return self._duration_ms
    
    @duration_ms.setter
    def duration_ms(self, value):
        if value is not None and value < 0:
            raise ValueError("Duration must be non-negative or None.")
        self._duration_ms = value

    @property
    def on_timer_end(self):
        return self._on_timer_end

    @on_timer_end.setter
    def on_timer_end(self, callback):
        if not callable(callback):
            raise ValueError("Callback must be callable.")
        self._on_timer_end = callback

    @property
    def elapsed_ms(self):
        if self._start_time is None:
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
            if callable(self._on_timer_end):
                self._on_timer_end()
            if self._one_shot:
                self.stop()
            else:
                self.start() 

# ==========================================
# 3. HARDWARE SETUP
# ==========================================

# --- Buttons ---
try:
    btn_start = Pin("A0", Pin.IN, Pin.PULL_UP)
    btn_reset = Pin("A1", Pin.IN, Pin.PULL_UP)
except Exception as e:
    print(f"Button Setup Error: {e}")

# --- TM1637 Displays ---
try:
    # Display 1: TIME (CLK=D2, DIO=D3)
    display_time = tm1637.TM1637(clk=Pin("D2"), dio=Pin("D3"))
    # Display 2: SCORE (CLK=D4, DIO=D5)
    display_score = tm1637.TM1637(clk=Pin("D4"), dio=Pin("D5"))
    
    display_time.brightness(2)
    display_score.brightness(2)
except Exception as e:
    print(f"Display Setup Error: {e}")

# --- Hall Sensors ---
# Fish 1: A2, Fish 2: SCL, Fish 3: A6, Fish 4: D6, Fish 5: RX
sensor_pins = ["A2", "SCL", "A6", "D6", "RX"]
hall_sensors = []

for pin_name in sensor_pins:
    try:
        hall_sensors.append(Pin(pin_name, Pin.IN))
    except Exception as e:
        print(f"Error setting up sensor on {pin_name}: {e}")

print(f"Sensors initialized: {len(hall_sensors)}")

# ==========================================
# 4. GAME CONFIGURATION
# ==========================================
GAME_DURATION_MS = 30000
FISH_DURATION_MS = 5000 
NUM_FISH = 5

# ==========================================
# 5. GAME CLASS
# ==========================================
class FishingGame:
    def __init__(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        
        # Button Logic
        self.last_start_val = 1
        self.last_reset_val = 1
        
        # Sensor Logic
        self.sensor_triggered = False 

        # --- TIMERS ---
        self.game_timer = Timer(GAME_DURATION_MS, one_shot=True)
        self.game_timer.on_timer_end = self.end_game

        self.fish_timer = Timer(FISH_DURATION_MS, one_shot=True)
        self.fish_timer.on_timer_end = self.fish_timeout

        self.display_timer = Timer(100, one_shot=False)
        self.display_timer.on_timer_end = self.update_displays

        # Serial Input
        self.poll_obj = uselect.poll()
        self.poll_obj.register(sys.stdin, uselect.POLLIN)
        
        self.reset_game()

    def send_espnow_msg(self, msg):
        """Helper to send data to the LED Receiver"""
        try:
            esp.send(BROADCAST_PEER, msg)
            # print(f"(Sent '{msg}' via ESP-NOW)") # Uncomment for debug
        except Exception as e:
            print(f"ESP-NOW Send Failed: {e}")

    def reset_game(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        
        self.game_timer.stop()
        self.fish_timer.stop()
        self.display_timer.stop()
        
        # Tell Receiver to turn off all LEDs
        self.send_espnow_msg("OFF")
        
        print("\n" * 5)
        print("--- MICROPYTHON FISHING ---")
        print("Press Button A0 to Start.")
        
        display_time.numbers(0, 0, colon=True)
        display_score.show("0000")

    def start_game(self):
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            
            print("\n!!! GAME STARTED !!!")
            
            self.game_timer.start()
            self.display_timer.start()
            display_score.number(self.score)
            
            self.spawn_new_fish()

    def spawn_new_fish(self):
        old_fish = self.current_fish
        
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(0, NUM_FISH - 1)
        
        self.fish_timer.start()
        self.sensor_triggered = False
        
        # --- SEND LED COMMAND ---
        # We send the number (1 to 5) as a string
        msg = str(self.current_fish + 1)
        self.send_espnow_msg(msg)
        
        print(f"\n--> Catch Fish #{self.current_fish + 1}")

    def catch_fish(self):
        if self.state != "PLAYING":
            return

        self.score += 1
        print(f"*** CAUGHT! Score: {self.score}")
        display_score.number(self.score)
        
        # Stop fish timer
        self.fish_timer.stop()
        
        # Send OFF momentarily (optional, gives a visual blink effect on receiver)
        self.send_espnow_msg("OFF")
        time.sleep(0.1) # Short pause
        
        self.spawn_new_fish()

    def fish_timeout(self):
        print(f"!!! Too slow! Fish #{self.current_fish + 1} got away.")
        
        # Blink/OFF effect
        self.send_espnow_msg("OFF")
        time.sleep(0.1)
        
        self.spawn_new_fish()

    def end_game(self):
        self.state = "GAME_OVER"
        self.current_fish = -1
        
        self.fish_timer.stop()
        self.display_timer.stop()
        
        # Turn off remote LEDs
        self.send_espnow_msg("OFF")
        
        print("\n=== TIME'S UP ===")
        print(f"Final Score: {self.score}")
        print("Press Button A1 to Reset.")
        
        display_time.numbers(0, 0, colon=True)
        display_score.show("End ")
        time.sleep(1)
        display_score.number(self.score)

    def update_displays(self):
        if self.state == "PLAYING":
            elapsed = self.game_timer.elapsed_ms
            time_left_ms = GAME_DURATION_MS - elapsed
            time_left_sec = max(0, time_left_ms // 1000)
            display_time.numbers(0, time_left_sec, colon=True)

    # --- Hardware Input Handling ---

    def check_buttons(self):
        curr_start = btn_start.value()
        curr_reset = btn_reset.value()

        # Start Button (Active LOW)
        if curr_start == 0 and self.last_start_val == 1:
            if self.state == "IDLE" or self.state == "GAME_OVER":
                self.start_game()
        
        # Reset Button (Active LOW)
        if curr_reset == 0 and self.last_reset_val == 1:
            self.reset_game()

        self.last_start_val = curr_start
        self.last_reset_val = curr_reset

    def check_active_sensor(self):
        if self.state != "PLAYING" or self.current_fish == -1:
            return

        active_sensor_pin = hall_sensors[self.current_fish]
        sensor_val = active_sensor_pin.value()
        
        # NOTE: Assuming Hall Sensor goes LOW (0) when magnet is near
        is_magnet_near = (sensor_val == 0)

        if is_magnet_near and not self.sensor_triggered:
            self.sensor_triggered = True
            self.catch_fish()
        elif not is_magnet_near:
            self.sensor_triggered = False

    def check_serial_input(self):
        if self.poll_obj.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if ch in '12345':
                    idx = int(ch) - 1
                    if idx == self.current_fish:
                        self.catch_fish()
                elif ch == 's':
                    if self.state == "IDLE": self.start_game()
                elif ch == 'r':
                    self.reset_game()

    def loop(self):
        while True:
            self.check_buttons()
            self.check_active_sensor()
            self.check_serial_input()
            
            self.game_timer.update()
            self.fish_timer.update()
            self.display_timer.update()
            
            time.sleep(0.01)

# --- Run ---
game = FishingGame()
game.loop()