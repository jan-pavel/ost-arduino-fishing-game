import time
import urandom # 'random' is usually 'urandom' in MicroPython
import sys
import uselect # For checking serial input without blocking
from machine import Pin, I2C, ADC

# --- Hardware Setup ---

# 1. BUTTONS setup
try:
    btn_start = Pin("A2", Pin.IN)
    btn_reset = Pin("A3", Pin.IN)
except ValueError:
    print("Pin name error: Trying generic GPIO 2 and 3...")
    btn_start = Pin(2, Pin.IN)
    btn_reset = Pin(3, Pin.IN)

# 2. LED Setup
try:
    pin_led = Pin("D8", Pin.OUT)
except ValueError:
    print("Pin D8 error: Trying generic GPIO 4...")
    pin_led = Pin(4, Pin.OUT) 

# 3. HALL SENSOR Setup (The "Fishing Hook")
try:
    # Using A0 (GPIO 1 on Arduino Nano ESP32)
    # Adjust this Pin number if your wiring is different
    hall_sensor = ADC(Pin(1)) 
    hall_sensor.atten(ADC.ATTN_11DB) # Full range: 3.3v
    print("Hall Sensor Initialized on Pin A0/1")
except Exception as e:
    print(f"Hall Sensor Error: {e}")
    hall_sensor = None

# 4. LCD setup
HAS_LCD = False
lcd = None
try:
    from lcd_i2c import LCD
    i2c_obj = I2C(1) 
    LCD_ADDR = 0x27
    lcd = LCD(LCD_ADDR, 16, 2, i2c=i2c_obj)
    lcd.begin()
    lcd.print("Fishing Game") 
    HAS_LCD = True
    print("LCD Found and Initialized.")
except Exception as e:
    print(f"LCD Error (Running without screen): {e}")
    HAS_LCD = False

# --- Game Configuration ---
GAME_DURATION_MS = 30000  # 30 seconds
FISH_DURATION_MS = 5000   # 5 seconds
NUM_FISH = 5

# Based on your log: Resting is ~32300, Magnet is ~16000
# We set a threshold in the middle.
HALL_THRESHOLD = 28000 

class FishingGame:
    def __init__(self):
        # Button state tracking
        self.last_start_val = 0
        self.last_reset_val = 0
        
        # Sensor Tracking
        self.sensor_triggered = False # Prevents holding magnet to catch infinite fish
        
        # LCD update timing
        self.last_lcd_update = 0
        self.lcd_interval = 200 
        
        # LED Blink Timing
        self.led_blink_interval = 300 
        self.last_led_toggle = 0
        self.led_state = 0
        
        # Serial Input
        self.poll_obj = uselect.poll()
        self.poll_obj.register(sys.stdin, uselect.POLLIN)
        
        self.reset_game()

    def reset_game(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        self.game_start_ticks = 0
        self.fish_start_ticks = 0
        
        pin_led.value(0)
        
        print("\n" * 5)
        print("--- MICROPYTHON FISHING ---")
        print("Waiting... Press Button A2 (Start) to begin.")
        self.update_lcd("FISHING GAME", "Press Start")

    def start_game(self):
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            self.game_start_ticks = time.ticks_ms()
            print("\n!!! GAME STARTED !!!")
            print("Use the MAGNET to catch the fish!")
            self.spawn_new_fish()
            self.update_lcd("GO! Catch Fish!", f"Score: {self.score}")

    def spawn_new_fish(self):
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(1, NUM_FISH)
        
        self.fish_start_ticks = time.ticks_ms()
        
        print(f"\n--> NEW FISH at Position [{self.current_fish}]")
        arrow = "    " + "    " * (self.current_fish - 1) + "^^^"
        print("    [1] [2] [3] [4] [5]")
        print(arrow)
        
        self.last_lcd_update = 0 
        self.display_game_state()

    def catch_fish(self, fish_num):
        if self.state != "PLAYING":
            return

        if fish_num == self.current_fish:
            self.score += 1
            print(f"*** CAUGHT fish {fish_num}! Score: {self.score}")
            
            # Little victory blink
            pin_led.value(0)
            time.sleep(0.1)
            pin_led.value(1)
            
            self.spawn_new_fish()
        else:
            print(f"X Missed! Tried {fish_num}, fish at {self.current_fish}")

    def fish_timeout(self):
        print(f"!!! Too slow! Fish {self.current_fish} got away.")
        for _ in range(3):
            pin_led.value(0)
            time.sleep(0.1)
            pin_led.value(1)
            time.sleep(0.1)
        self.spawn_new_fish()

    def end_game(self):
        self.state = "GAME_OVER"
        self.current_fish = -1
        print("\n" + "="*30)
        print(f"TIME'S UP! Final Score: {self.score}")
        print("Press Button A3 (Reset) to play again.")
        print("="*30 + "\n")
        self.update_lcd("GAME OVER", f"Final Score: {self.score}")

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
        
        # LOGIC: Based on your logs, resting is ~32000.
        # When magnet is near, it drops to ~16000.
        # We check if value drops BELOW threshold.
        
        is_magnet_near = (val < HALL_THRESHOLD)

        if is_magnet_near and not self.sensor_triggered:
            # Magnet just arrived! Catch the CURRENT fish.
            self.sensor_triggered = True
            self.catch_fish(self.current_fish)
            
        elif not is_magnet_near:
            # Magnet moved away, reset trigger so we can catch again
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

    def handle_led_state(self):
        if self.state == "PLAYING":
            pin_led.value(1)
        elif self.state == "GAME_OVER":
            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_led_toggle) > self.led_blink_interval:
                self.led_state = not self.led_state
                pin_led.value(self.led_state)
                self.last_led_toggle = now
        else:
            pin_led.value(0)

    def update_lcd(self, line1, line2):
        if not HAS_LCD:
            return
        try:
            lcd.clear()
            lcd.print(str(line1))
            if hasattr(lcd, 'move_to'):
                lcd.move_to(0, 1)
            elif hasattr(lcd, 'setCursor'):
                lcd.setCursor(0, 1)
            elif hasattr(lcd, 'set_cursor'):
                lcd.set_cursor(0, 1)
            lcd.print(str(line2))
        except Exception as e:
            print(f"LCD Write Error: {e}")

    def display_game_state(self):
        if self.state == "PLAYING":
            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_lcd_update) > self.lcd_interval:
                time_left_ms = GAME_DURATION_MS - time.ticks_diff(now, self.game_start_ticks)
                time_left_sec = max(0, time_left_ms // 1000)
                self.update_lcd(f"Time: {time_left_sec}s", f"Score: {self.score}")
                self.last_lcd_update = now

    def update(self):
        self.handle_led_state()
        
        if self.state == "PLAYING":
            now = time.ticks_ms()
            if time.ticks_diff(now, self.game_start_ticks) > GAME_DURATION_MS:
                self.end_game()
                return
            if time.ticks_diff(now, self.fish_start_ticks) > FISH_DURATION_MS:
                self.fish_timeout()
            self.display_game_state()

    def loop(self):
        while True:
            self.check_buttons()
            self.check_serial_input()
            self.check_hall_sensor() # Check the magnet!
            self.update()
            time.sleep(0.05)

# --- Run ---
game = FishingGame()
game.loop()