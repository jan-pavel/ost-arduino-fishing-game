import network
import espnow
import time

# ==========================================
# 1. WIFI SETUP
# ==========================================
# ESP-NOW requires the WiFi interface to be active
station = network.WLAN(network.STA_IF)
station.active(True)
station.disconnect() # Ensure we aren't connected to a router

# ==========================================
# 2. ESP-NOW SETUP
# ==========================================
esp = espnow.ESPNow()
esp.active(True)

print("--- ESP-NOW Receiver Ready ---")
print("Waiting for commands from the Fishing Game...")

# ==========================================
# 3. MAIN LOOP
# ==========================================
while True:
    # esp.recv() returns a tuple: (mac_address, message)
    # If no message is waiting, it returns (None, None)
    host, msg = esp.recv()

    if msg:
        try:
            # Decode the message from bytes to string (e.g., b'1' -> '1')
            command = msg.decode('utf-8').strip()
            
            # --- Logic to handle commands ---
            if command == "OFF":
                print(f"[RX] Received 'OFF' -> Turn ALL LEDs OFF")
                
            elif command in ["1", "2", "3", "4", "5"]:
                print(f"[RX] Received '{command}'   -> Turn ON LED #{command} (and others OFF)")
                
            else:
                print(f"[RX] Unknown command: {command}")
                
        except UnicodeError:
            print("Error decoding message")
            
    # No sleep needed here usually, esp.recv() is fast. 
    # But a tiny sleep prevents the loop from hogging 100% CPU if you want.
    # time.sleep_ms(10)