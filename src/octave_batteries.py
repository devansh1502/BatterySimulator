import json
import os
from datetime import datetime

import paho.mqtt.client as paho

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
        charging_power = min(power, self.maximum_power_kw) # Charging should be limited to max power
        energy_added = charging_power * duration # Calculating energy change

        # Calculating new SOC
        # Different sized batteries can have different SOC changes wrt same energy added. It is
        # important to take cap into account. Example: 2 KW energy change for a 10 kwh battery would
        # mean a 20% change in Soc and for a 100 kwh battery it would be 2%.
        new_soc = int(self.state_of_charge + (energy_added / self.capacity_kwh) * 100)

        self.state_of_charge = min(max(new_soc, 0), 100) # Soc should be in valid range of 0 to 100
        return self

    def discharge(self, power, duration):
        # Discharging should be limited to max power
        discharging_power = max(power, -self.maximum_power_kw)
        energy_consumed = discharging_power * duration

        before_discharge_soc = self.state_of_charge  # Before Discharge battery soc

        new_soc = int(self.state_of_charge + (energy_consumed / self.capacity_kwh) * 100)
        self.state_of_charge = min(max(new_soc, 0), 100)

        after_discharge_soc = self.state_of_charge  # After Discharge battery soc

        self.cycles += (before_discharge_soc - after_discharge_soc) / 100 #Updating Cycle count
        return self

    def check_warning(self):
        warning = ""
        if self.state_of_charge > 90:
            warning = f"Current State of charge is over 90%: {self.state_of_charge}%"
        elif self.state_of_charge < 10:
            warning = f"Current State of charge is below 10%: {self.state_of_charge}%"

        print("warning", warning)
        if (
            self.client is not None
            and self.client.is_connected()
            and warning is not None
        ):
            topic = f"/warnings/{self.battery_id}"
            payload = {
                "warning": warning,
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
            err = client.connect(HOSTNAME, PORT)
            if err is None:
                return client
            logger.error(f"Error connecting to MQTT broker: {err}")
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
