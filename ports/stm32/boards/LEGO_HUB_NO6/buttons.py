import pyb

class BUTTONS():
    def __init__(self):
        self.btns = pyb.ADC(pyb.Pin('A1'))
        self.ctr = pyb.ADC(pyb.Pin('C4'))
        self.charge_monitor = pyb.ADC(pyb.Pin('A3'))
        self.lut = {4093: [0,0,0], 3654:[0,0,1], 3155:[0,1,0], 2885:[0,1,1], 2645:[1,0,0], 2454:[1,0,1],2218:[1,1,0], 2084:[1,1,1], 1800: [0,0,0] }
        
    def search(self, measured):
        min = 100000000
        for num,btns in self.lut.items():
            dist = (num-measured)**2
            if dist < min: 
                min = dist
                btn = btns
        return btn

    def read(self):
            b = self.btns.read()#>>4
            c = self.ctr.read()#>>4
            d = self.charge_monitor.read()
            a1 = self.search(b)  #[L,C, R, BLE]
            a2 = self.search(c)  #[PORTADC, C, ChargeOK]
            a3 = d               #charge value
            return [a1,a2,a3]
        
    def left(self):
        return(self.read()[0][0])
    
    def right(self):
        return(self.read()[0][1])
    def center(self):
        return(self.read()[1][1])
        
    def ble(self):
        return(self.read()[0][2])
    
    def charge_okay(self):
        return(self.read()[1][2])



