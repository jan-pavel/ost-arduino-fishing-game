import time
import urandom # 'random' is usually 'urandom' in MicroPython
import sys
import uselect # For checking serial input without blocking
from machine import Pin

# --- Hardware Setup ---
# Setup buttons on A2 and A3 as requested
# Note: Depending on your specific Arduino board (Portenta, Nano RP2040), 
# you might need to use the integer GPIO number (e.g., 26, 27) instead of "A2".
try:
    btn_start = Pin("A2", Pin.IN)
    btn_reset = Pin("A3", Pin.IN)
except ValueError:
    # Fallback for generic boards if string names fail
    print("Pin name error: Trying generic GPIO 2 and 3...")
    btn_start = Pin(2, Pin.IN)
    btn_reset = Pin(3, Pin.IN)

# --- Game Configuration ---
GAME_DURATION_MS = 30000  # 30 seconds
FISH_DURATION_MS = 5000   # 5 seconds
NUM_FISH = 5

class FishingGame:
    def __init__(self):
        self.reset_game()
        
        # Button state tracking for edge detection
        self.last_start_val = 0
        self.last_reset_val = 0
        
        # Setup Serial Input (Non-blocking)
        self.poll_obj = uselect.poll()
        self.poll_obj.register(sys.stdin, uselect.POLLIN)

    def reset_game(self):
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1
        self.game_start_ticks = 0
        self.fish_start_ticks = 0
        self.message = "Ready."
        print("\n" * 5) # Clear space
        print("--- MICROPYTHON FISHING ---")
        print("Waiting... Press Button A2 (Start) to begin.")

    def start_game(self):
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            self.game_start_ticks = time.ticks_ms()
            print("\n!!! GAME STARTED !!!")
            print("Type 1-5 in Serial Monitor to catch fish!")
            self.spawn_new_fish()

    def spawn_new_fish(self):
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = urandom.randint(1, NUM_FISH)
        
        self.fish_start_ticks = time.ticks_ms()
        print(f"\n--> NEW FISH at Position [{self.current_fish}]")
        print("    [1] [2] [3] [4] [5]")
        # Create a simple visual arrow
        arrow = "    " + "    " * (self.current_fish - 1) + "^^^"
        print(arrow)

    def catch_fish(self, fish_num):
        if self.state != "PLAYING":
            return

        if fish_num == self.current_fish:
            self.score += 1
            print(f"*** CAUGHT fish {fish_num}! Score: {self.score}")
            self.spawn_new_fish()
        else:
            print(f"X Missed! You tried {fish_num}, fish is at {self.current_fish}")

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

    def check_buttons(self):
        # Invert logic? Usually 1 is pressed, unless using Pull-UP (then 0 is pressed)
        # Adjust `== 1` to `== 0` if your buttons trigger when grounded.
        curr_start = btn_start.value()
        curr_reset = btn_reset.value()

        # Edge Detection: Start (A2)
        if curr_start == 1 and self.last_start_val == 0:
            if self.state == "IDLE" or self.state == "GAME_OVER":
                self.start_game()
        
        # Edge Detection: Reset (A3)
        if curr_reset == 1 and self.last_reset_val == 0:
            self.reset_game()

        self.last_start_val = curr_start
        self.last_reset_val = curr_reset

    def check_serial_input(self):
        """
        Checks if user typed a number (1-5) into the Serial Monitor
        """
        # Check if characters are available in stdin
        if self.poll_obj.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if ch in '12345':
                    self.catch_fish(int(ch))
                elif ch == 's':
                    if self.state == "IDLE": self.start_game()
                elif ch == 'r':
                    self.reset_game()

    def update(self):
        if self.state == "PLAYING":
            now = time.ticks_ms()
            
            # Check Game Timer (30s)
            if time.ticks_diff(now, self.game_start_ticks) > GAME_DURATION_MS:
                self.end_game()
                return

            # Check Fish Timer (5s)
            if time.ticks_diff(now, self.fish_start_ticks) > FISH_DURATION_MS:
                self.fish_timeout()

    def loop(self):
        while True:
            self.check_buttons()
            self.check_serial_input()
            self.update()
            time.sleep(0.05) # Small delay to save CPU

# --- Run ---
game = FishingGame()
game.loop()