"""
VL53L0X Time-of-Flight Distance Sensor Driver for MicroPython (Pi Pico)

Provides distance measurements up to 2m using laser time-of-flight.
Default I2C Address: 0x29 (can be changed via software)

Note: Multiple VL53L0X sensors require XSHUT pin control to set unique addresses.
"""

import time

# Registers (subset - VL53L0X has many registers)
SYSRANGE_START = 0x00
SYSTEM_SEQUENCE_CONFIG = 0x01
SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0A
GPIO_HV_MUX_ACTIVE_HIGH = 0x84
SYSTEM_INTERRUPT_CLEAR = 0x0B
RESULT_INTERRUPT_STATUS = 0x13
RESULT_RANGE_STATUS = 0x14
I2C_SLAVE_DEVICE_ADDRESS = 0x8A
IDENTIFICATION_MODEL_ID = 0xC0

# Default address
DEFAULT_ADDRESS = 0x29


class VL53L0X:
    """VL53L0X Time-of-Flight distance sensor driver."""

    def __init__(self, i2c, address=DEFAULT_ADDRESS, xshut_pin=None):
        """
        Args:
            i2c: I2C bus instance
            address: I2C address (0x29 default)
            xshut_pin: Optional Pin object for XSHUT control
        """
        self.i2c = i2c
        self.address = address
        self.xshut = xshut_pin

        # If XSHUT provided, ensure sensor is enabled
        if self.xshut:
            self.xshut.value(1)
            time.sleep(0.01)

        self._init_device()

    def _write_byte(self, reg, value):
        """Write single byte to register."""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def _write_bytes(self, reg, data):
        """Write multiple bytes to register."""
        self.i2c.writeto_mem(self.address, reg, bytes(data))

    def _read_byte(self, reg):
        """Read single byte from register."""
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _read_bytes(self, reg, length):
        """Read multiple bytes from register."""
        return self.i2c.readfrom_mem(self.address, reg, length)

    def _init_device(self):
        """Initialize the VL53L0X with default settings."""
        # Verify device ID
        model_id = self._read_byte(IDENTIFICATION_MODEL_ID)
        if model_id != 0xEE:
            print(f"Warning: VL53L0X model ID = 0x{model_id:02X}, expected 0xEE")

        # Standard initialization sequence (simplified)
        # Full init would include SPAD calibration, ref calibration, etc.
        self._write_byte(0x88, 0x00)
        self._write_byte(0x80, 0x01)
        self._write_byte(0xFF, 0x01)
        self._write_byte(0x00, 0x00)
        self._write_byte(0x00, 0x01)
        self._write_byte(0xFF, 0x00)
        self._write_byte(0x80, 0x00)

        # Configure interrupt
        self._write_byte(SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        gpio_hv = self._read_byte(GPIO_HV_MUX_ACTIVE_HIGH)
        self._write_byte(GPIO_HV_MUX_ACTIVE_HIGH, gpio_hv & ~0x10)
        self._write_byte(SYSTEM_INTERRUPT_CLEAR, 0x01)

        # Set default timing budget (~33ms)
        self._write_byte(SYSTEM_SEQUENCE_CONFIG, 0xFF)

    def set_address(self, new_address):
        """
        Change I2C address.

        Args:
            new_address: New I2C address (0x08-0x77)
        """
        if new_address < 0x08 or new_address > 0x77:
            raise ValueError("Address must be 0x08-0x77")

        self._write_byte(I2C_SLAVE_DEVICE_ADDRESS, new_address & 0x7F)
        self.address = new_address

    def enable(self):
        """Enable sensor via XSHUT pin."""
        if self.xshut:
            self.xshut.value(1)
            time.sleep(0.01)

    def disable(self):
        """Disable sensor via XSHUT pin (saves power)."""
        if self.xshut:
            self.xshut.value(0)

    def read(self, timeout_ms=500):
        """
        Perform single-shot measurement.

        Args:
            timeout_ms: Maximum time to wait for measurement

        Returns:
            int: Distance in mm, or -1 if error/timeout
        """
        # Start measurement
        self._write_byte(0x80, 0x01)
        self._write_byte(0xFF, 0x01)
        self._write_byte(0x00, 0x00)
        self._write_byte(0x00, 0x01)
        self._write_byte(0xFF, 0x00)
        self._write_byte(0x80, 0x00)
        self._write_byte(SYSRANGE_START, 0x01)

        # Wait for start
        start = time.ticks_ms()
        while self._read_byte(SYSRANGE_START) & 0x01:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return -1
            time.sleep(0.001)

        # Wait for measurement complete
        while (self._read_byte(RESULT_INTERRUPT_STATUS) & 0x07) == 0:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return -1
            time.sleep(0.001)

        # Read result
        data = self._read_bytes(RESULT_RANGE_STATUS, 12)
        distance = (data[10] << 8) | data[11]

        # Clear interrupt
        self._write_byte(SYSTEM_INTERRUPT_CLEAR, 0x01)

        # Check for errors (range status)
        range_status = (data[0] & 0x78) >> 3
        if range_status != 0 and range_status != 11:
            # Error conditions (except "no error" and "range valid")
            return -1

        return distance

    def start_continuous(self, period_ms=0):
        """
        Start continuous measurement mode.

        Args:
            period_ms: Measurement period (0 = back-to-back)
        """
        self._write_byte(0x80, 0x01)
        self._write_byte(0xFF, 0x01)
        self._write_byte(0x00, 0x00)
        self._write_byte(0x00, 0x01)
        self._write_byte(0xFF, 0x00)
        self._write_byte(0x80, 0x00)

        if period_ms > 0:
            # Timed mode
            self._write_byte(SYSRANGE_START, 0x04)
        else:
            # Back-to-back mode
            self._write_byte(SYSRANGE_START, 0x02)

    def read_continuous(self):
        """
        Read from continuous measurement mode.

        Returns:
            int: Distance in mm, or -1 if not ready
        """
        if (self._read_byte(RESULT_INTERRUPT_STATUS) & 0x07) == 0:
            return -1

        data = self._read_bytes(RESULT_RANGE_STATUS, 12)
        distance = (data[10] << 8) | data[11]

        self._write_byte(SYSTEM_INTERRUPT_CLEAR, 0x01)
        return distance

    def stop_continuous(self):
        """Stop continuous measurement mode."""
        self._write_byte(SYSRANGE_START, 0x01)
        self._write_byte(0xFF, 0x01)
        self._write_byte(0x00, 0x00)
        self._write_byte(0x00, 0x01)
        self._write_byte(0xFF, 0x00)


class VL53L0XArray:
    """
    Manage multiple VL53L0X sensors with XSHUT pin control.

    Handles address assignment at startup.
    """

    def __init__(self, i2c, xshut_pins, addresses=None):
        """
        Args:
            i2c: I2C bus instance
            xshut_pins: List of Pin objects for XSHUT control
            addresses: List of I2C addresses to assign (default: 0x29, 0x30, 0x31, ...)
        """
        self.i2c = i2c
        self.sensors = []

        if addresses is None:
            addresses = [0x29 + i for i in range(len(xshut_pins))]

        # Disable all sensors
        for pin in xshut_pins:
            pin.value(0)
        time.sleep(0.01)

        # Enable and configure each sensor one at a time
        for i, (pin, addr) in enumerate(zip(xshut_pins, addresses)):
            # Enable this sensor
            pin.value(1)
            time.sleep(0.01)

            # Create sensor at default address
            sensor = VL53L0X(i2c, DEFAULT_ADDRESS, pin)

            # Change to unique address (if not first sensor)
            if addr != DEFAULT_ADDRESS:
                sensor.set_address(addr)

            self.sensors.append(sensor)
            print(f"VL53L0X #{i} configured at 0x{addr:02X}")

    def read_all(self):
        """
        Read all sensors.

        Returns:
            list: Distance readings in mm for each sensor
        """
        return [s.read() for s in self.sensors]

    def __getitem__(self, index):
        """Get sensor by index."""
        return self.sensors[index]

    def __len__(self):
        """Get number of sensors."""
        return len(self.sensors)
