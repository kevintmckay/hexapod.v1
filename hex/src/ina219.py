"""
INA219 Current/Power Monitor Driver for MicroPython (Pi Pico)

Provides voltage, current, and power measurements for battery monitoring.
Default I2C Address: 0x40 (conflicts with PCA9685, use 0x44 with A0+A1 jumpers)
"""

import struct
import time

# Registers
REG_CONFIG = 0x00
REG_SHUNT_VOLTAGE = 0x01
REG_BUS_VOLTAGE = 0x02
REG_POWER = 0x03
REG_CURRENT = 0x04
REG_CALIBRATION = 0x05

# Configuration bits
CONFIG_RESET = 0x8000
CONFIG_BVOLT_RANGE_32V = 0x2000  # 0-32V range
CONFIG_BVOLT_RANGE_16V = 0x0000  # 0-16V range

# PGA (gain for shunt voltage)
CONFIG_GAIN_1_40MV = 0x0000   # +/- 40mV
CONFIG_GAIN_2_80MV = 0x0800   # +/- 80mV
CONFIG_GAIN_4_160MV = 0x1000  # +/- 160mV
CONFIG_GAIN_8_320MV = 0x1800  # +/- 320mV (default)

# ADC resolution
CONFIG_BADC_12BIT = 0x0180    # 12-bit, 532us
CONFIG_SADC_12BIT = 0x0018    # 12-bit, 532us

# Operating mode
CONFIG_MODE_CONTINUOUS = 0x0007


class INA219:
    """INA219 current/power monitor driver."""

    def __init__(self, i2c, address=0x44, shunt_ohms=0.1, max_amps=3.2):
        """
        Args:
            i2c: I2C bus instance
            address: I2C address (default 0x44 to avoid PCA9685 conflict)
            shunt_ohms: Shunt resistor value in ohms (default 0.1)
            max_amps: Maximum expected current in amps (default 3.2A)
        """
        self.i2c = i2c
        self.address = address
        self.shunt_ohms = shunt_ohms
        self.max_amps = max_amps

        # Calibration values (calculated in configure)
        self.current_lsb = 0
        self.power_lsb = 0
        self.cal_value = 0

        self._init_device()

    def _write_register(self, reg, value):
        """Write 16-bit value to register."""
        data = struct.pack('>H', value)
        self.i2c.writeto_mem(self.address, reg, data)

    def _read_register(self, reg):
        """Read 16-bit value from register."""
        data = self.i2c.readfrom_mem(self.address, reg, 2)
        return struct.unpack('>H', data)[0]

    def _read_register_signed(self, reg):
        """Read 16-bit signed value from register."""
        data = self.i2c.readfrom_mem(self.address, reg, 2)
        return struct.unpack('>h', data)[0]

    def _init_device(self):
        """Initialize and configure the INA219."""
        # Reset
        self._write_register(REG_CONFIG, CONFIG_RESET)
        time.sleep(0.001)

        # Configure for 32V bus voltage range, 320mV shunt range, 12-bit ADC
        config = (CONFIG_BVOLT_RANGE_32V |
                  CONFIG_GAIN_8_320MV |
                  CONFIG_BADC_12BIT |
                  CONFIG_SADC_12BIT |
                  CONFIG_MODE_CONTINUOUS)
        self._write_register(REG_CONFIG, config)

        # Calculate and set calibration
        self._calibrate()

    def _calibrate(self):
        """Calculate calibration value for current measurement."""
        # Current_LSB = Max_Expected_Current / 2^15
        self.current_lsb = self.max_amps / 32768

        # Cal = trunc(0.04096 / (Current_LSB * R_shunt))
        self.cal_value = int(0.04096 / (self.current_lsb * self.shunt_ohms))

        # Power_LSB = 20 * Current_LSB
        self.power_lsb = 20 * self.current_lsb

        # Write calibration value
        self._write_register(REG_CALIBRATION, self.cal_value)

    def read_voltage(self):
        """
        Read bus voltage.

        Returns:
            float: Voltage in volts
        """
        raw = self._read_register(REG_BUS_VOLTAGE)
        # Shift right 3 bits, LSB = 4mV
        return (raw >> 3) * 0.004

    def read_shunt_voltage(self):
        """
        Read shunt voltage (voltage drop across shunt resistor).

        Returns:
            float: Shunt voltage in millivolts
        """
        raw = self._read_register_signed(REG_SHUNT_VOLTAGE)
        # LSB = 10uV
        return raw * 0.01

    def read_current(self):
        """
        Read current.

        Returns:
            float: Current in amps
        """
        raw = self._read_register_signed(REG_CURRENT)
        return raw * self.current_lsb

    def read_power(self):
        """
        Read power.

        Returns:
            float: Power in watts
        """
        raw = self._read_register(REG_POWER)
        return raw * self.power_lsb

    def read_all(self):
        """
        Read all measurements.

        Returns:
            dict with keys: voltage, current, power, shunt_voltage
        """
        return {
            'voltage': self.read_voltage(),
            'current': self.read_current(),
            'power': self.read_power(),
            'shunt_voltage': self.read_shunt_voltage(),
        }

    def is_conversion_ready(self):
        """Check if conversion is complete."""
        raw = self._read_register(REG_BUS_VOLTAGE)
        return bool(raw & 0x02)  # CNVR bit

    def is_overflow(self):
        """Check if math overflow occurred."""
        raw = self._read_register(REG_BUS_VOLTAGE)
        return bool(raw & 0x01)  # OVF bit


