import network
import espnow
from machine import Pin

# ==========================================
# 1. HARDWARE SETUP
# ==========================================
led1 = Pin("A1", Pin.OUT)
led2 = Pin("A2", Pin.OUT)
led3 = Pin("D5", Pin.OUT)
led4 = Pin("RX", Pin.OUT)
led5 = Pin("D8", Pin.OUT)

class LEDControl:
    @staticmethod
    def all_off():
        led1.off(); led2.off(); led3.off(); led4.off(); led5.off()
    
    @staticmethod
    def all_on():
        led1.on(); led2.on(); led3.on(); led4.on(); led5.on()

led_map = { "1": led1, "2": led2, "3": led3, "4": led4, "5": led5 }

# ==========================================
# 2. ESP-NOW SETUP
# ==========================================
station = network.WLAN(network.STA_IF)
station.active(True)
station.disconnect()

esp = espnow.ESPNow()
esp.active(True)

LEDControl.all_off()
print("--- Receiver Ready (Supports ALL/OFF) ---")

# ==========================================
# 3. MAIN LOOP
# ==========================================
while True:
    host, msg = esp.recv()
    if msg:
        try:
            command = msg.decode('utf-8').strip()
            
            if command == "OFF":
                LEDControl.all_off()
                
            elif command == "ALL":
                LEDControl.all_on()
                
            elif command in led_map:
                LEDControl.all_off()
                led_map[command].on()
                
        except Exception as e:
            print(f"Error: {e}")