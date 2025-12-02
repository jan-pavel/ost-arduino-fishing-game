# OST Arduino Fishing Game
It is a standalone, wireless interactive fishing game powered by MicroPython and ESP-NOW. It creates a physical "arcade-style" gaming experience that eliminates the need for a computer connection during gameplay by running logic directly on the microcontrollers.

The system consists of two wireless modules:
1.  **The Game Controller (Sender):** Handles the game logic, displays time/score, reads hall sensors (magnets), and reads buttons.
2.  **The Light Board (Receiver):** Receives wireless commands via ESP-NOW to light up specific LEDs corresponding to the fish.

## Concept
**Goal:** Players use a magnetic fishing rod to find and "catch" the currently illuminated fish before the 5-second timer runs out.

### How to Play
**1. Game Start**
* Ensure the device is powered on.
* Press the **Start Button** (Blue/Green).
* Watch the displays for the **Countdown**: The displays will count down **3... 2... 1... GO!** and the LEDs will blink in sync.

**2. Gameplay**
* A 30-second game timer begins.
* One specific LED (Fish 1–5) will light up wirelessly.
* Move the magnetic fishing rod to the corresponding sensor.
* **If you are fast enough:** The sensor triggers, the score increases, and a new fish is selected immediately.
* **If you are too slow (>5s):** The fish "escapes" (LED turns off), and a new position is chosen.

**3. Game Over**
* When 30 seconds expire, the game ends.
* The final score flashes on the display.
* Press the **Reset Button** (Red) to reset the system to IDLE mode.

## Requirements
To build this project you will need:

### Hardware
* 2x [Arduino Nano ESP32](https://store.arduino.cc/products/nano-esp32-with-headers) (or similar ESP32 boards)
* 2x TM1637 Displays (One for Time, one for Score)
* 5x Hall Effect Sensors (Digital switch type)
* 5x LEDs (Standard or Grove LEDs)
* 2x Buttons (Start and Reset)
* Magnetic Fishing Rod
* Case materials (Plexiglass/Wood construction)
* Grove Shields (for easy cabling)
* USB-C cables and Power Banks

### Software
* [MicroPython Firmware](https://micropython.org/)
* [Arduino Lab for MicroPython](https://labs.arduino.cc/en/labs/micropython)
* [Arduino MicroPython Installer](https://labs.arduino.cc/en/labs/micropython-installer)

### Libraries
* `tm1637.py` (For 7-segment displays)
* `espnow` (Built-in)
* `network` (Built-in)
* `machine` (Built-in)

## How to build

### Wiring

**Unit 1: Game Controller (Sender)**
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

**Unit 2: LED Board (Receiver)**
*Receives wireless commands to light up fish.*

| Component | Pin / Port | Function |
| :--- | :--- | :--- |
| **LED 1** | A1 | Fish 1 Indicator |
| **LED 2** | A2 | Fish 2 Indicator |
| **LED 3** | D5 | Fish 3 Indicator |
| **LED 4** | RX | Fish 4 Indicator |
| **LED 5** | D8 | Fish 5 Indicator |

**Assembly Gallery**

| Setup View | Top View |
|:---:|:---:|
|![](https://github.com/user-attachments/assets/cab7fb00-d752-40bb-a2ca-9ee4bc7d474d)|![](https://github.com/user-attachments/assets/d98c50ea-c9f9-47c0-9ff9-ec52a3003abb)|
| **Controller Wiring** | **Rod & Sensors** |
| ![](https://github.com/user-attachments/assets/ec0eaaac-d24b-4d43-8bc0-26b105b974b1) | ![](https://github.com/user-attachments/assets/60d49ae4-be34-4491-993e-fa241ed03fab) |
| **Display Detail** | **Sensor Placement** |
| ![](https://github.com/user-attachments/assets/8cbbc3c8-decd-4ae0-ac48-51aade653cca) | ![](https://github.com/user-attachments/assets/b5dccd6a-18ec-4cea-b089-f9c24615d4c2) |
| **Case Construction** | **Full Assembly** |
| ![](https://github.com/user-attachments/assets/2444f242-15e3-441a-82ce-62df6c2d9df8) | ![](https://github.com/user-attachments/assets/5ce6d02a-b686-4760-b4b9-f6500258a70d) |

### Uploading the code

**1. Flash the Receiver (LED Board)**
* Connect the Receiver ESP32 to your PC.
* Open **Arduino Lab for MicroPython**.
* Save the `Receiver Code` as `main.py` on the device.
* *Note: This board waits for "1-5", "OFF", or "ALL" commands via ESP-NOW.*

**2. Flash the Sender (Game Controller)**
* Connect the Sender ESP32 to your PC.
* Upload the `tm1637.py` library to the device storage.
* Save the `Sender Code` as `main.py` on the device.
* *Note: This board broadcasts commands to the broadcast address (`FF:FF:FF:FF:FF:FF`).*

**3. Power Up**
* Unplug both boards from the PC.
* Power them using USB power banks or wall adapters.
* The Receiver will initialize in listening mode.
* Press **Start (A0)** on the Controller to begin the wireless game.

### Feedback and questions
If you are interested in this project and need to ask questions, feel free to get in touch with us!
