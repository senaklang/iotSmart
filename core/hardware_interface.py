# core/hardware_interface.py
import serial
import time
from threading import Thread, Event, Lock
import serial.tools.list_ports
import logging
from typing import Optional, Dict
from queue import Queue, Empty

class HardwareInterface:
    def __init__(self, port: str = 'COM4', baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

        # sync
        self.stop_event = Event()
        self.connected = Event()
        self.serial_lock = Lock()

        # queue for commands (strings, include newline or not)
        self.command_queue: Queue[str] = Queue()

        # latest sensor data (parsed)
        self.latest_sensor_data: Optional[Dict[str, float]] = None

        # logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # worker thread
        self.worker_thread = Thread(target=self._process_commands, daemon=True)

    def __del__(self):
        self.disconnect_serial()

    # ------------------ Serial connect/disconnect ------------------
    def is_connected(self) -> bool:
        return self.serial is not None and self.serial.is_open

    def get_connection_info(self) -> dict:
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout,
            'connected': self.is_connected()
        }
        
    def connect_serial(self, port: Optional[str] = None) -> bool:
        port = port or self.port
        try:
            available = [p.device for p in serial.tools.list_ports.comports()]
            if port not in available:
                self.logger.warning(f"Requested port {port} not in available ports: {available}")
                return False

            if self.is_connected():
                return True

            self.serial = serial.Serial(port=port, baudrate=self.baudrate, timeout=self.timeout)
            time.sleep(2)  # give Arduino time to reset
            self.connected.set()
            self.stop_event.clear()

            if not self.worker_thread.is_alive():
                self.worker_thread = Thread(target=self._process_commands, daemon=True)
                self.worker_thread.start()

            self.logger.info(f"Connected to serial {port}")
            return True
        except Exception as e:
            self.logger.error(f"connect_serial error: {e}")
            return False

    def disconnect_serial(self):
        self.stop_event.set()
        try:
            if self.is_connected():
                with self.serial_lock:
                    if self.serial:
                        self.serial.close()
                self.connected.clear()
                self.logger.info("Serial disconnected")
            self.serial = None
        except Exception as e:
            self.logger.error(f"disconnect_serial error: {e}")

    # ------------------ Worker: send & receive ------------------
    def _process_commands(self):
        """Thread: take commands from queue, write to serial, and read responses (esp. GET_SENSORS)."""
        self.logger.info("Hardware worker started")
        while not self.stop_event.is_set():
            try:
                cmd = self.command_queue.get(timeout=0.1)
            except Empty:
                continue

            # normalize (ensure newline for device)
            raw = cmd if cmd.endswith("\n") else cmd + "\n"

            if not self.is_connected():
                # Try small retry: put it back and wait
                self.logger.warning("Serial not connected. Requeuing command and waiting.")
                self.command_queue.put(cmd)
                time.sleep(0.5)
                continue

            with self.serial_lock:
                try:
                    # write
                    self.serial.write(raw.encode('utf-8'))  # type: ignore
                    self.logger.debug(f"Sent -> {raw.strip()}")
                    # small gap for Arduino to act
                    time.sleep(0.05)

                    # If this was a GET_SENSORS request, try reading lines for a short time
                    if raw.strip().upper() == "GET_SENSORS":
                        start = time.time()
                        buffer_deadline = 2.0
                        while time.time() - start < buffer_deadline:
                            if self.serial.in_waiting:  # type: ignore
                                line = self.serial.readline().decode('utf-8', errors='ignore').strip()  # type: ignore
                                self.logger.debug(f"RX -> {line}")
                                if line.startswith("Temp:"):
                                    parsed = self._parse_sensor_line(line)
                                    if parsed:
                                        self.latest_sensor_data = parsed
                                        self.logger.info(f"Updated sensor data: {parsed}")
                                        break
                            else:
                                time.sleep(0.05)

                except Exception as e:
                    self.logger.error(f"Worker serial I/O error: {e}")
                    # if serial died, clear and attempt reconnect later
                    try:
                        if self.serial:
                            self.serial.close()
                    except:
                        pass
                    self.serial = None
                    self.connected.clear()
                    # requeue command to try later
                    self.command_queue.put(cmd)
                    time.sleep(1.0)

    def _parse_sensor_line(self, line: str) -> Dict[str, float]:
        """
        Expect line like:
        Temp:30.1°C, Humidity:45.2%, TDS:120ppm, PH:7.2
        """
        try:
            parts = line.replace('°C', '').replace('%', '').replace('ppm', '').split(',')
            data = {}
            for p in parts:
                if ':' in p:
                    k, v = p.split(':', 1)
                    data[k.strip()] = v.strip()
            if all(k in data for k in ['Temp', 'Humidity', 'TDS', 'PH']):
                return {
                    'temperature': float(data['Temp']),
                    'humidity': float(data['Humidity']),
                    'tds': float(data['TDS']),
                    'ph': float(data['PH'])
                }
        except Exception as e:
            self.logger.error(f"parse_sensor_line error: {e}")
        return {}

    # ------------------ Public API ------------------
    def control_lamp(self, device_id: str, action: str, channel: str) -> bool:
        """
        send command to Arduino immediately (if connected) and also push to queue as backup.
        device_id/action/channel example: 'lamp', 'on', '1' -> 'lampon1'
        """
        cmd = f"{device_id}{action}{channel}"
        print(cmd)
        # push to queue first (as backup)
        self.command_queue.put(cmd)

        # attempt immediate send if connected
        if self.is_connected():
            try:
                with self.serial_lock:
                    raw = cmd + "\n"
                    self.serial.write(raw.encode('utf-8'))  # type: ignore
                    self.logger.info(f"Immediate send -> {cmd}")
                return True
            except Exception as e:
                self.logger.warning(f"Immediate send failed, left in queue: {e}")
                # worker thread will handle from queue automatically
                return False
        else:
            self.logger.warning("control_lamp called but serial not connected; queued")
            return False

    def read_sensor_data(self) -> Optional[Dict[str, float]]:
        """
        Request sensor from Arduino (non-blocking). Latest parsed sensor data returned (may be None).
        Use GET_SENSORS to trigger immediate read.
        """
        self.command_queue.put("GET_SENSORS")
        return self.latest_sensor_data

    # Helper: try reconnect (callable from external scheduler)
    def try_reconnect(self):
        if not self.is_connected():
            self.logger.info("Attempting reconnect to serial...")
            self.connect_serial()

"""
hw = HardwareInterface()


print(hw.connect_serial())
if hw.connect_serial():
    print(hw.read_sensor_data())
"""