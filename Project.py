import time
import urandom
import sys
import uselect
from machine import Pin, I2C, ADC
from time import ticks_diff, ticks_ms

# ==========================================
# 1. TIMER CLASS
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
            return 0 # Return 0 if not started yet to prevent errors
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
                self.start() # Restart for repeating timers

# ==========================================
# 2. HARDWARE SETUP
# ==========================================

# --- Buttons ---
try:
    btn_start = Pin("A2", Pin.IN)
    btn_reset = Pin("A3", Pin.IN)
except ValueError:
    print("Pin name error: Trying generic GPIO 2 and 3...")
    btn_start = Pin(2, Pin.IN)
    btn_reset = Pin(3, Pin.IN)

# --- LED ---
try:
    pin_led = Pin("D8", Pin.OUT)
except ValueError:
    print("Pin D8 error: Trying generic GPIO 4...")
    pin_led = Pin(4, Pin.OUT) 

# --- Hall Sensor ---
try:
    # Using A0 (GPIO 1 on Arduino Nano ESP32)
    hall_sensor = ADC(Pin(1)) 
    hall_sensor.atten(ADC.ATTN_11DB) # Full range: 3.3v
    print("Hall Sensor Initialized on Pin A0/1")
except Exception as e:
    print(f"Hall Sensor Error: {e}")
    hall_sensor = None

# --- LCD ---
HAS_LCD = False
lcd = None
try:
    from lcd_i2c import LCD
    i2c_obj = I2C(1) 
    LCD_ADDR = 0x20
    lcd = LCD(LCD_ADDR, 16, 2, i2c=i2c_obj)
    lcd.begin()
    lcd.print("Fishing Game") 
    HAS_LCD = True
    print("LCD Found and Initialized.")
except Exception as e:
    print(f"LCD Error (Running without screen): {e}")
    HAS_LCD = False

# ==========================================
# 3. GAME CONFIGURATION
# ==========================================
GAME_DURATION_MS = 30000  # 30 seconds
FISH_DURATION_MS = 5000   # 5 seconds
NUM_FISH = 5
HALL_THRESHOLD = 28000 

