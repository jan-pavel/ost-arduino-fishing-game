# ost-arduino-fishing-game
A standalone, wireless interactive fishing game powered by MicroPython and ESP-NOW.

---

## 🎣 Concept Description
This project creates a physical "arcade-style" gaming experience. It eliminates the need for a computer connection during gameplay by running logic directly on the microcontrollers.

The system consists of two wireless modules:
1.  **The Game Controller (Sender):** Handles the game logic, displays time/score, reads hall sensors (magnets), and reads buttons.
2.  **The Light Board (Receiver):** Receives wireless commands via ESP-NOW to light up specific LEDs corresponding to the fish.

**Goal:** Players use a magnetic fishing rod to find and "catch" the currently illuminated fish before the 5-second timer runs out.

---

## 🕹 Instructions & Interactions

### Game Start
1.  Ensure the device is powered on.
2.  Press the **Start Button** (Blue/Green).
3.  Watch the displays for the **Countdown**:
    * The displays will count down: **3... 2... 1... GO!**
    * The LEDs will blink in sync with the countdown.

### How to Play
- A 30-second game timer begins.
- One specific LED (Fish 1–5) will light up wirelessly.
- Move the magnetic fishing rod to the corresponding sensor.
- **If you are fast enough:** The sensor triggers, the score increases, and a new fish is selected immediately.
- **If you are too slow (>5s):** The fish "escapes" (LED turns off), and a new position is chosen.

### Game Over
- When 30 seconds expire, the game ends.
- The final score flashes on the display.
- Press the **Reset Button** (Red) to reset the system to IDLE mode.

---

## 🛠 Requirements: Software & Hardware

### Software
- **Firmware:** MicroPython (flashed on both ESP32 boards).
- **IDE:** Thonny IDE or VS Code (with Pymakr extension).
- **Libraries:**
    - `tm1637.py` (For 7-segment displays).
    - `espnow`, `network`, `machine` (Built-in MicroPython libraries).

### Hardware
- **2x ESP32 Boards** (Nano form factor recommended).
- **2x TM1637 Displays** (One for Time, one for Score).
- **5x Hall Effect Sensors** (Digital switch type).
- **5x LEDs** (Standard or Grove LEDs).
- **2x Buttons** (Start and Reset).
- **Magnetic Fishing Rod**.
- **Case** (Plexiglass/Wood construction).
- **Grove Shields** (for easy cabling).

---

## 🔌 Pin Configuration & Wiring

### Unit 1: Game Controller (Sender)
*Handles logic, sensors, and screens.*

| Component | Pin / Port | Function |
| :--- | :--- | :--- |
| **Start Button** | A0 | Starts Game / Countdown |
| **Reset Button** | A1 | Resets Game / Stops Timers |
| **Display 1 (Time)** | CLK: D2 / DIO: D3 | Shows remaining time |
| **Display 2 (Score)** | CLK: D4 / DIO: D5 | Shows score & status ("Strt", "End") |
| **Sensor 1** | A2 | Hall Sensor Fish 1 |
| **Sensor 2** | SCL | Hall Sensor Fish 2 |
| **Sensor 3** | A6 | Hall Sensor Fish 3 |
| **Sensor 4** | D6 | Hall Sensor Fish 4 |
| **Sensor 5** | RX | Hall Sensor Fish 5 |

### Unit 2: LED Board (Receiver)
*Receives wireless commands to light up fish.*

| Component | Pin / Port | Function |
| :--- | :--- | :--- |
| **LED 1** | A1 | Fish 1 Indicator |
| **LED 2** | A2 | Fish 2 Indicator |
| **LED 3** | D5 | Fish 3 Indicator |
| **LED 4** | RX | Fish 4 Indicator |
| **LED 5** | D8 | Fish 5 Indicator |

---

## 📸 Gallery

| Setup View | Top View |
|:---:|:---:|
|![](https://github.com/user-attachments/assets/cab7fb00-d752-40bb-a2ca-9ee4bc7d474d)|![](https://github.com/user-attachments/assets/d98c50ea-c9f9-47c0-9ff9-ec52a3003abb)|
| **Controller Wiring** | **Rod & Sensors** |
| ![](https://github.com/user-attachments/assets/ec0eaaac-d24b-4d43-8bc0-26b105b974b1) | ![](https://github.com/user-attachments/assets/60d49ae4-be34-4491-993e-fa241ed03fab) |
| **Display Detail** | **Sensor Placement** |
| ![](https://github.com/user-attachments/assets/8cbbc3c8-decd-4ae0-ac48-51aade653cca) | ![](https://github.com/user-attachments/assets/b5dccd6a-18ec-4cea-b089-f9c24615d4c2) |
| **Case Construction** | **Full Assembly** |
| ![](https://github.com/user-attachments/assets/2444f242-15e3-441a-82ce-62df6c2d9df8) | ![](https://github.com/user-attachments/assets/5ce6d02a-b686-4760-b4b9-f6500258a70d) |

---

## 🔧 How to Build & Flash

### Step 1: Prepare the Hardware
1.  Assemble the sensors under the "water" surface.
2.  Mount the LEDs in the corresponding fish positions.
3.  Connect the TM1637 displays to the Controller ESP32.

### Step 2: Flash the Receiver (LED Board)
1.  Connect the Receiver ESP32 to your PC.
2.  Open **Thonny IDE**.
3.  Save the `Receiver Code` as `main.py` on the device.
4.  *Note: This board waits for "1-5", "OFF", or "ALL" commands via ESP-NOW.*

### Step 3: Flash the Sender (Game Controller)
1.  Connect the Sender ESP32 to your PC.
2.  Upload `tm1637.py` to the device storage.
3.  Save the `Sender Code` as `main.py` on the device.
4.  *Note: This board broadcasts commands to the broadcast address (`FF:FF:FF:FF:FF:FF`).*

### Step 4: Power Up
1.  Unplug both boards from the PC.
2.  Power them using USB power banks or wall adapters.
3.  The Receiver will initialize in listening mode.
4.  Press **Start (A0)** on the Controller to begin the wireless game.
