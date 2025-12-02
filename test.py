from time import sleep_ms
import tm1637
from machine import Pin, ADC
tm1 = tm1637.TM1637(clk=Pin("D2"), dio=Pin("D3"))
tm2 = tm1637.TM1637(clk=Pin("D4"), dio=Pin("D5"))

# all LEDS on "88:88"
tm1.write([127, 255, 127, 127])
tm1.write(bytearray([127, 255, 127, 127]))
tm1.write(b'\x7F\xFF\x7F\x7F')
tm1.show('8888', True)
tm1.numbers(88, 88, True)

tm2.write([127, 255, 127, 127])
tm2.write(bytearray([127, 255, 127, 127]))
tm2.write(b'\x7F\xFF\x7F\x7F')
tm2.show('8888', True)
tm2.numbers(88, 88, True)

btn_start = Pin("A0", Pin.IN, Pin.PULL_UP)
btn_reset = Pin("A1", Pin.IN, Pin.PULL_UP)

hall_1 = Pin("A2", Pin.IN)
hall_1_analog = ADC(Pin("A3"))
hall_1_analog.atten(ADC.ATTN_11DB) # Full range: 3.3v
hall_2 = Pin("SCL", Pin.IN)
hall_3 = Pin("A6", Pin.IN)
hall_4 = Pin("D6", Pin.IN)
hall_5 = Pin("RX", Pin.IN)

while True:
  print(f"BTN Start: {btn_start.value()} BTN Reset: {btn_reset.value()}")
  print(f"Hall 1: {hall_1.value()} Analog: {hall_1_analog.read_u16()}")
  print(f"Hall 2: {hall_2.value()}")
  print(f"Hall 3: {hall_3.value()}")
  print(f"Hall 4: {hall_4.value()}")
  print(f"Hall 5: {hall_5.value()}")

  sleep_ms(100)
  