# ==========================================
# 4. GAME CLASS
# ==========================================
class FishingGame:
    def __init__(self):
        # Game State
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        
        # Button Debouncing (Keeping manual logic for Buttons is usually better/simpler)
        self.last_start_val = 0
        self.last_reset_val = 0
        
        # Sensor Tracking
        self.sensor_triggered = False 

        # --- INITIALIZE TIMERS ---
        
        # 1. Main Game Timer (30s, One Shot)
        self.game_timer = Timer(GAME_DURATION_MS, one_shot=True)
        self.game_timer.on_timer_end = self.end_game

        # 2. Fish Patience Timer (5s, One Shot)
        self.fish_timer = Timer(FISH_DURATION_MS, one_shot=True)
        self.fish_timer.on_timer_end = self.fish_timeout

        # 3. LCD Update Timer (200ms, Repeating)
        self.lcd_timer = Timer(200, one_shot=False)
        self.lcd_timer.on_timer_end = self.refresh_display

        # 4. LED Blink Timer (300ms, Repeating - used in Game Over)
        self.led_timer = Timer(300, one_shot=False)
        self.led_timer.on_timer_end = self.toggle_led_state
        self.led_state = 0

        # Serial Input
        self.poll_obj = uselect.poll()
        self.poll_obj.register(sys.stdin, uselect.POLLIN)
        
        self.reset_game()

    def reset_game(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        
        # Stop all timers
        self.game_timer.stop()
        self.fish_timer.stop()
        self.lcd_timer.stop()
        self.led_timer.stop()
        
        pin_led.value(0)
        
        print("\n" * 5)
        print("--- MICROPYTHON FISHING ---")
        print("Waiting... Press Button A2 (Start) to begin.")
        self.update_lcd("FISHING GAME", "Press Start")

    def start_game(self):
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            
            print("\n!!! GAME STARTED !!!")
            print("Use the MAGNET to catch the fish!")
            
            # Start Timers
            self.game_timer.start()
            self.lcd_timer.start()
            
            self.spawn_new_fish()
            self.update_lcd("GO! Catch Fish!", f"Score: {self.score}")

    def spawn_new_fish(self):
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(1, NUM_FISH)
        
        # Reset/Start the fish timer for this new fish
        self.fish_timer.start()
        
        print(f"\n--> NEW FISH at Position [{self.current_fish}]")
        arrow = "    " + "    " * (self.current_fish - 1) + "^^^"
        print("    [1] [2] [3] [4] [5]")
        print(arrow)
        
        # Force an immediate LCD update
        self.refresh_display()

    def catch_fish(self, fish_num):
        if self.state != "PLAYING":
            return

        if fish_num == self.current_fish:
            self.score += 1
            print(f"*** CAUGHT fish {fish_num}! Score: {self.score}")
            
            # Stop the fish timer immediately so it doesn't timeout while we blink
            self.fish_timer.stop()
            
            # Little victory blink (Blocking is okay for short effect)
            pin_led.value(0)
            time.sleep(0.1)
            pin_led.value(1)
            
            self.spawn_new_fish()
        else:
            print(f"X Missed! Tried {fish_num}, fish at {self.current_fish}")

    def fish_timeout(self):
        # This function is called automatically by self.fish_timer
        print(f"!!! Too slow! Fish {self.current_fish} got away.")
        
        # Failure Blink
        for _ in range(3):
            pin_led.value(0)
            time.sleep(0.1)
            pin_led.value(1)
            time.sleep(0.1)
            
        self.spawn_new_fish()

    def end_game(self):
        # This function is called automatically by self.game_timer
        self.state = "GAME_OVER"
        self.current_fish = -1
        
        # Stop game logic timers
        self.fish_timer.stop()
        self.lcd_timer.stop()
        
        # Start the blink timer for Game Over effect
        self.led_timer.start()
        
        print("\n" + "="*30)
        print(f"TIME'S UP! Final Score: {self.score}")
        print("Press Button A3 (Reset) to play again.")
        print("="*30 + "\n")
        self.update_lcd("GAME OVER", f"Final Score: {self.score}")

    def refresh_display(self):
        # Called automatically by self.lcd_timer every 200ms
        if self.state == "PLAYING":
            # Calculate remaining time using the timer property
            elapsed = self.game_timer.elapsed_ms
            time_left_ms = GAME_DURATION_MS - elapsed
            time_left_sec = max(0, time_left_ms // 1000)
            
            self.update_lcd(f"Time: {time_left_sec}s", f"Score: {self.score}")
            
            # Keep LED on during play
            pin_led.value(1)

    def toggle_led_state(self):
        # Called automatically by self.led_timer during GAME_OVER
        if self.state == "GAME_OVER":
            self.led_state = not self.led_state
            pin_led.value(self.led_state)
        else:
            self.led_timer.stop() # Safety stop

    # --- Hardware Handling ---

    def check_buttons(self):
        curr_start = btn_start.value()
        curr_reset = btn_reset.value()

        if curr_start == 1 and self.last_start_val == 0:
            if self.state == "IDLE" or self.state == "GAME_OVER":
                self.start_game()
        
        if curr_reset == 1 and self.last_reset_val == 0:
            self.reset_game()

        self.last_start_val = curr_start
        self.last_reset_val = curr_reset

    def check_hall_sensor(self):
        if self.state != "PLAYING" or hall_sensor is None:
            return

        # Read analog value (0 - 65535)
        val = hall_sensor.read_u16()
        
        is_magnet_near = (val < HALL_THRESHOLD)

        if is_magnet_near and not self.sensor_triggered:
            self.sensor_triggered = True
            self.catch_fish(self.current_fish)
            
        elif not is_magnet_near:
            self.sensor_triggered = False

    def check_serial_input(self):
        if self.poll_obj.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if ch in '12345':
                    self.catch_fish(int(ch))
                elif ch == 's':
                    if self.state == "IDLE": self.start_game()
                elif ch == 'r':
                    self.reset_game()

    def update_lcd(self, line1, line2):
        if not HAS_LCD:
            return
        try:
            lcd.clear()
            lcd.print(str(line1))
            if hasattr(lcd, 'move_to'): lcd.move_to(0, 1)
            elif hasattr(lcd, 'setCursor'): lcd.setCursor(0, 1)
            elif hasattr(lcd, 'set_cursor'): lcd.set_cursor(0, 1)
            lcd.print(str(line2))
        except Exception as e:
            print(f"LCD Write Error: {e}")

    def loop(self):
        while True:
            # 1. Check Hardware Inputs
            self.check_buttons()
            self.check_serial_input()
            self.check_hall_sensor()
            
            # 2. Update Timers (Logic is now inside the Timer classes)
            self.game_timer.update()
            self.fish_timer.update()
            self.lcd_timer.update()
            self.led_timer.update()
            
            # 3. Small sleep to save CPU
            time.sleep(0.01)

# --- Run ---
game = FishingGame()
game.loop()