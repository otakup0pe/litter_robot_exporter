import os
import time
from prometheus_client import start_http_server, Gauge, Enum
import requests
import asyncio

from pylitterbot import Account
from pylitterbot.robot import EVENT_UPDATE

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    robot_status_values = {
        "BONNET_REMOVED": "Bonnet Removed",
        "CAT_DETECTED": "Cat Detected",
        "CAT_SENSOR_TIMING": "Cat Sensor Timing",
        "CLEAN_CYCLE": "Clean Cycle",
        "EMPTY_CYCLE": "Empty Cycle",
        "CLEAN_CYCLE": "Clean Cycle",
        "READY": "Ready",
        "POWER_DOWN": "Power Down",
        "OFF": "Off",
        "POWER_UP": "Power Up",
        "DRAWER_FULL": "Drawer Full",
    }

    def __init__(self, app_port=80, polling_interval_seconds=5):
        self.app_port = app_port
        self.polling_interval_seconds = polling_interval_seconds
        labels = ["robot_id", "robot_name", "robot_model", "robot_serial_number", "robot_status"]
        self.litter_level = Gauge("robot_litter_level", "Litter level", labels)
        self.waste_drawer_level = Gauge("robot_waste_drawer_level", "Waste drawer level", labels)
        self.is_drawer_full_indicator_triggered = Gauge("robot_is_drawer_full_indicator_triggered", "Drawer full indicator triggered", labels)
        self.is_online = Gauge("robot_is_online", "Is online", labels)
        self.is_sleeping = Gauge("robot_is_sleeping", "Is sleeping", labels)
        self.is_waste_drawer_full = Gauge("robot_is_waste_drawer_full", "Is waste drawer full", labels)
        self.status = Gauge("robot_status", "Robot status", labels)
        self.cycle_count = Gauge("robot_cycle_count", "Cycle count", labels)


    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:

            # Retry if exception occurs
            try:
                asyncio.run(self.fetch())
            except Exception as e:
                print(f"Exception occurred: {e}")
                pass
            time.sleep(self.polling_interval_seconds)

    async def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Create an account.
        account = Account()

        try:
            # Connect to the API and load robots. Source credentials from environment variables.
            username = os.getenv('ROBOT_API_USERNAME')
            password = os.getenv('ROBOT_API_PASSWORD')

            # exit if above env variables are not set
            if not username or not password:
                print("ROBOT_API_USERNAME and ROBOT_API_PASSWORD environment variables must be set")
                return

            await account.connect(username=username, password=password, load_robots=True, subscribe_for_updates=True)

            # Print robots associated with account.
            for robot in account.robots:

                status_label = self.robot_status_values[robot.status.name]

                label_values = [robot.id, robot.name, robot.model, robot.serial, status_label]

                self.litter_level.clear()
                self.waste_drawer_level.clear()
                self.is_drawer_full_indicator_triggered.clear()
                self.is_online.clear()
                self.is_sleeping.clear()
                self.is_waste_drawer_full.clear()
                self.cycle_count.clear()

                # Update Prometheus metrics with application metrics
                self.litter_level.labels(*label_values).set(robot.litter_level)
                self.waste_drawer_level.labels(*label_values).set(robot.waste_drawer_level)
                self.is_drawer_full_indicator_triggered.labels(*label_values).set(int(robot.is_drawer_full_indicator_triggered))    
                self.is_online.labels(*label_values).set(int(robot.is_online))
                self.is_sleeping.labels(*label_values).set(int(robot.is_sleeping))
                self.is_waste_drawer_full.labels(*label_values).set(int(robot.is_waste_drawer_full))
                self.cycle_count.labels(*label_values).set(robot.cycle_count)
                
        finally:
            # Disconnect from the API.
            await account.disconnect()


def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
    app_port = int(os.getenv("APP_PORT", "80"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))

    app_metrics = AppMetrics(
        app_port=app_port,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    print("Listening on port " + str(exporter_port))
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
