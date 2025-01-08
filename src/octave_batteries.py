import json
import os
import paho.mqtt.client as paho

from datetime import datetime
from utils.utils import logger

class OctaveBattery:
    def __init__(self, battery_id, capacity, maximum_power, state_of_charge, cycles):
        self.battery_id = battery_id
        self.capacity_kwh = capacity  # kWh
        self.maximum_power_kw = maximum_power  # kW
        self.state_of_charge = min(max(state_of_charge, 0), 100)  # Soc can be in a valid range of 0-100
        self.cycles = cycles
        self.client = self.get_paho_client()

    # Charges with default duration of 1 hour
    def charge(self, power, duration):
        # Charging should be limited to max power
        charging_power = min(power, self.maximum_power_kw)

        # Calculating energy change
        energy_added = charging_power * duration

        # Calculating new SOC
        # Different sized batteries can have different SOC changes wrt same energy added. Therefore it is
        # important to take capacity into account. Example 2 KW energy change for a 10 kwh battery would
        # mean a 20% change in Soc and for a 100 kwh battery it would be 2%.
        new_soc = int(self.state_of_charge + (energy_added / self.capacity_kwh) * 100)

        # Soc should be in valid range of 0 to 100
        self.state_of_charge = min(max(new_soc, 0), 100)
        return self

    def discharge(self, power, duration):
        # Discharging should be limited to max power
        discharging_power = max(power, -self.maximum_power_kw)

        # Calculating energy change
        energy_consumed = discharging_power * duration

        # Before Discharge battery soc
        before_discharge_soc = self.state_of_charge

        # Calculating new SOC
        new_soc = int(self.state_of_charge + (energy_consumed / self.capacity_kwh) * 100)

        # Soc should be in valid range of 0 to 100
        self.state_of_charge = min(max(new_soc, 0), 100)

        # After Discharge battery soc
        after_discharge_soc = self.state_of_charge

        # Update cycle count
        self.cycles += (before_discharge_soc - after_discharge_soc) / 100
        return self

    def get_warning(self):
        if self.state_of_charge > 90:
            return f"Current State of charge is over 90%: {self.state_of_charge}%"
        elif self.state_of_charge < 10:
            return f"Current State of charge is below 10%: {self.state_of_charge}%"
        return None

    def publish_warning(self, warning_type):
        if self.client.is_connected():
            topic = f"/warnings/{self.battery_id}"
            payload = {
                "warning": warning_type,
                "timestamp": datetime.now().isoformat(),
            }
            self.client.publish(topic, json.dumps(payload), qos=1)
        else:
            logger.error(f"Error: MQTT client not connected. Could not publish warning for battery {self.battery_id}")

    def get_paho_client(self):
        USERNAME = os.environ["OCTAVE_USERNAME"]
        PASSWORD = os.environ["OCTAVE_PASSWORD"]
        HOSTNAME = os.environ["OCTAVE_HOSTNAME"]
        PORT = int(os.environ["OCTAVE_PORT"])

        client = paho.Client()
        client.username_pw_set(USERNAME, PASSWORD)

        try:
            client.connect(HOSTNAME, PORT)
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

        return client