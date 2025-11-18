import time
import urandom # 'random' is usually 'urandom' in MicroPython
import sys
import uselect # For checking serial input without blocking
from machine import Pin, I2C

# --- Hardware Setup ---

# 1. BUTTONS setup
try:
    btn_start = Pin("A2", Pin.IN)
    btn_reset = Pin("A3", Pin.IN)
except ValueError:
    # Fallback for generic boards
    print("Pin name error: Trying generic GPIO 2 and 3...")
    btn_start = Pin(2, Pin.IN)
    btn_reset = Pin(3, Pin.IN)

# 2. LCD setup
HAS_LCD = False
lcd = None
try:
    # Try to import the library provided
    from lcd_i2c import LCD
    
    # Initialize I2C (Port 1 is common, but might need Pin definitions on some boards)
    i2c_obj = I2C(1) 
    
    LCD_ADDR = 0x27
    # Note: Adjust parameters if your library expects a different order
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

class FishingGame:
    def __init__(self):
        # Button state tracking
        self.last_start_val = 0
        self.last_reset_val = 0
        
        # LCD update timing
        self.last_lcd_update = 0
        self.lcd_interval = 200 
        
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
        
        # Console Output
        print("\n" * 5)
        print("--- MICROPYTHON FISHING ---")
        print("Waiting... Press Button A2 (Start) to begin.")
        
        # LCD Output
        self.update_lcd("FISHING GAME", "Press Start")

    def start_game(self):
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            self.game_start_ticks = time.ticks_ms()
            print("\n!!! GAME STARTED !!!")
            print("Type 1-5 or use Sensors!")
            self.spawn_new_fish()
            self.update_lcd("GO! Catch Fish!", f"Score: {self.score}")

    def spawn_new_fish(self):
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(1, NUM_FISH)
        
        self.fish_start_ticks = time.ticks_ms()
        
        # Visual feedback on Console
        print(f"\n--> NEW FISH at Position [{self.current_fish}]")
        arrow = "    " + "    " * (self.current_fish - 1) + "^^^"
        print("    [1] [2] [3] [4] [5]")
        print(arrow)
        
        # Force immediate LCD update
        self.last_lcd_update = 0 
        self.display_game_state()

    def catch_fish(self, fish_num):
        if self.state != "PLAYING":
            return

        if fish_num == self.current_fish:
            self.score += 1
            print(f"*** CAUGHT fish {fish_num}! Score: {self.score}")
            self.spawn_new_fish()
        else:
            print(f"X Missed! Tried {fish_num}, fish at {self.current_fish}")

    def fish_timeout(self):
        print(f"!!! Too slow! Fish {self.current_fish} got away.")
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

    # --- LCD HELPER FUNCTIONS ---
    def update_lcd(self, line1, line2):
        """
        Safely updates the LCD if it exists.
        Uses multiple checks to find the correct cursor movement method.
        """
        if not HAS_LCD:
            return
        
        try:
            lcd.clear()
            lcd.print(str(line1))
            
            # --- FIX FOR SECOND LINE ---
            # Depending on the exact library version, the command changes.
            # We try all common variations to ensure it works.
            if hasattr(lcd, 'move_to'):
                lcd.move_to(0, 1)     # Standard for brainelectronics (Col, Row)
            elif hasattr(lcd, 'setCursor'):
                lcd.setCursor(0, 1)   # Standard for Arduino-ports (Col, Row)
            elif hasattr(lcd, 'set_cursor'):
                lcd.set_cursor(0, 1)  # Common Snake_case variant
            else:
                # If no method found, we might be stuck on line 1. 
                # Try printing enough spaces to wrap? (Not ideal but a fallback)
                pass 
            
            lcd.print(str(line2))
            
        except Exception as e:
            print(f"LCD Write Error: {e}")

    def display_game_state(self):
        """Calculates time and updates the screen during gameplay."""
        if self.state == "PLAYING":
            now = time.ticks_ms()
            
            if time.ticks_diff(now, self.last_lcd_update) > self.lcd_interval:
                
                time_left_ms = GAME_DURATION_MS - time.ticks_diff(now, self.game_start_ticks)
                time_left_sec = max(0, time_left_ms // 1000)
                
                line1 = f"Time: {time_left_sec}s"
                line2 = f"Score: {self.score}"
                
                self.update_lcd(line1, line2)
                self.last_lcd_update = now

    def update(self):
        if self.state == "PLAYING":
            now = time.ticks_ms()
            
            # Check Timers
            if time.ticks_diff(now, self.game_start_ticks) > GAME_DURATION_MS:
                self.end_game()
                return

            if time.ticks_diff(now, self.fish_start_ticks) > FISH_DURATION_MS:
                self.fish_timeout()
                
            # Update LCD
            self.display_game_state()

    def loop(self):
        while True:
            self.check_buttons()
            self.check_serial_input()
            self.update()
            time.sleep(0.05)

# --- Run ---
game = FishingGame()
game.loop()