
from machine import UART, Pin, Timer
import time, struct
import micropython, gc

import ubinascii
import pyb


BYTE_SYNC =     b'\x00'
BYTE_NACK =     b'\x02'
BYTE_ACK =      b'\x04'

#FIRST BYTE

#bits 5-3
LENGTH_1                     = 0x00    # 1 byte           0b000 << 3
LENGTH_2                     = 0x08    # 2 bytes          0b001 << 3
LENGTH_4                     = 0x10    # 4 bytes          0b010 << 3
LENGTH_8                     = 0x18    # 8 bytes          0b011 << 3
LENGTH_16                    = 0x20    # 16 bytes         0b100 << 3
LENGTH_32                    = 0x28    # 32 bytes         0b101 << 3



# MESSAGE_CMD bits 2-0
CMD_TYPE                     = 0x00    # CMD command - TYPE     (device type for VM reference)
CMD_MODES                    = 0x01    # CMD command - MODES    (number of supported modes minus one)
CMD_SPEED                    = 0x02    # CMD command - SPEED    (maximum communication speed)
CMD_SELECT                   = 0x03    # CMD command - SELECT   (select mode)
CMD_WRITE                    = 0x04    # CMD command - WRITE    (write to device)
CMD_EXT_MODE                 = 0x06    # CMD command - EXT_MODE (value will be added to mode in CMD_WRITE_DATA - LPF2 only)
CMD_VERSION                  = 0x07    # CMD command - VERSION  (device firmware and hardware versions)

# MESSAGE_INFO and MESSAGE_DATA bits 2-0
MODE_0                       = 0x00    # MODE 0 (or 8 if INFO_MODE_PLUS_8 bit is set)
MODE_1                       = 0x01    # MODE 1 (or 9 if INFO_MODE_PLUS_8 bit is set)
MODE_2                       = 0x02    # MODE 2 (or 10 if INFO_MODE_PLUS_8 bit is set)
MODE_3                       = 0x03    # MODE 3 (or 11 if INFO_MODE_PLUS_8 bit is set)
MODE_4                       = 0x04    # MODE 4 (or 12 if INFO_MODE_PLUS_8 bit is set)
MODE_5                       = 0x05    # MODE 5 (or 13 if INFO_MODE_PLUS_8 bit is set)
MODE_6                       = 0x06    # MODE 6 (or 14 if INFO_MODE_PLUS_8 bit is set)
MODE_7                       = 0x07    # MODE 7 (or 15 if INFO_MODE_PLUS_8 bit is set)

# CMD_EXT_MODE payload
EXT_MODE_0                   = 0x00    # mode is < 8
EXT_MODE_8                   = 0x08    # mode is >= 8

# SECOND INFO BYTE

INFO_NAME                    = 0x00    # INFO command - NAME    (device name)
INFO_RAW                     = 0x01    # INFO command - RAW     (device RAW value span)
INFO_PCT                     = 0x02    # INFO command - PCT     (device PCT value span)
INFO_SI                      = 0x03    # INFO command - SI      (device SI  value span)
INFO_UNITS                   = 0x04    # INFO command - UNITS   (device SI  unit symbol)
INFO_MAPPING                 = 0x05    # INFO command - MAPPING (input/output value type flags)
INFO_MODE_COMBOS             = 0x06    # INFO command - COMBOS  (mode combinations - LPF2-only)
INFO_UNK7                    = 0x07    # INFO command - unknown (LPF2-only)
INFO_UNK8                    = 0x08    # INFO command - unknown (LPF2-only)
INFO_UNK9                    = 0x09    # INFO command - unknown (LPF2-only)
INFO_UNK10                   = 0x0a    # INFO command - unknown (LPF2-only)
INFO_UNK11                   = 0x0b    # INFO command - unknown (LPF2-only)
INFO_UNK12                   = 0x0c    # INFO command - unknown (LPF2-only)
INFO_MODE_PLUS_8             = 0x20    # Bit flag used in powered up devices to indicate that the mode is 8 + the mode specified in the first byte
INFO_FORMAT                  = 0x80    # INFO command - FORMAT  (device data sets and format)

# INFO_FORMAT formats
DATA8                        = 0x00   # 8-bit signed integer
DATA16                       = 0x01   # 16-bit little-endian signed integer
DATA32                       = 0x02   # 32-bit little-endian signed integer
DATAF                        = 0x03   # 32-bit little-endian IEEE 754 floating point


