import threading
import logging
import glob
import time

class DS18B20:
    def __init__(self, device_id, interval=10):
        """
        Initialize the DS18B20 temperature sensor.

        :param device_id: The ID of the DS18B20 device (e.g., '28-000008d4b8b3')
        :param interval: The interval in seconds for reading the temperature (default is 10s)
        """
        self.logger = logging.getLogger("DS18B20")
        logging.basicConfig(level=logging.INFO)

        self.interval = interval
        self.running = False
        self.lock = threading.Lock()
        self.temperature = None

        # Look for the device using the provided device ID
        base_dir = '/sys/bus/w1/devices/'
        matches = glob.glob(base_dir + device_id)
        if not matches:
            raise FileNotFoundError(f"DS18B20 device {device_id} not found")

        # Path to the device's file
        self.device_file = matches[0] + '/w1_slave'

        # Create and start the thread
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        """Start the temperature reading thread."""
        if not self.thread.is_alive():
            self.running = True
            self.thread.start()
            self.logger.info("[DS18B20] Thread started.")
        else:
            self.logger.warning("[DS18B20] Thread already running.")

    def stop(self):
        """Stop the temperature reading thread."""
        self.logger.info("[DS18B20] Stopping thread...")
        self.running = False
        self.thread.join()
        self.logger.info("[DS18B20] Thread stopped.")

    def get_temperature(self):
        """Get the most recent temperature reading."""
        with self.lock:
            return self.temperature, "°C"

    def run(self):
        """Run the thread and continuously read temperature from the sensor."""
        while self.running:
            try:
                with open(self.device_file, 'r') as f:
                    lines = f.readlines()

                # Validate CRC (ensure the data is valid)
                if not lines[0].strip().endswith("YES"):
                    raise ValueError("CRC check failed")

                temp_string = lines[1].split('t=')[1]
                temp = float(temp_string) / 1000.0

                # Lock access to the temperature variable for thread safety
                with self.lock:
                    self.temperature = temp

                self.logger.info(f"Ambient temperature: {self.temperature:.2f} °C")

            except FileNotFoundError as e:
                self.logger.error(f"[DS18B20] Device file not found: {e}")
            except ValueError as e:
                self.logger.error(f"[DS18B20] Value error: {e}")
            except Exception as e:
                self.logger.exception(f"[DS18B20] Unexpected exception: {e}")

            time.sleep(self.interval)
