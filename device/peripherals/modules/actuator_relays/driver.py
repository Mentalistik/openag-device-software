# Import standard python modules
import time
import threading
import os

# Import python types
from typing import NamedTuple, Optional, Dict

# Import device utilities
from device.utilities import bitwise, logger
from device.utilities.communication.i2c.main import I2C
from device.utilities.communication.i2c.exceptions import I2CError
from device.utilities.communication.i2c.mux_simulator import MuxSimulator

# Import driver elements
from device.peripherals.modules.actuator_relays import exceptions, simulator

class RelaysDriver:
    """Driver for ArduinoRelays digital to analog converter."""

    CMD_CHANNEL_CTRL = 0x10
    CMD_SAVE_I2C_ADDR = 0x11
    CMD_READ_I2C_ADDR = 0x12
    CMD_READ_FIRMWARE_VER = 0x13

    channel_state = 0

    channel_state_path = "/tmp/channel_state"

    def __init__(self,
        name: str,
        i2c_lock: threading.RLock,
        bus: int,
        address: int,
        mux: Optional[int]=None,
        channel: Optional[int]=None,
        simulate: bool=False,
        mux_simulator: Optional[MuxSimulator]=None,) -> None:
        """Initializes ArduinoRelays."""

        # Initialize logger
        logname = "ArduinoRelays({})".format(name)
        self.logger = logger.Logger(logname, "peripherals")

        # Initialize i2c lock
        self.i2c_lock = i2c_lock

        # Check if simulating
        if simulate:
            self.logger.info("Simulating driver")
            Simulator = ArduinoRelaysSimulator
        else:
            Simulator = None

        # Initialize I2C
        try:
            self.i2c = I2C(
                name="ArduinoRelays-{}".format(name),
                i2c_lock=i2c_lock,
                bus=bus,
                address=address,
                mux=mux,
                channel=channel,
                mux_simulator=mux_simulator,
                PeripheralSimulator=Simulator,)
        except I2CError as e:
            raise exceptions.InitError(logger=self.logger) from e

    def set_high(self, port: int, retry: bool=True, disable_mux: bool=False) -> None:
        """Sets port high."""
        self.logger.debug("Setting port {} high".format(port))

        # Check valid port range
        if port < 0 or port > 4:
            message = "port out of range, must be within 0-3"
            raise exceptions.SetHighError(message=message, logger=self.logger)

        # Lock thread in case we have multiple io expander instances
        with self.i2c_lock:

            try:
                # Read, update and save the current channel state
                self.read_channel_state()
                self.channel_state |= (1 << (port - 1))
                self.write_channel_state()
                # Send set output command
                self.i2c.write(bytes([self.CMD_CHANNEL_CTRL, self.channel_state]), disable_mux=disable_mux)
            except I2CError as e:
                raise exceptions.SetHighError(logger=self.logger) from e

    def set_low(self, port: int, retry: bool=True, disable_mux: bool=False) -> None:
        """Sets port low."""
        self.logger.debug("Setting port {} low".format(port))

        # Check valid port range
        if port < 0 or port > 4:
            message = "port out of range, must be within 0-3"
            raise exceptions.SetLowError(message=message, logger=self.logger)

        # Lock thread in case we have multiple io expander instances
        with self.i2c_lock:
            
            try:
                # Read, update and save the current channel state
                self.read_channel_state()
                self.channel_state &= ~(1 << (port - 1))
                self.write_channel_state()
                # Send set output command
                self.i2c.write(bytes([self.CMD_CHANNEL_CTRL, self.channel_state]), disable_mux=disable_mux)
            except I2CError as e:
                raise exceptions.SetHighError(logger=self.logger) from e
    
    def write_channel_state(self) -> None:
        f = open(self.channel_state_path, 'w')
        f.write(str(self.channel_state))

    def read_channel_state(self) -> None:
        if os.path.exists(self.channel_state_path):
            f = open(self.channel_state_path, 'r')
            read_state_string = f.read()
            if read_state_string == '':
                self.channel_state = 0
            else:
                self.channel_state = int(read_state_string)
        else:
            self.write_channel_state();