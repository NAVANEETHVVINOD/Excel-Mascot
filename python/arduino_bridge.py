import serial
import time
import threading

class ArduinoBridge:
    def __init__(self, port="COM3", baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.connect()

    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"✅ Connected to Arduino on {self.port}")
        except serial.SerialException as e:
            print(f"⚠️ Could not connect to Arduino on {self.port}: {e}")
            self.serial_conn = None

    def send_command(self, command):
        """Sends a command string to the Arduino."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                full_cmd = f"{command}\n"
                self.serial_conn.write(full_cmd.encode('utf-8'))
                # print(f"Sent to Arduino: {command}") # Debug logging
            except Exception as e:
                print(f"❌ Error sending to Arduino: {e}")
                self.connect() # Try to reconnect?
        else:
            # print(f"Arduino not connected. Skipped command: {command}")
            pass

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

if __name__ == "__main__":
    # Test stub
    bridge = ArduinoBridge()
    time.sleep(2)
    bridge.send_command("NORMAL")
    time.sleep(1)
    bridge.send_command("PHOTO")
    bridge.close()
