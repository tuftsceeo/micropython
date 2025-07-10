import pyb
import time, math
from array import array

class DISPLAY():
    def __init__(self):
        self.pixel_lut = [9,11,6,1,14,10,19,8,0,26,23,18,3,2,24,21,20,15,13,25,22,7,17,12,38,27,28,29,39,40,41,42,43,44,45,46,47]
        self.fullBrightness = 256*256-1
        self.display = bytearray(96)
        self.sclk = pyb.Pin(pyb.Pin.board.TLC_SCLK, pyb.Pin.AF_PP, alt=pyb.Pin.AF5_SPI1, pull= pyb.Pin.PULL_NONE)
        self.sout = pyb.Pin(pyb.Pin.board.TLC_SOUT, pyb.Pin.AF_PP, alt=pyb.Pin.AF5_SPI1, pull= pyb.Pin.PULL_NONE)
        self.sin = pyb.Pin(pyb.Pin.board.TLC_SIN,   pyb.Pin.AF_PP, alt=pyb.Pin.AF5_SPI1, pull= pyb.Pin.PULL_NONE)
        self.tlcLat = pyb.Pin(pyb.Pin.board.TLC_LAT, pyb.Pin.OUT, pull= pyb.Pin.PULL_NONE)
        self.gsclk = pyb.Pin(pyb.Pin('B15'),pyb.Pin.ALT, alt=pyb.Pin.AF9_TIM12, pull = pyb.Pin.PULL_NONE)
        
        self.spi = pyb.SPI(1, pyb.SPI.CONTROLLER,baudrate = 25000000, polarity=0, phase=0, bits=8, firstbit=pyb.SPI.MSB)
        self.display_on()
        self.power_led(0,0,1)

    def set(self, led, value = 256*256-1):
        self.display[led * 2] = value&0xFF
        self.display[led * 2 + 1] = (value >> 8)&0xFF
        
    def pixel_set(self, led, value = 256*256-1):
        if led not in range(len(self.pixel_lut)): return -1
        self.set(self.pixel_lut[led],value)
        
    def timer_init(self):
        #Power the LED display
        tim = pyb.Timer(12, freq=25000000)
        ch = tim.channel(2, pyb.Timer.PWM, pin=self.gsclk)  #machine.Pin('B15'))
        ch.pulse_width_percent(50)

    def display_update(self):
        self.spi.write(b'\x00')
        for i in range(96):
            self.spi.write(bytes(self.display[95 - i:96 - i]))
        self.tlcLat.on()
        time.sleep_us(1)
        self.tlcLat.off()
        
    def latch_ctrl(self, dc, mc, bc, fc): #(dc: uint8, mc: uint32, bc: uint32, fc: uint8):
        #dc = dot correction, mc = max current, bc = brightness control, fc - function control
        payload= bytearray()
        payload.append(1)                    # bit 768
        payload.append(0x96)                 # bits 760-767
        for i in range(48):
            payload.append(0)
        payload.append(fc >> 2)              # bits 368-375
        payload.append(fc << 6 | bc >> 15)   # bits 360-367
        payload.append(bc >> 7)              # bits 352-359
        payload.append(bc << 1 | mc >> 8)    # bits 344-351
        payload.append(mc)                   # bits 336-343  default is zero
        for i in range(42):
            payload.append(dc&0xFF)          # max dot correction value - bright as possible
        self.spi.write(payload)
        self.tlcLat.on()
        time.sleep_us(1)
        self.tlcLat.off()
    
    def display_on(self):
        self.tlcLat.off()
        for i in range(2):
            self.latch_ctrl(0xff, 0, 0x1fffff, 0x11)
        self.timer_init()
        
    def start(self):
        self.pixel_set(25)
        self.pixel_set(26)
        self.pixel_set(27)
        self.display_update()
        
    def matrix_led(self, x, y, b = 1.0):
        self.pixel_set(y*5+x, int(self.fullBrightness*b))
        self.display_update()
        
    def ble_led(self, r=0, g=1, b=0):
        self.pixel_set(25, self.fullBrightness*r)
        self.pixel_set(26, self.fullBrightness*g)
        self.pixel_set(27, self.fullBrightness*b)
        self.display_update()
        
    def power_led(self, r=0, g=0, b=1):
        #left and right leds
        self.pixel_set(28, self.fullBrightness*r)
        self.pixel_set(29, self.fullBrightness*g)
        self.pixel_set(30, self.fullBrightness*b)
        self.pixel_set(31, self.fullBrightness*r)
        self.pixel_set(32, self.fullBrightness*g)
        self.pixel_set(33, self.fullBrightness*b)
        self.display_update()

    def battery_led(self, r=1, g=0, b=0):
        self.pixel_set(34, self.fullBrightness*r)
        self.pixel_set(35, self.fullBrightness*g)
        self.pixel_set(36, self.fullBrightness*b)
        self.display_update()

    def full_test(self):
        for i in range(48):
            for b in range(0,self.fullBrightness,128):
                self.pixel_set(i,b)
                self.display_update()
                time.sleep(0.001)
            time.sleep(0.1)
            if i: self.pixel_set(i-1,0)