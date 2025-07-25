from machine import Pin
from lpf2 import LPF2
from port import PORT
import time
class FORCE():
    def __init__(self, port):
        self.forc = LPF2(PORT(port)) #create an LPF2 object with distance
        self.forc.metaData()
        
    def modes(self):
        for i in range(len(self.forc.modes)):
            print('running in mode ',i,self.forc.modes[i]['name'],self.forc.modes[i]['format'])
        pass
    
    def touch(self):
        if not self.forc.user_mode == 1:
            self.forc.set_mode(1)
        time.sleep(0.1)
        return self.forc.valuex
    
    def force(self):
        if not self.forc.user_mode == 0:
            self.forc.set_mode(0)
        time.sleep(0.1)
        return self.forc.valuex
    
   



