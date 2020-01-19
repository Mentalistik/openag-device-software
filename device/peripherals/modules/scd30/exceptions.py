from device.utilities.exceptions import ExceptionLogger


class DriverError(ExceptionLogger):
    pass


class InitError(DriverError):
    message_base = "Unable to initialize"


class TriggerSensorMeasurementError(DriverError):  # type: ignore
    message_base = "Unable to trigger sensor measurement"


class ReadSensorDataError(DriverError):  # type: ignore
    message_base = "Unable to read sensor data"


class ReadReadyStateError(DriverError):  # type: ignore
    message_base = "Unable to read sensor ready state"


class ReadUserRegisterError(DriverError):  # type: ignore
    message_base = "Unable to read user register"


class ResetError(DriverError):  # type: ignore
    message_base = "Unable to reset"
