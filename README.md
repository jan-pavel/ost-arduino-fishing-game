# ost-arduino-fishing-game
An interactive fishing game combining Arduino hardware with a reflex-based terminal mini-game.

---

## 🎣 Concept Description
This project blends physical interaction with digital gameplay.  
Players use a magnetic fishing rod to “catch” illuminated fish, while a Python terminal game runs in real time:

- The terminal highlights which of the five fish is active.
- The physical installation lights up the same fish.
- Players try to catch the correct fish as quickly as possible.
- The software tracks reaction time, score, and session duration.

The goal is a mix of **coordination**, **speed**, and **playful tech exploration**.

---

## 🕹 Instructions & Interactions
*(Insert photos of the installation, fishing rod, LEDs, or terminal output.)*

### Game Start
- Press **s** to start the game.
- Each round lasts **30 seconds**.

### How to Play
- Every 5 seconds, a new “fish” appears (position 1–5).
- The active fish blinks in the terminal and lights up on the hardware.
- If you catch it correctly, you earn a point.
- Press the corresponding number **1–5** to catch the fish.

### Controls
| Key | Action |
|-----|--------|
| **s** | Start game |
| **r** | Reset game |
| **q** | Quit program |
| **1–5** | Attempt to catch fish |

---

## 🛠 Requirements: Software & Hardware

### Software
- Python 3.10 or higher  
- `curses` library (native on Linux/macOS, use `windows-curses` on Windows)  
- Arduino IDE  
- USB serial connection (optional for live communication)

### Hardware
- Arduino Nano
- LED stripes
- 5 Hall sensors
- Cables from the Hall sensors to the Grove Shield
- USB-C cable
- Magnetic fishing rod
- Case (in our case out of plexyglass and wood)
- Grove Shield for Arduino Nano with 10 slots

### Slotfunctions for the Grove Shield: Arduino 1 with 8 slots
| Slot | Function |
|-----|--------|
| **1** | Display 1 |
| **2** | Display 2 |
| **3** | Hall Sensor |
| **4** | Buttons |
| **5** | Hall Sensor |
| **6** | Hall Sensor |
| **7** | Hall Sensor |
| **8** | Hall Sensor |

### Slotfunctions for the Grove Shield: Arduino 2 with 5 slots
| Slot | Function |
|-----|--------|
| **1** | LED 1 |
| **2** | LED 2 |
| **3** | LED 3 |
| **4** | LED 4 |
| **5** | LED 5 |

### Pictures
| Picture | Picture|
|-----|--------|
|![](https://github.com/user-attachments/assets/cab7fb00-d752-40bb-a2ca-9ee4bc7d474d)|![](https://github.com/user-attachments/assets/d98c50ea-c9f9-47c0-9ff9-ec52a3003abb)|
| ![](https://github.com/user-attachments/assets/ec0eaaac-d24b-4d43-8bc0-26b105b974b1) | ![](https://github.com/user-attachments/assets/60d49ae4-be34-4491-993e-fa241ed03fab) |
| ![](https://github.com/user-attachments/assets/8cbbc3c8-decd-4ae0-ac48-51aade653cca) | ![](https://github.com/user-attachments/assets/b5dccd6a-18ec-4cea-b089-f9c24615d4c2) |
| ![](https://github.com/user-attachments/assets/2444f242-15e3-441a-82ce-62df6c2d9df8) | ![](https://github.com/user-attachments/assets/5ce6d02a-b686-4760-b4b9-f6500258a70d) |



---

## 🔧 How to Build

### Step 1: LED Fish Setup
- Place 5 LEDs at the designated “fish positions”.
- Connect each LED through a 220Ω resistor.
- Assign each LED to its own digital output pin on the Arduino.

### Step 2: Magnet Sensor Setup
- Mount one reed sensor under each fish.
- When the magnetic rod is placed above it, the sensor triggers.
- Connect each sensor to a digital input pin.

### Step 3: Program the Arduino
- Control which fish lights up  
- Detect which fish has been caught  
- Communicate states via serial to the Python program

*(Insert Arduino code snippets here.)*

### Step 4: Run the Python Game Logic
Start the game with:
```bash
python3 fishing_game.py
