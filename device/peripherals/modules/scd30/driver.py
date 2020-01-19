# Import standard python modules
import time, threading, struct, datetime

# Import python types
from typing import NamedTuple, Optional, Tuple

# Import device utilities
from device.utilities import logger, bitwise
from device.utilities.communication.i2c.main import I2C
from device.utilities.communication.i2c.exceptions import I2CError
from device.utilities.communication.i2c.mux_simulator import MuxSimulator

# Import driver elements
from device.peripherals.modules.scd30 import simulator, exceptions


class UserRegister(NamedTuple):
    """Dataclass for parsed user register byte."""

    resolution: int
    end_of_battery: bool
    heater_enabled: bool
    reload_disabled: bool


class SCD30Driver:
    """Driver for scd30 temperature and humidity sensor."""

    # Initialize variable properties
    min_temperature = -40  # celcius
    max_temperature = 125  # celcius
    min_humidity = 0  # %RH
    max_humidity = 100  # %RH
    min_co2 = 0  # ppm
    max_co2 = 5000  # ppm

    cachedSensorData = None
    lastReadSensorData = None

    def __init__(
        self,
        name: str,
        i2c_lock: threading.RLock,
        bus: int,
        address: int,
        mux: Optional[int] = None,
        channel: Optional[int] = None,
        simulate: Optional[bool] = False,
        mux_simulator: Optional[MuxSimulator] = None,
    ) -> None:
        """Initializes driver."""

        # Initialize logger
        logname = "Driver({})".format(name)
        self.logger = logger.Logger(logname, "peripherals")

        # Check if simulating
        if simulate:
            self.logger.info("Simulating driver")
            Simulator = simulator.SCD30Simulator
        else:
            Simulator = None

        # Initialize I2C
        try:
            self.i2c = I2C(
                name=name,
                i2c_lock=i2c_lock,
                bus=bus,
                address=address,
                mux=mux,
                channel=channel,
                mux_simulator=mux_simulator,
                PeripheralSimulator=Simulator,
                verify_device=False,  # need to write before device responds to read
            )
            #self.read_user_register(retry=True)

        except I2CError as e:
            raise exceptions.InitError(logger=self.logger) from e

    def read_sensor_data(self, retry: bool = True) -> bytes:
        """ Reads temperature value."""

        secondsUntilReadingData = 2

        # Don't read data if it was read few seconds ago
        if self.lastReadSensorData is not None and (datetime.datetime.now() - self.lastReadSensorData).total_seconds() < secondsUntilReadingData:
            return self.cachedSensorData

        # Commands
        TRIGGER_MEASUREMENT_COMMAND = [0x00, 0x10, 0x00, 0x00, 0x81]
        GET_READY_STATE_COMMAND = [0x02, 0x02]
        READ_SENSOR_DATA_COMMAND = [0x03, 0x00]

        # Trigger continuous measurement
        try:
            self.i2c.write(bytes(TRIGGER_MEASUREMENT_COMMAND), retry=retry)
        except I2CError as e:
            raise exceptions.TriggerSensorMeasurementError(logger=self.logger) from e

        # Wait for ready status
        while True:
            try:
                self.i2c.write(bytes(GET_READY_STATE_COMMAND), retry=retry)
            except I2CError as e:
                raise exceptions.ReadReadyStateError(logger=self.logger) from e

            try:
                data = self.i2c.read(3)
            except I2CError as e:
                raise exceptions.ReadReadyStateError(logger=self.logger) from e

            if data is False:
                time.sleep(0.1)
                continue

            if data[1] == 1:  # data ready
                break
            time.sleep(0.1)

        # Read sensor data
        try:
            self.i2c.write(bytes(READ_SENSOR_DATA_COMMAND), retry=retry)
            sensorData = self.i2c.read(18)
        except I2CError as e:
            raise exceptions.ReadSensorDataError(logger=self.logger) from e

        self.lastReadSensorData = datetime.datetime.now()
        self.cachedSensorData = sensorData
        return sensorData

    def read_temperature(self, retry: bool = True) -> Optional[float]:
        """ Reads temperature value."""
        self.logger.debug("Reading temperature")

        sensorData = self.read_sensor_data(retry=True)

        # Convert raw data to readable temperature value
        struct_T = struct.pack('>BBBB', sensorData[6], sensorData[7], sensorData[9], sensorData[10])
        temperature, = struct.unpack('>f', struct_T)

        # Verify temperature value within valid range
        if temperature > self.min_temperature and temperature < self.min_temperature:
            self.logger.warning("Temperature outside of valid range")
            return None

        # Successfully read temperature
        self.logger.debug("Temperature: {} C".format(temperature))
        return temperature

    def read_humidity(self, retry: bool = True) -> Optional[float]:
        """Reads humidity value."""
        self.logger.debug("Reading humidity")

        sensorData = self.read_sensor_data(retry=True)

        # Convert raw data to readable humidity value
        struct_rH = struct.pack('>BBBB', sensorData[12], sensorData[13], sensorData[15], sensorData[16])
        humidity, = struct.unpack('>f', struct_rH)

        # Verify humidity value within valid range
        if humidity > self.min_humidity and humidity < self.min_humidity:
            self.logger.warning("Humidity outside of valid range")
            return None

        # Successfully read humidity
        self.logger.debug("Humidity: {} %".format(humidity))
        return humidity

    def read_co2(self, retry: bool = True) -> Optional[float]:
        """Reads co2 value."""
        self.logger.debug("Reading co2")

        sensorData = self.read_sensor_data(retry=True)

        # Convert raw data to readable co2 value
        struct_co2 = struct.pack('>BBBB', sensorData[0], sensorData[1], sensorData[3], sensorData[4])
        co2, = struct.unpack('>f', struct_co2)

        # Verify co2 value within valid range
        if co2 > self.min_humidity and co2 < self.min_humidity:
            self.logger.warning("Humidity outside of valid range")
            return None

        # Successfully read co2
        self.logger.debug("CO2: {} ppm".format(co2))
        return co2

    # def read_user_register(self, retry: bool = True) -> UserRegister:
    #     """ Reads user register."""
    #     self.logger.debug("Reading user register")
    #
    #     # Read register
    #     try:
    #         byte = self.i2c.read_register(0xE7, retry=retry)
    #     except I2CError as e:
    #         raise exceptions.ReadUserRegisterError(logger=self.logger) from e
    #
    #     # Parse register content
    #     resolution_msb = bitwise.get_bit_from_byte(bit=7, byte=byte)
    #     resolution_lsb = bitwise.get_bit_from_byte(bit=0, byte=byte)
    #     user_register = UserRegister(
    #         resolution=resolution_msb << 1 + resolution_lsb,
    #         end_of_battery=bool(bitwise.get_bit_from_byte(bit=6, byte=byte)),
    #         heater_enabled=bool(bitwise.get_bit_from_byte(bit=2, byte=byte)),
    #         reload_disabled=bool(bitwise.get_bit_from_byte(bit=1, byte=byte)),
    #     )
    #
    #     # Successfully read user register
    #     self.logger.debug("User register: {}".format(user_register))
    #     return user_register

    # def reset(self, retry: bool = True) -> None:
    #     """Initiates soft reset."""
    #
    #     SOFT_RESET_COMMAND = [0x02, 0x02]
    #
    #     self.logger.info("Initiating soft reset")
    #
    #     # Send reset command
    #     try:
    #         self.i2c.write(bytes(SOFT_RESET_COMMAND), retry=retry)
    #     except I2CError as e:
    #         raise exceptions.ResetError(logger=self.logger) from e
