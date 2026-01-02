"""
MPU6050 IMU Driver for MicroPython (Pi Pico)

Provides accelerometer and gyroscope readings for balance detection.
I2C Address: 0x68 (default) or 0x69 (AD0 high)
"""

import struct
import time

# Registers
PWR_MGMT_1 = 0x6B
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
ACCEL_CONFIG = 0x1C
ACCEL_XOUT_H = 0x3B
TEMP_OUT_H = 0x41
GYRO_XOUT_H = 0x43
WHO_AM_I = 0x75

# Scale factors
ACCEL_SCALE = {0: 16384, 1: 8192, 2: 4096, 3: 2048}  # LSB/g
GYRO_SCALE = {0: 131, 1: 65.5, 2: 32.8, 3: 16.4}     # LSB/(deg/s)


class MPU6050:
    """MPU6050 6-axis IMU driver."""

    def __init__(self, i2c, address=0x68):
        """
        Args:
            i2c: I2C bus instance
            address: I2C address (0x68 default)
        """
        self.i2c = i2c
        self.address = address
        self.accel_scale = ACCEL_SCALE[0]
        self.gyro_scale = GYRO_SCALE[0]

        # Calibration offsets
        self.accel_offset = [0, 0, 0]
        self.gyro_offset = [0, 0, 0]

        self._init_device()

    def _write_byte(self, reg, value):
        """Write single byte to register."""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def _read_byte(self, reg):
        """Read single byte from register."""
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _read_bytes(self, reg, length):
        """Read multiple bytes from register."""
        return self.i2c.readfrom_mem(self.address, reg, length)

    def _init_device(self):
        """Initialize the MPU6050."""
        # Check device ID
        who = self._read_byte(WHO_AM_I)
        if who != 0x68:
            print(f"Warning: MPU6050 WHO_AM_I = 0x{who:02X}, expected 0x68")

        # Wake up (clear sleep bit)
        self._write_byte(PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # Set sample rate divider (1kHz / (1 + 4) = 200Hz)
        self._write_byte(SMPLRT_DIV, 4)

        # Set DLPF (Digital Low Pass Filter) to ~44Hz
        self._write_byte(CONFIG, 3)

        # Set accelerometer range to +/- 2g
        self._write_byte(ACCEL_CONFIG, 0x00)
        self.accel_scale = ACCEL_SCALE[0]

        # Set gyroscope range to +/- 250 deg/s
        self._write_byte(GYRO_CONFIG, 0x00)
        self.gyro_scale = GYRO_SCALE[0]

    def set_accel_range(self, range_g):
        """
        Set accelerometer range.

        Args:
            range_g: 2, 4, 8, or 16 (g)
        """
        ranges = {2: 0, 4: 1, 8: 2, 16: 3}
        if range_g not in ranges:
            raise ValueError("range_g must be 2, 4, 8, or 16")
        idx = ranges[range_g]
        self._write_byte(ACCEL_CONFIG, idx << 3)
        self.accel_scale = ACCEL_SCALE[idx]

    def set_gyro_range(self, range_dps):
        """
        Set gyroscope range.

        Args:
            range_dps: 250, 500, 1000, or 2000 (degrees/second)
        """
        ranges = {250: 0, 500: 1, 1000: 2, 2000: 3}
        if range_dps not in ranges:
            raise ValueError("range_dps must be 250, 500, 1000, or 2000")
        idx = ranges[range_dps]
        self._write_byte(GYRO_CONFIG, idx << 3)
        self.gyro_scale = GYRO_SCALE[idx]

    def read_raw(self):
        """
        Read raw sensor data.

        Returns:
            tuple: (ax, ay, az, gx, gy, gz) raw values
        """
        # Read 14 bytes: accel(6) + temp(2) + gyro(6)
        data = self._read_bytes(ACCEL_XOUT_H, 14)

        # Unpack as big-endian signed shorts
        ax = struct.unpack('>h', data[0:2])[0]
        ay = struct.unpack('>h', data[2:4])[0]
        az = struct.unpack('>h', data[4:6])[0]
        gx = struct.unpack('>h', data[8:10])[0]
        gy = struct.unpack('>h', data[10:12])[0]
        gz = struct.unpack('>h', data[12:14])[0]

        return ax, ay, az, gx, gy, gz

    def read(self):
        """
        Read calibrated sensor data.

        Returns:
            dict with keys:
                accel: (ax, ay, az) in g
                gyro: (gx, gy, gz) in deg/s
        """
        ax, ay, az, gx, gy, gz = self.read_raw()

        # Apply calibration offsets
        ax -= self.accel_offset[0]
        ay -= self.accel_offset[1]
        az -= self.accel_offset[2]
        gx -= self.gyro_offset[0]
        gy -= self.gyro_offset[1]
        gz -= self.gyro_offset[2]

        # Convert to physical units
        return {
            'accel': (
                ax / self.accel_scale,
                ay / self.accel_scale,
                az / self.accel_scale,
            ),
            'gyro': (
                gx / self.gyro_scale,
                gy / self.gyro_scale,
                gz / self.gyro_scale,
            ),
        }

    def read_temperature(self):
        """
        Read temperature in Celsius.

        Returns:
            float: Temperature in degrees C
        """
        data = self._read_bytes(TEMP_OUT_H, 2)
        raw = struct.unpack('>h', data)[0]
        return (raw / 340.0) + 36.53

    def calibrate(self, samples=100, delay_ms=10):
        """
        Calibrate sensor (device must be stationary and level).

        Calculates offset values for accelerometer and gyroscope.
        Assumes Z axis points up (1g reading expected).

        Args:
            samples: Number of samples to average
            delay_ms: Delay between samples in ms
        """
        print("Calibrating MPU6050 (keep device still and level)...")

        accel_sum = [0, 0, 0]
        gyro_sum = [0, 0, 0]

        for _ in range(samples):
            ax, ay, az, gx, gy, gz = self.read_raw()
            accel_sum[0] += ax
            accel_sum[1] += ay
            accel_sum[2] += az
            gyro_sum[0] += gx
            gyro_sum[1] += gy
            gyro_sum[2] += gz
            time.sleep(delay_ms / 1000)

        # Average
        self.accel_offset[0] = accel_sum[0] // samples
        self.accel_offset[1] = accel_sum[1] // samples
        # Z should read 1g, so offset = reading - 1g
        self.accel_offset[2] = (accel_sum[2] // samples) - self.accel_scale

        self.gyro_offset[0] = gyro_sum[0] // samples
        self.gyro_offset[1] = gyro_sum[1] // samples
        self.gyro_offset[2] = gyro_sum[2] // samples

        print(f"Accel offsets: {self.accel_offset}")
        print(f"Gyro offsets: {self.gyro_offset}")

    def get_roll_pitch(self):
        """
        Calculate roll and pitch angles from accelerometer.

        Returns:
            tuple: (roll, pitch) in degrees
        """
        import math

        data = self.read()
        ax, ay, az = data['accel']

        # Roll: rotation around X axis
        roll = math.degrees(math.atan2(ay, az))

        # Pitch: rotation around Y axis
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))

        return roll, pitch
