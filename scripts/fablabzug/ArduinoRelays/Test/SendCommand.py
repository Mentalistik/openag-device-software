# Import standard python modules
import fcntl
import struct
import io
import time
import sys

I2C_SLAVE = 0x04
I2C_BUS = 1

LIGHT = 0x00;
COOLING_FAN = 0x01;
INDOOR_FAN = 0x02;
WATER_PUMP = 0x03;
Relays = [LIGHT, COOLING_FAN, INDOOR_FAN, WATER_PUMP];

def write(bytes_: bytes) -> None:
    fcntl.ioctl(device, 0x0703, int(I2C_SLAVE))
    device.write(bytes_)

# Send command to arduino
selectedRelay = Relays[int(sys.argv[1])]
command = [selectedRelay];

if int(sys.argv[2]) == 1:
    command.append(0x01);
else:
    command.append(0x00);

device_name = "/dev/i2c-{}".format(I2C_BUS)
device = io.open(device_name, "r+b", buffering=0)

write(bytes(command))