class BatteryMonitor:
    """
    High-level battery monitoring using INA219.

    Provides state-of-charge estimation and low battery warnings.
    """

    def __init__(self, ina219, cell_count=3, cell_min_v=3.0, cell_max_v=4.2):
        """
        Args:
            ina219: INA219 driver instance
            cell_count: Number of cells in series (3 for 3S)
            cell_min_v: Minimum cell voltage (fully discharged)
            cell_max_v: Maximum cell voltage (fully charged)
        """
        self.ina = ina219
        self.cell_count = cell_count
        self.min_voltage = cell_min_v * cell_count
        self.max_voltage = cell_max_v * cell_count
        self.warn_voltage = (cell_min_v + 0.2) * cell_count  # 3.2V/cell warning

    def get_voltage(self):
        """Get battery voltage."""
        return self.ina.read_voltage()

    def get_current(self):
        """Get battery current (positive = discharging)."""
        return self.ina.read_current()

    def get_power(self):
        """Get power consumption in watts."""
        return self.ina.read_power()

    def get_soc_percent(self):
        """
        Estimate state of charge percentage.

        Simple linear interpolation based on voltage.
        Not accurate under load - best measured at rest.

        Returns:
            float: Estimated SOC (0-100%)
        """
        voltage = self.get_voltage()
        if voltage >= self.max_voltage:
            return 100.0
        if voltage <= self.min_voltage:
            return 0.0

        return ((voltage - self.min_voltage) /
                (self.max_voltage - self.min_voltage)) * 100

    def is_low_battery(self):
        """Check if battery is low (below warning threshold)."""
        return self.get_voltage() < self.warn_voltage

    def is_critical(self):
        """Check if battery is critically low."""
        return self.get_voltage() < self.min_voltage

    def get_status(self):
        """
        Get battery status summary.

        Returns:
            dict with keys: voltage, current, power, soc_percent, status
        """
        voltage = self.get_voltage()
        current = self.get_current()
        power = self.get_power()
        soc = self.get_soc_percent()

        if voltage < self.min_voltage:
            status = 'critical'
        elif voltage < self.warn_voltage:
            status = 'low'
        else:
            status = 'ok'

        return {
            'voltage': voltage,
            'current': current,
            'power': power,
            'soc_percent': soc,
            'status': status,
        }
