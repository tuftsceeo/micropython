# Shared manifest for LEGO_HUB_NO6 & LEGO_HUB_NO7.

include("$(PORT_DIR)/boards/manifest.py")


module("port.py", opt=3)
module("sound.py", opt=3)
module("buttons.py", opt=3)
module("display.py", opt=3)
module("imu.py", opt=3)
module("force.py", opt=3)
module("lpf2.py", opt=3)
module("motor.py", opt=3)
# Modules for application firmware update.
module("fwupdate.py", base_path="$(PORT_DIR)/mboot", opt=3)
module("appupdate.py", opt=3)
