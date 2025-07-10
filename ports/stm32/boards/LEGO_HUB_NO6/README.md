LEGO Hub No.6
=============

This board definition is for the LEGO Hub No. 6, a LEGO control unit with a 5x5
LED display, 6 Powered Up ports, speaker, 6-DOF sensor, Bluetooth, external SPI
flash storage, and a rechargeable battery.  The Hub can work without the battery if
it is plugged in to, and powered by, its USB port.  But without the battery the LEDs
and power on the Powered Up ports will not function.

Features that are currently supported:
- standard MicroPython
- machine and bluetooth modules
- filesystem
- USB VCP, MSC and HID

The Hub has a bootloader preinstalled at 0x08000000 (which is 32kiB in size) which
cannot be erased.  This bootloader is entered by holding down the Bluetooth button,
plugging in USB to power it up, then releasing the Bluetooth button after 5 seconds,
at which point the USB DFU device appears.  If the battery is installed then the
Bluetooth button's RGB LED will cycle colours.  When this bootloader is active, the
flash from 0x08008000 and up can be erased and programmed via USB DFU.

The built-in bootloader has some drawbacks: it cannot be entered programmatically,
and it does not keep the Hub powered up when running from battery (which requires
keeping BAT_PWR_EN high).  As such, this board is configured to work with mboot as
a secondary bootloader: mboot is placed at 0x08008000 and the main application
firmware at 0x08010000.  When mboot is installed it can be entered programmatically
via machine.bootloader(), or by holding down the left arrow button when powering
on the Hub and waiting until the display says "B" before releasing the button.

Backing up original Hub firmware
--------------------------------

Before install MicroPython it is advised to backup the original LEGO firmware that
the Hub comes installed with.  To do this, enter the built-in bootloader by holding
down the Bluetooth button for 5 seconds while powering up the Hub via USB (you may
need to take out the battery and disconnect USB to power off the Hub first).  Then
run the following command from the root of this repository:

    $ cd ports/stm32
    $ make BOARD=LEGO_HUB_NO6 backup-hub-firmware

This will create a file called `lego_hub_firmware.dfu`.  Put this file in a safe
location.  To restore it, enter the built-in bootloader again and run:

    $ make BOARD=LEGO_HUB_NO6 restore-hub-firmware

This will restore the original firmware but not the filesystem.  To recreate the
original filesystem the Hub must be updated using the appropriate LEGO PC
application.

Installing MicroPython
----------------------

You first need to build and install mboot, which only needs to be done once.  From
the root of this repository run:

    $ cd ports/stm32/mboot
    $ make BOARD=LEGO_HUB_NO6

Now enter the built-in bootloader by holding down the Bluetooth button for 5
seconds while powering up the Hub via USB (you may need to take out the battery
and disconnect USB to power off the Hub first).  Then run:

    $ make BOARD=LEGO_HUB_NO6 deploy

mboot should now be installed.  Enter mboot by holding down the left arrow
button when powering up the Hub.  The display will cycle the letters: N, S, F, B.
When it gets to "B" release the left arrow and it will start mboot.  The Hub then
blinks the centre button red once per second, and appears as a USB DFU device.

Now build MicroPython (start at the root of this repository):

    $ cd mpy-cross
    $ make
    $ cd ../ports/stm32
    $ make submodules
    $ make BOARD=LEGO_HUB_NO6

And deploy to the Hub (making sure mboot is active, the centre button is blinking
red):

    $ make BOARD=LEGO_HUB_NO6 deploy

If successful, the Hub should now appear as a USB serial and mass storage device.

Using MicroPython on the Hub
----------------------------

Access the MicroPython REPL using mpremote (pip install mpremote), or with any
serial terminal program.

To scan for BLE devices:

    >>> import bluetooth
    >>> ble = bluetooth.BLE()
    >>> ble.irq(lambda *x: print(*x))
    >>> ble.active(1)
    >>> ble.gap_scan(2000, 625, 625)

Use help("modules") to see available built-in modules.

Updating MicroPython from the Hub's filesystem
----------------------------------------------

You can update the MicroPython application firmware using the instructions above
for installing the firmware for the first time.  The Hub also supports updating
the application firmware from within MicroPython itself, using the on-board
filesystem.

To use this feature, build the firmware (see above for details) then gzip it and
copy the resulting file to the Hub (eg using mpremote):

    $ make BOARD=LEGO_HUB_NO6
    $ gzip build-LEGO_HUB_NO6/firmware.dfu
    $ mpremote cp build-LEGO_HUB_NO6/firmware.dfu.gz :

Then get a REPL on the Hub and execute:

    >>> import appupdate
    >>> appupdate.update_app("firmware.dfu.gz")

You can alternatively run this REPL command using mpremote:

    $ mpremote exec --no-follow "import appupdate; appupdate.update_app('firmware.dfu.gz')"

At that point the Hub should restart and the LED on the central button will flash
different colours.  Once the update is complete the LED will stop flashing and the
Hub will appear again as a USB device.  The application firmware is now updated
and you can remove the firmware.dfu.gz file if desired.


Using custom libraries 
----------------------------------------------


## buttons
    import buttons
    btn = buttons.BUTTONS()
    center_button = btn.center() # value of center button 1 when pressed and 0 when not pressed
    left_button = btn.left()
    right_button = btn.right()
    ble_button = btn.ble()
    print(f"Center button:{center_button}, Left button:{left_button}, Right button:{right_button}, Ble button:{ble_button}")





## display
    import display
    dis = display.DISPLAY()
    # matrix_led(LED_COLUMN, LED_ROW, BRIGHTNESS)
    # LED_COLUMN = 0 -4
    # LED_ROW = 0 - 4
    # BRIGHTNESS = 0 - 10
    dis.matrix_led(3,4,10)

    #center(R,G,B)
    # R = 0 - 65535 (Red value)
    # G = 0 - 65535 (Green value)
    # B = 0 - 65535 (Blue value) 
    dis.center(65535, 0, 0)

    # Other LEDs you can control
    # center(R,G,B)
    # center_main(R,G,B)
    # center_sub(R,G,B)
    # ble(R,G,B)
    # battery_led(R,G,B)


## imu

    import imu
    data  = imu.IMU()

    print(data.values()) #returns acceleration in x, y and z directions and gyro data in x, y and z directions.
    # output looks something like (-254, -56, -16165, 135, -184, 83)


## sound
    import sound
    s = sound.SOUND()
    s.play(440,1) # play(frequency, duration) where frequency is the frequency of the sound and duration is the length of the sound

## force
    import force
    f = force.FORCE()
    print(f.touch()) # returns if the force sensor is pressed or not pressed ( 0 OR 1)
    print(f.force()) # returns the floating point value of force with which the sensor is pressed ( 0 - 10.0) 


