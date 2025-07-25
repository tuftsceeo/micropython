from machine import Pin
from LPF2 import LPF2
from port import PORT
import time
class MOTOR():
    def __init__(self, port):
        self.motor = LPF2(PORT(port)) #create an LPF2 object with motor
        self.motor.metaData()
        self.set_absolute_angle()

    def position(self):
        return self.motor.valuex[0]
    
    def run_at_speed(self, speed):
        if (speed > 0):
            self.motor.ch1.pulse_width_percent(speed)
            self.motor.ch2.pulse_width_percent(0)
        else:
            self.motor.ch1.pulse_width_percent(0)
            self.motor.ch2.pulse_width_percent(abs(speed))
            
    def run_CCW_at_speed(self, speed):
        self.motor.ch1.pulse_width_percent(speed*2)
        self.motor.ch2.pulse_width_percent(0)


    def run_CW_at_speed(self, speed):
        self.motor.ch1.pulse_width_percent(0)
        self.motor.ch2.pulse_width_percent(speed*2)

    def stop_motor(self):
        self.motor.ch1.pulse_width_percent(100)
        self.motor.ch2.pulse_width_percent(100)
        time.sleep(0.1)
        #brake and coast
        #self.motor.ch1.pulse_width_percent(0)
        #self.motor.ch2.pulse_width_percent(0)

    def run_to_absolute_position(self,angle):
        self.set_absolute_angle() #set mode 3
        #finding the shortest path 
        circle_length = 360
        
        
        position = self.position()
        position_error  = position - angle
        
        
        #find shortest path
        if(position_error < -180):
            position_error += circle_length
        elif(position_error > 180):
            position_error -= circle_length
            
        last_error = position_error
        
        while abs(position_error) > 20:
            #coarse positioning
            speed = 50
            if position_error > 0:
                #CW
                self.motor.ch1.pulse_width_percent(100)
                self.motor.ch2.pulse_width_percent(100-speed)

            else:
                #CCW
                self.motor.ch1.pulse_width_percent(100-speed)
                self.motor.ch2.pulse_width_percent(100)

            position = self.position()
            position_error  = position - angle

        self.stop_motor()
        
        position = self.position()
        position_error  = min(10, position - angle) # don't have position error more than 10
        while abs(position_error) > 5: 
            error = 0   
            while (self.position() == position): # run until position changes
                error += position_error
                speed = min(25, int(abs(position_error)*0.4 + 0.8* abs(error))) #speed with P and I with
                #print(speed)
                #speed = 20
                if position_error > 0:
                    #CW
                    self.motor.ch1.pulse_width_percent(100)
                    self.motor.ch2.pulse_width_percent(100-speed)
  
                else:
                    #CCW
                    self.motor.ch1.pulse_width_percent(100-speed)
                    self.motor.ch2.pulse_width_percent(100)

            position = self.position()
            last_error = position_error 
            position_error  = position - angle
            if(position_error < -180):
                position_error += circle_length
            elif(position_error > 180):
                position_error -= circle_length

        self.stop_motor() 
        
        return
 
    
    def set_absolute_angle(self):
        if not self.motor.user_mode == 3:
            self.motor.set_mode(3)
        while not self.motor.valuex: #wait till you can read motor position
            pass

        
        
    def set_relative_angle(self):
        if not self.motor.user_mode == 2:
            self.motor.set_mode(2)
        while not self.motor.valuex: #wait till you can read motor position
            pass