MSG_SYS =       0x00
MSG_CMD =       0x01
MSG_INFO =      0x02
MSG_DATA =      0x03

CMD_TYPE =      0x00
CMD_MODES =     0x01
CMD_SPEED =     0x02
CMD_SELECT =    0x03
CMD_WRITE =     0x04
CMD_MODESETS =  0x06
CMD_VERSION =   0x07

INFO_NAME =     0x00
INFO_RAW =      0x01
INFO_PCT =      0x02
INFO_SI =       0x03
INFO_SYMBOL =   0x04
INFO_MAPPING =  0x05
INFO_MODECOMB = 0x06
INFO_PLUS_8 =   0x20
INFO_FORMAT =   0x80


class LPF2():
    def __init__(self, port , verbose = False):
        self.verbose = verbose
        self.enable = Pin(port.enable, Pin.OUT)
        self.dig1 = Pin(port.d1, Pin.IN)
        self.dig0 = Pin(port.d0, Pin.OUT)
        self.uart = UART(port.uart)
        
        self.M1 = Pin(port.M1,Pin.OUT)
        self.M2 = Pin(port.M2,Pin.OUT)
        self.lifetime = 0
        self.connected = False
        self.modes = []
        self.user_mode = 0
        self.timer = Timer(mode=Timer.PERIODIC, period=10, callback = self.cb_data)
        
        
        pwm_timer_frequency = 100
        if port.number == 0:
            tim1 = pyb.Timer(1, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(1, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(1, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(2, pyb.Timer.PWM, pin=self.M2)

        elif port.number == 1:
            tim1 = pyb.Timer(1, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(1, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(3, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(4, pyb.Timer.PWM, pin=self.M2)

        elif port.number == 2:
            tim1 = pyb.Timer(4, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(4, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(1, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(2, pyb.Timer.PWM, pin=self.M2)

        elif port.number == 3:
            tim1 = pyb.Timer(4, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(4, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(3, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(4, pyb.Timer.PWM, pin=self.M2)

        elif port.number == 4:
            tim1 = pyb.Timer(8, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(8, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(1, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(2, pyb.Timer.PWM, pin=self.M2)

        elif port.number == 5:
            tim1 = pyb.Timer(3, freq=pwm_timer_frequency)
            tim2 = pyb.Timer(3, freq=pwm_timer_frequency)
            self.ch1 = tim1.channel(3, pyb.Timer.PWM, pin=self.M1)
            self.ch2 = tim2.channel(4, pyb.Timer.PWM, pin=self.M2)


        self.showhex = False
        self.valuex = []


    
    def cb_data(self,p):
        if not self.connected: return
        self.flush()
        self.uart.write(BYTE_NACK)
        self.flush()
        time.sleep(0.01)
        if not self.uart.any():
            return None
        
        new = self.uart.read(self.uart.any())
        #print(new)
        if 0x04 == new[0]:  # done            
            return new
        
        cmd, LLL, CCC = self.params(new[0])
        

        if cmd == MSG_CMD and CCC ==6: # Distance sensor or light sensor
            new= new[3:]
            cmd, LLL, CCC = self.params(new[0])
            
        if cmd == MSG_DATA and CCC == self.user_mode: #make sure the mode of data is the same as the one set by the user
            #print(cmd, LLL, CCC)
            size = LLL + 2 # LLL+cksm, LLL+INFO+cksm # for data we will assume there will be msg + checksum 
            
            try:
                if self.cksm(new):
                    self.decode_new(new,CCC)
                else:
                    pass
            except:
                print('error in data ',new)

            
    def decode_new(self, row,CCC):
        data_sets = self.modes[CCC]['format'][0]
        data_format =  self.modes[CCC]['format'][1]
        data_figures = self.modes[CCC]['format'][2]
        data_decimals = self.modes[CCC]['format'][3]
        
        self.data = row[1:-1]
        frac = int(len(self.data)/data_sets)
        
        hex_value = []
        for i in range(0,len(self.data), frac):
            hex_value.append(self.data[i:i+frac])
    
        
        
        value= []
        if data_format == 0:
            for data in hex_value:
                value.append(struct.unpack('B', data)[0]/(10**data_decimals))
                
        elif data_format == 1:
            for data in hex_value:
                value.append(struct.unpack('<h',data)[0]/(10**data_decimals))
           
        elif data_format == 2:
            for data in hex_value:
                value.append(struct.unpack('<l',data)[0]/(10**data_decimals))
        elif data_format == 3:
            for data in hex_value:
                value.append(struct.unpack('<f',data)[0]/(10**data_decimals))
        else:
            value = []
        self.valuex = value
        return self.valuex

    def close(self):
        self.uart.deinit()
        self.timer = None
        self.connected = False
        self.enable.off()
        if self.verbose:
            print('disconnected')
        time.sleep_ms(500)
        self.flush()
    
    def params(self, datum):
        cmd = datum >> 6
        LLL = 2**((datum & 0b111000) >> 3)
        CCC = datum & 0b111
        return cmd, LLL, CCC
    
    def checksum(self, data):
        cs = 0xFF ^ data[0]
        for g in data[1:]:
            cs = cs ^ g   
        return cs
            
    def cksm(self, data):
        if len(data) == 1:
            return True
        return self.checksum(data[0:-1]) == data[-1]  

    def set_mode(self, mode):
        modeset = [0b1000011] # set mode
        modeset.append(mode)
        modeset.append(self.checksum(modeset))
        string = struct.pack('bbb',*modeset)
        self.uart.write(string)
        self.set_pins(mode)  #seting the power on appropriate pins
        self.user_mode = mode


    def set_pins(self,mode):
        if self.modes[mode]['flags'][0]&0b10000000:
            if self.verbose: print("M2 on")
            self.ch1.pulse_width_percent(0)
            self.ch2.pulse_width_percent(100)
        if self.modes[mode]['flags'][0]&0b01000000:
            if self.verbose: print("M1 on")
            self.ch1.pulse_width_percent(100)
            self.ch2.pulse_width_percent(0)
        if self.modes[mode]['flags'][0]&0b00100000:
            if self.verbose:
                print("Is a motor") 
        if self.modes[mode]['flags'][0]&0b00010000:
            if self.verbose: print("Is Power") 
        if self.modes[mode]['flags'][0]&0b00000100:
            if self.verbose: print("Is position") 
        if self.modes[mode]['flags'][0]&0b00000010:
            if self.verbose: print("Absolute position") 
        if self.modes[mode]['flags'][0]&0b00000001:
            if self.verbose: print("Speed") 
        if self.modes[mode]['flags'][1]&0b01000000:
            if self.verbose: print("Calibration flag") 
        if self.modes[mode]['flags'][4]&0b00000001:
            self.ch1.pulse_width_percent(0)
            self.ch2.pulse_width_percent(0)
            if self.verbose: print("Both on")
            
           
        
    def blackout(self, pin):
        while True:
            found = True
            while True:
                if pin.value() == 0:
                    break
            for x in range(0, 20):
                if pin.value() == 1:
                    found = False
                    break
                time.sleep_ms(10)
            if found:
                return found
                
    def flush(self):
        dump = self.uart.read(self.uart.any())
        
    def readCmd(self):
        if not self.uart.any():
            return None
        new = self.uart.read(1)
        if 0x04 == new[0]:  # done
            return new
        cmd, LLL, CCC = self.params(new[0])
        if cmd == 0:
            return None  # just a sys call
        size = LLL + 3 if cmd == 2 else LLL + 2 # LLL+cksm, LLL+INFO+cksm
        while len(new) < size:  
            n = self.uart.read(1)
            if n: new += n
        if self.cksm(new):
            return new
        return []


        
    def message(self, mode, message):
        data = [0b11000110] # set mode - have to use extended mode
        data.append(mode)   
        data.append(self.checksum(data))
        
        string = struct.pack('bbb',*data)
        self.uart.write(string)


    def update(self, row):
        msg = []
        cmd, LLL, CCC = self.params(row[0])

        if cmd == MSG_CMD: #0x01 
            if CCC == CMD_TYPE: # 000
                self.type = row[1]                    
                payload = 'TYPE = %d (x%x)'% (self.type, self.type)
                
            elif CCC == CMD_MODES: #001                
                if(LLL ==1):
                    self.modes_views = (row[1])
                if (LLL ==2):
                    self.modes_views = (row[1], row[2] if row[2] else row[1])
                elif(LLL ==4):
                    self.modes_views = (row[3], row[4] if row[4] else row[3])
                    
                self.modes = [{'i':i, 'name':'', 'flags':''} for i in range(1+self.modes_views[0])]      
                payload = 'MODES = %d modes, %d in view'% self.modes_views
                
            elif CCC == CMD_SPEED:
                self.speed =  struct.unpack('I',row[1:-1])[0]
                payload = 'SPEED = %d' % self.speed
            elif CCC == CMD_MODESETS:
                self.mode =  struct.unpack('B',row[1:-1])[0]
                payload = 'MODESET = %d' % self.mode
            elif CCC == CMD_VERSION:
                self.version = (struct.unpack('>l',row[1:5])[0]/1000,struct.unpack('>l',row[5:9])[0]/1000)
                payload = 'VERSION = hardware %f software %f' % self.version
            else:
                payload = 'CMD NOT PARSED YET'
                self.unknown.append({'id':'CMD NOT PARSED YET','row':row})
           
        
        elif cmd == MSG_INFO:  
            MMM = 8+CCC if row[1]&0x20 else CCC
            CCC = row[1]&0b111  
            if row[1] == 0x80: #this is format
                self.modes[MMM]['format'] = (row[2],row[3],row[4],row[5])
                payload = 'FORMAT = # datasets %d, format %d, figures %d, decimals %d' % self.modes[MMM]['format']
                time.sleep_ms(10)
                  
            elif row[1] == 0x9 or row[1] == 0x8 or row[1] ==0xa0: 
                self.modes[MMM]['unknown'] = [hex(h) for h in row]
                payload = 'no clue'
                
            elif CCC == INFO_NAME:
                self.name = row[2:-1]
                try:
                    if b'\x00' in self.name[0:6]:
                        self.modes[MMM]['name'] = (self.name[0:6].decode().rstrip('\x00'))
                        self.modes[MMM]['flags'] = (self.name[6:12])

                        
                except:
                    print("error")
                    self.modes[MMM]['name']=(self.name)
                    
                payload = 'NAME = %s' % (self.modes[MMM]['name']) 
            elif CCC == INFO_RAW:
                self.modes[MMM]['raw'] = (struct.unpack('f',row[2:6])[0],struct.unpack('f',row[6:10])[0])
                payload = 'RAW = min %f max %f' % self.modes[MMM]['raw']
                
                
            elif CCC == INFO_PCT:
                self.modes[MMM]['pct'] = (struct.unpack('f',row[2:6])[0],struct.unpack('f',row[6:10])[0])
                payload = 'PCT = min %f max %f' % self.modes[MMM]['pct']
                
                
            elif CCC == INFO_SI:
                self.modes[MMM]['si'] = (struct.unpack('f',row[2:6])[0],struct.unpack('f',row[6:10])[0])
                payload = 'SI = min %f max %f' % self.modes[MMM]['si']
                
                
            elif CCC == INFO_SYMBOL:
                self.modes[MMM]['symbol'] = (row[2:-1].decode().rstrip('\x00'))
                payload = 'SYMBOL = %s' % self.modes[MMM]['symbol']
                
                
            elif CCC == INFO_MAPPING:
                self.modes[MMM]['mapping'] = (row[2],row[3])
                payload = 'MAPPING = input %d, output %d'% self.modes[MMM]['mapping']
            else:
                payload = 'INFO NOT PARSED'
                self.unknown.append({'id':'INFO NOT PARSED','row':row})
        elif cmd == MSG_DATA:
            payload = self.decode_new(row, CCC)
            

        else:
            payload = 'added to unknowns'
            self.unknown.append({'id':'Other Type','row':row})

        return cmd, payload
                                    
    def metaData(self, debug=False):
        if self.verbose: print('starting..', end='')
            
        self.data = None
        self.mode = 0
        self.uart.init(baudrate = 2400, timeout = 1000)
        
        self.flush()
        self.enable.on()
        self.dig0.on()
        self.blackout(self.dig1)
        self.enable.off()
        if self.verbose: print('connected',end='')        
        gc.collect()
        self.header = []
        self.unknown = []
        while True:
            payload = self.readCmd()
            if not payload: 
                time.sleep_ms(0)
                continue
            if payload == -1:
                return False
            if 0x04 == payload[0]: #break when there is ACK
                break
            self.header.append(payload)
            if self.verbose: print('.', end='')

    
        for row in self.header:
            cmd, payload = self.update(row)
            #if self.verbose: print(bin(row[0]),self.cksm(row),CTRL_LUT[cmd],payload)
        
        self.uart.write(BYTE_ACK)
        self.uart.deinit()
        self.uart.init(baudrate = 115200, timeout = 200) 
        self.connected = True
        #print("user mode", self.user_mode)
        #self.set_mode(self.user_mode)
        return True