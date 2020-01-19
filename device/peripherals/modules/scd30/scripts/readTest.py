# Import standard python modules
import fcntl
import struct
import io
import time

I2C_SLAVE = 0x0703
I2C_BUS = 1

TRIGGER_MEASUREMENT_COMMAND = [0x00, 0x10, 0x00, 0x00, 0x81]
GET_READY_STATE_COMMAND = [0x02, 0x02]
READ_SENSOR_DATA_COMMAND = [0x03, 0x00]


def write(bytes_: bytes) -> None:
    fcntl.ioctl(device, int(I2C_SLAVE), int(0x61))
    device.write(bytes_)


def read(num_bytes: int) -> bytes:
    fcntl.ioctl(device, int(I2C_SLAVE), int(0x61))
    return bytes(device.read(num_bytes))


device_name = "/dev/i2c-{}".format(I2C_BUS)
device = io.open(device_name, "r+b", buffering=0)
# Send read temperature command (no-hold master)
write(bytes(TRIGGER_MEASUREMENT_COMMAND))

# Wait for ready status
while True:
    write(bytes(GET_READY_STATE_COMMAND))
    data = read(3)

    if data is False:
        time.sleep(0.1)
        continue

    if data[1] == 1:  # data ready
        break
    time.sleep(0.1)

# Read sensor data
write(bytes(READ_SENSOR_DATA_COMMAND))
sensorData = read(18)
print(sensorData)
device.close()

struct_co2 = struct.pack('>BBBB', sensorData[0], sensorData[1], sensorData[3], sensorData[4])
float_co2, = struct.unpack('>f', struct_co2)
struct_T = struct.pack('>BBBB', sensorData[6], sensorData[7], sensorData[9], sensorData[10])
float_T, = struct.unpack('>f', struct_T)
struct_rH = struct.pack('>BBBB', sensorData[12], sensorData[13], sensorData[15], sensorData[16])
float_rH, = struct.unpack('>f', struct_rH)

if float_co2 > 0.0:
    print("gas_ppm{sensor=\"SCD30\",gas=\"CO2\"} %f" % float_co2)
    print("temperature_degC{sensor=\"SCD30\"} %f" % float_T)
if float_rH > 0.0:
    print("humidity_rel_percent{sensor=\"SCD30\"} %f" % float_rH)
