from machine import Pin
class PORT():
    def __init__(self, number):
        p = Pin.cpu

        
        def Port(number, e, rx, tx, u, d0, d1, m1, m2):
            self.number = number
            self.enable = e
            self.RX = rx
            self.TX = tx
            self.uart = u
            self.d0 = d0
            self.d1 = d1
            self.M1 = m1
            self.M2 = m2
        
        if number ==0:
            Port(number, p.A10, p.E7,  p.E8,  7, p.D7,  p.D8,  p.E9,  p.E11)
        elif number ==1:
            Port(number, p.A8,  p.D0,  p.D1,  4, p.D9,  p.D10, p.E13, p.E14)
        elif number ==2:
            Port(number, p.E5,  p.E0,  p.E1,  8, p.D11, p.E4,  p.B6,  p.B7 )
        elif number ==3:
            Port(number, p.B2,  p.D2,  p.C12, 5, p.C15, p.C14, p.B8,  p.B9 )
        elif number ==4:
            Port(number, p.B5,  p.E2,  p.E3, 10, p.C13, p.E12, p.C6,  p.C7 )
        elif number ==5:
            Port(number, p.C5,  p.D14, p.D15, 9, p.C11, p.E6,  p.C8,  p.B1 )
        else:
            print("invalid port")
        

    def pull_up(self):
        self.d0_pin = Pin(self.d0, Pin.IN, Pin.PULL_UP)
        self.d1_pin = Pin(self.d1, Pin.IN, Pin.PULL_UP)
        return self.d0_pin, self.d1_pin




        

