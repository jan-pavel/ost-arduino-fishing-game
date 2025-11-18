import curses
import time
import random

# --- Game Configuration ---
GAME_DURATION = 30  # 30 seconds total game time
FISH_DURATION = 5   # 5 seconds to catch each fish
NUM_FISH = 5        # 5 positions

class FishingGame:
    """
    Manages the game state, logic, and rendering in the terminal.
    """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # --- Curses Setup ---
        curses.curs_set(0)  # Hide the blinking cursor
        self.stdscr.nodelay(True)  # Make getch() non-blocking
        curses.start_color()
        # Initialize color pairs (ID, foreground, background)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        self.reset_game()

    def reset_game(self):
        """Initializes or resets the game to the IDLE state."""
        self.state = "IDLE"
        self.score = 0
        self.current_fish = -1  # No fish active (1-5)
        self.game_start_time = 0
        self.fish_start_time = 0
        self.message = "Press 's' to start the game."
        self.message_color = 0

    def start_game(self):
        """Starts the 30-second game timer and spawns the first fish."""
        if self.state != "PLAYING":
            self.state = "PLAYING"
            self.score = 0
            self.game_start_time = time.time()
            self.message = "Game Started! Good luck!"
            self.message_color = 2
            self.spawn_new_fish()

    def spawn_new_fish(self):
        """Picks a new random fish and resets the 5-second timer."""
        # Pick a new fish that is different from the current one
        old_fish = self.current_fish
        while self.current_fish == old_fish or self.current_fish == -1:
            self.current_fish = random.randint(1, NUM_FISH)
        
        self.fish_start_time = time.time()
        self.message = f"--> New fish at position {self.current_fish}!"
        self.message_color = 3  # Yellow for new fish

    def catch_fish(self, fish_num):
        """Checks if the player's 'catch' (key press) is correct."""
        if self.state != "PLAYING":
            self.message = "Press 's' to start first."
            self.message_color = 1
            return

        if fish_num == self.current_fish:
            # --- SUCCESS ---
            self.score += 1
            self.message = f"*** CAUGHT! (Sensor {fish_num}) *** Score: {self.score}"
            self.message_color = 2  # Green for success
            self.spawn_new_fish()
        else:
            # --- FAILED (Wrong fish) ---
            self.message = f"-> Whoops! That's the wrong fish. Try for {self.current_fish}."
            self.message_color = 1  # Red for error

    def fish_timeout(self):
        """Called when the 5-second fish timer expires."""
        self.message = f"!!! Too slow for fish {self.current_fish}! (Blinks red)"
        self.message_color = 1  # Red for error
        self.spawn_new_fish()

    def end_game(self):
        """Called when the 30-second game timer expires."""
        self.state = "GAME_OVER"
        self.current_fish = -1  # Turn off all fish
        self.message = f"!!! TIME'S UP !!! Final Score: {self.score}"
        self.message_color = 3

    def handle_input(self, key):
        """Processes user key presses."""
        if key == ord('q'):
            return False  # Signal to quit the game
        elif key == ord('s'):
            self.start_game()
        elif key == ord('r'):
            self.reset_game()
        elif key in [ord(str(i)) for i in range(1, NUM_FISH + 1)]:
            self.catch_fish(int(chr(key)))
        
        return True  # Signal to continue

    def update_state(self):
        """Checks timers and updates game state accordingly."""
        if self.state == "PLAYING":
            now = time.time()
            # 1. Check if the main 30-second game timer is up
            if now - self.game_start_time > GAME_DURATION:
                self.end_game()
            # 2. Check if the 5-second fish timer is up
            elif now - self.fish_start_time > FISH_DURATION:
                self.fish_timeout()

    def draw(self):
        """Renders the game UI to the terminal screen."""
        self.stdscr.clear()
        
        # --- Header ---
        self.stdscr.addstr(0, 2, "--- Python Fishing Game Simulator ---")
        self.stdscr.addstr(1, 2, "Controls: [s] Start | [r] Reset | [q] Quit")
        
        # --- Fish "Rectangle" ---
        # Draw all 5 positions
        self.stdscr.addstr(5, 5, "[1]")
        self.stdscr.addstr(5, 15, "[2]")
        self.stdscr.addstr(7, 10, "[5]")
        self.stdscr.addstr(9, 5, "[3]")
        self.stdscr.addstr(9, 15, "[4]")

        # Highlight the active fish
        if self.state == "PLAYING" and self.current_fish != -1:
            positions = {
                1: (5, 5, "[1]"), 2: (5, 15, "[2]"),
                3: (9, 5, "[3]"), 4: (9, 15, "[4]"),
                5: (7, 10, "[5]")
            }
            y, x, text = positions[self.current_fish]
            # Draw the active fish in reverse (highlighted)
            self.stdscr.addstr(y, x, text, curses.A_REVERSE)

        # --- Game State UI ---
        if self.state == "IDLE":
            self.stdscr.addstr(4, 2, "Press 's' to start.")

        elif self.state == "PLAYING":
            # Calculate remaining times
            game_time_left = max(0, GAME_DURATION - (time.time() - self.game_start_time))
            fish_time_left = max(0, FISH_DURATION - (time.time() - self.fish_start_time))
            
            self.stdscr.addstr(12, 2, f"Game Time Left: {game_time_left:05.2f}s")
            self.stdscr.addstr(13, 2, f"Fish Time Left: {fish_time_left:05.2f}s", 
                               (curses.color_pair(1) if fish_time_left < 1.5 else 0))
            self.stdscr.addstr(14, 2, f"Score: {self.score}", curses.A_BOLD)

        elif self.state == "GAME_OVER":
            self.stdscr.addstr(6, 2, "====================")
            self.stdscr.addstr(7, 2, "!!! GAME OVER !!!")
            self.stdscr.addstr(8, 2, f"Your Final Score: {self.score}", curses.A_BOLD)
            self.stdscr.addstr(9, 2, "====================")
            self.stdscr.addstr(11, 2, "Press 'r' to play again.")

        # --- Status Message ---
        # *** FIX IS HERE ***
        # Wrap in try/except to prevent crashing if window is too small
        try:
            self.stdscr.addstr(16, 2, self.message, curses.color_pair(self.message_color))
        except curses.error:
            # This fails if the window is too small. We can safely ignore it.
            pass
        
        self.stdscr.refresh()

    def run(self):
        """The main game loop."""
        while True:
            # 1. Handle user input
            key = self.stdscr.getch()
            if not self.handle_input(key):
                break  # Quit loop
            
            # 2. Update game state (check timers)
            self.update_state()
            
            # 3. Draw the current state to the screen
            self.draw()
            
            # 4. Sleep to prevent 100% CPU usage
            time.sleep(0.05)  # ~20 frames per second


def main(stdscr):
    """
    Wrapper function to safely run the curses application.
    """
    game = FishingGame(stdscr)
    game.run()

if __name__ == "__main__":
    # curses.wrapper handles all terminal setup and cleanup
    curses.wrapper(main)
