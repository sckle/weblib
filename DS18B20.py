import threading
import logging
import glob
import time

class DS18B20:
    def __init__(self, device_id, on_data=None, delay=0):
        self.logger = logging.getLogger("DS18B20")
        logging.basicConfig(level=logging.INFO)

        time.sleep(delay)
        self.running = False
        self.thread = threading.Thread(target=self.run, daemon=True)
        # Optional callback for post-processing
        self.on_data = on_data

        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + device_id)[0]
        self.device_file = device_folder + '/w1_slave'
        self.start()

    def start(self):
        if not self.thread.is_alive():
            self.running = True
            self.thread.start()
            self.logger.info("[DS18B20] Thread started.")
        else:
            self.logger.warning("[DS18B20] Thread already running.")

    def stop(self):
        self.logger.info("[DS18B20] Stopping thread...")
        self.running = False
        self.thread.join()
        self.logger.info("[DS18B20] Thread stopped.")

    def run(self):
        while self.running:
            try:
                with open(self.device_file, 'r') as f:
                    lines = f.readlines()
                temp_string = lines[1].split('t=')[1]
                temperature = float(temp_string) / 1000.0
                print(f"Ambient temperature: {temperature:.2f} °C")

                if self.on_data:
                    self.on_data(temperature, "°C")

            except Exception as e:
                if self.log_exceptions:
                    self.logger.exception(f"[SmartShunt] Unexpected exception: {e}")

            time.sleep(10)
