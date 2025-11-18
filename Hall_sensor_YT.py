from machine import Pin
import time

hall = Pin("A2", Pin.IN)

while True:
    value = hall.value()

    if value >= 0.5:
        print("Magnet detected: YES")
    else:
        print("Magnet detected: NO")

    time.sleep(0.2)