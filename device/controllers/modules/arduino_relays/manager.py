# Import standard python modules
import datetime, time
from typing import Optional, Tuple, Dict, Any

# Import controller manager parent class
from device.controllers.classes.controller import manager, modes

class ArduinoRelaysControllerManager(manager.ControllerManager):
    """Manages a controller with Arduino relay logic."""

    cooling_turn_on_time = None;
    cooling_try_minutes = 10;
    cooling_retry_minutes = 120;
    cooling_tolerance = 1;
    cooling_stay_off = False;

    # --------------------------------------------------------------------------------------
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes manager."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        # Initialize variable names
        self.sensor_name: str = self.variables.get("sensor_name", None)
        self.desired_percent_name: str = self.variables.get("desired_percent_name", None)
        self.negative_actuator_name: str = self.variables.get("negative_actuator_name", None)

    # --------------------------------------------------------------------------------------
    # This is the temperature sensor current temp.
    @property
    def sensor_value(self) -> Optional[float]:
        """Gets sensor value."""
        value = self.state.get_environment_reported_sensor_value(self.sensor_name)
        if value != None:
            return float(value)
        return None

    # --------------------------------------------------------------------------------------
    # This is the temperature sensor "set point".
    @property
    def desired_sensor_value(self) -> Optional[float]:
        """Gets desired sensor value."""
        value = self.state.get_environment_desired_sensor_value(self.sensor_name)
        if value != None:
            return float(value)
        return None

    # --------------------------------------------------------------------------------------
    @property
    def desired_percent(self) -> Optional[float]:
        """Gets positive actuator value."""
        value = self.state.get_environment_desired_sensor_value(
            self.desired_percent_name
        )
        if value != None:
            return float(value)
        return None
    
    # --------------------------------------------------------------------------------------
    @property
    def desired_negative_actuator_percent(self) -> Optional[float]:
        """Gets positive actuator value."""
        value = self.state.get_environment_desired_actuator_value(
            self.negative_actuator_name
        )
        if value != None:
            return float(value)
        return None

    # --------------------------------------------------------------------------------------
    @desired_negative_actuator_percent.setter
    def desired_negative_actuator_percent(self, value: float) -> None:
        """Sets reported output value in shared state."""
        self.logger.info(self.negative_actuator_name)
        if self.negative_actuator_name == None:
            return
        self.state.set_environment_desired_actuator_value(
            self.negative_actuator_name, value
        )

    # --------------------------------------------------------------------------------------
    def initialize_controller(self) -> None:
        """Initializes controller."""
        self.logger.info("Initializing")
        self.clear_reported_values()

    # --------------------------------------------------------------------------------------
    def update_controller(self) -> None:
        """Updates controller."""

        if self.sensor_name == None:
            # Actuator is just controlled by the desired value provided by the recipe
            if type(self.desired_percent) != float:
                self.desired_negative_actuator_percent = None
                self.logger.warning("desired_percent is not a float.")
                return

            self.desired_negative_actuator_percent = self.desired_percent

        else:
            # Check sensor values are initialized
            if type(self.sensor_value) != float or type(self.desired_sensor_value) != float:
                self.desired_negative_actuator_percent = None
                self.logger.warning("sensor_value or desired_sensor_value is not a float.")
                return

            if self.cooling_stay_off == True :
                if (datetime.datetime.now() - self.cooling_turn_on_time).total_seconds() / 60 >= self.cooling_retry_minutes :
                    self.cooling_stay_off = False;
                    self.cooling_turn_on_time = None;
                    self.logger.warning("resumed normal operation")
                else:
                    self.logger.warning("still in stay off mode")
                    return;

            # For now just slam between 0 and 100%.
            if self.sensor_value > self.desired_sensor_value + self.cooling_tolerance:
                self.desired_negative_actuator_percent = 100.0

                if self.cooling_turn_on_time == None :
                    self.cooling_turn_on_time = datetime.datetime.now()

            elif self.sensor_value <= self.desired_sensor_value - self.cooling_tolerance:
                self.desired_negative_actuator_percent = 0.0

            if self.desired_negative_actuator_percent == 100.0:
                # If cooling ran for cooling_try_minutes and desired value is still not reached then turn off and stay off for cooling_retry_minutes
                if (datetime.datetime.now() - self.cooling_turn_on_time).total_seconds() / 60 >= self.cooling_try_minutes :
                    self.desired_negative_actuator_percent = 0.0
                    self.cooling_stay_off = True;
                    self.logger.warning(f"paused for {self.cooling_retry_minutes} minutes")

    # --------------------------------------------------------------------------------------
    def clear_reported_values(self) -> None:
        """Clears reported values."""
        self.desired_negative_actuator_percent = None
