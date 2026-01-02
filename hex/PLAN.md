# Hexapod Robot Project

## Overview

3DOF hexapod walker using ESP32 controller, mixed servo configuration, and 3D printed frame.

## Specifications

| Spec | Value |
|------|-------|
| Legs | 6 |
| DOF per leg | 3 (coxa, femur, tibia) |
| Total servos | 18 (12× SG90 + 6× MG90S) |
| Gait types | Tripod, wave (recommended), ripple |
| Body size | ~200-250mm across |
| Leg reach | ~130mm from body center |

## Parts Allocation

### Controllers

| Part | Qty | Use | Notes |
|------|-----|-----|-------|
| ESP32 WROOM-32 | 1 | Main controller | Real-time servo control, WiFi/BT |
| Pi Zero 2W | 1 | Vision (optional) | Camera, path planning |

### Servos

| Part | Qty | Use | Notes |
|------|-----|-----|-------|
| SG90 | 12 | Coxa + tibia joints | 1.8 kg-cm, plastic gear |
| MG90S | 6 | Femur joints | 2.2 kg-cm, metal gear |

### Power

| Part | Qty | Use | Notes |
|------|-----|-----|-------|
| 3S Li-Ion (Titan) | 1 | Main power | 11.1V 3.5Ah (runtime) |
| 3S Li-Ion (Glacier) | 1 | Testing | 11.1V 1300mAh (lighter) |
| SoloGood 5V 5A UBEC | 2 | Servo power | One per PCA9685 |

### Electronics

| Part | Qty | Use | Notes |
|------|-----|-----|-------|
| PCA9685 | 2 | PWM drivers | 0x40 and 0x41 |
| MPU6050 | 1 | IMU | Balance/orientation |
| VL53L0X | 3 | ToF distance | Front, left, right |
| INA219 | 1 | Power monitor | Battery voltage/current |
| Pi Camera v1.3 | 1 | Vision | Requires Zero |

### To 3D Print

| Part | Qty | Material | Notes |
|------|-----|----------|-------|
| Body plate (top) | 1 | PLA | Hex shape |
| Body plate (bottom) | 1 | PLA | Electronics mount |
| Coxa bracket | 6 | PLA Light | 15% infill, 2 walls |
| Femur link | 6 | PLA Light | 15% infill, 2 walls |
| Tibia link | 6 | PLA Light | 15% infill, 2 walls |
| Foot tip | 6 | TPU | Flexible for grip |

## Leg Geometry

```
        [BODY]
           |
      +---------+
      |  COXA   |  <- SG90 (horizontal rotation)
      +---------+
           | 25mm
      +---------+
      |  FEMUR  |  <- MG90S (vertical lift) - metal gear for torque
      +---------+
           | 55mm
      +---------+
      |  TIBIA  |  <- SG90 (vertical extend)
      +---------+
           | 75mm
         [FOOT]
```

## Wiring Plan

### Power Distribution

```
3S Li-Ion (11.1V)
    |
    +---> UBEC #1 (5V 5A) ---> PCA9685 #1 (L1-L3, R1) + ESP32
    |
    +---> UBEC #2 (5V 5A) ---> PCA9685 #2 (R2-R3) + Pi Zero [optional]
```

### I2C Bus (ESP32 as Master)

```
ESP32
    |
    +-- GPIO21 (SDA) ----+---- PCA9685 #1 (0x40)
    |                    +---- PCA9685 #2 (0x41)
    +-- GPIO22 (SCL) ----+---- MPU6050 (0x68)
                         +---- VL53L0X x3 (0x29, 0x30, 0x31)
                         +---- INA219 (0x44)
```

### Servo Channel Mapping

| PCA9685 | Ch | Leg | Joint | Servo |
|---------|-----|-----|-------|-------|
| #1 | 0 | L1 | Coxa | SG90 |
| #1 | 1 | L1 | Femur | MG90S |
| #1 | 2 | L1 | Tibia | SG90 |
| #1 | 3 | L2 | Coxa | SG90 |
| #1 | 4 | L2 | Femur | MG90S |
| #1 | 5 | L2 | Tibia | SG90 |
| #1 | 6 | L3 | Coxa | SG90 |
| #1 | 7 | L3 | Femur | MG90S |
| #1 | 8 | L3 | Tibia | SG90 |
| #1 | 9 | R1 | Coxa | SG90 |
| #1 | 10 | R1 | Femur | MG90S |
| #1 | 11 | R1 | Tibia | SG90 |
| #2 | 0 | R2 | Coxa | SG90 |
| #2 | 1 | R2 | Femur | MG90S |
| #2 | 2 | R2 | Tibia | SG90 |
| #2 | 3 | R3 | Coxa | SG90 |
| #2 | 4 | R3 | Femur | MG90S |
| #2 | 5 | R3 | Tibia | SG90 |

### Leg Numbering (top view)

```
     FRONT
  L1       R1
    \     /
     \   /
  L2--[B]--R2
     /   \
    /     \
  L3       R3
     REAR
```

## Software Architecture

### ESP32 (MicroPython) - Real-Time Control

```
hex/src/
├── esp32_main.py    # Main controller loop, UART commands
├── hexapod.py       # Leg kinematics, IK solver
├── gait.py          # Tripod, wave, ripple patterns
├── pca9685.py       # PWM driver
├── mpu6050.py       # IMU driver
├── vl53l0x.py       # Distance sensor driver
├── ina219.py        # Battery monitor
└── calibrate.py     # Servo calibration tool
```

### Pi Zero (Python) - Optional Vision [OPTIONAL]

```
hex/src/
└── zero_main.py     # Camera, path planning, web UI
```

### Default Settings (Optimized for MG90S Femur)

```python
DEFAULT_GAIT = 'wave'       # 5 legs down = less load per leg
DEFAULT_HEIGHT = 40         # Lower stance = less femur torque
DEFAULT_SPEED = 0.8         # Slower = less dynamic load
```

### UART Protocol (ESP32 ↔ Zero)

```
Commands (115200 baud, 8N1):
    W:<dx>,<dy>     Walk in direction (mm)
    T:<angle>       Turn in place (degrees)
    S               Stop
    G:<gait>        Set gait (tripod, wave, ripple)
    H:<height>      Set standing height (mm)
    V:<speed>       Set speed (0.0-1.0)
    C               Center all servos
    B               Boot up sequence
    D               Shut down sequence
    ?               Query status

Responses:
    OK
    OK:<data>
    ERR:<message>
    IMU:<roll>,<pitch>,<yaw>
    DIST:<front>,<left>,<right>
    BAT:<voltage>,<current>,<soc>
```

## Build Phases

### Phase 1: Design and Print
- [x] Design body plates in CAD (OpenSCAD)
- [x] Design leg segments with servo pockets
- [ ] Print test leg (1x) to verify fit
- [ ] Print remaining parts

### Phase 2: Electronics
- [ ] Test PCA9685 with single servo
- [ ] Set second PCA9685 to address 0x41
- [ ] Wire power distribution (dual UBEC)
- [ ] Test all 18 servos individually

### Phase 3: Assembly
- [ ] Mount servos in printed brackets
- [ ] Assemble one leg completely
- [ ] Verify range of motion
- [ ] Assemble remaining legs
- [ ] Mount electronics in body

### Phase 4: Software
- [x] Create ESP32 controller (esp32_main.py)
- [x] Implement smooth gait interpolation
- [ ] Servo calibration (center positions)
- [ ] Single leg IK test
- [ ] Standing pose (all legs)
- [ ] Basic wave gait test

### Phase 5: Refinement
- [ ] Tune gait parameters
- [ ] Battery monitoring alerts
- [ ] Optional: IMU balance correction
- [ ] Optional: Pi Zero camera integration

## Reference Dimensions

| Servo | Size (mm) | Weight | Torque |
|-------|-----------|--------|--------|
| SG90 | 23 × 12 × 29 | 9g | 1.8 kg-cm |
| MG90S | 23 × 12 × 29 | 14g | 2.2 kg-cm |

Link lengths:
- Coxa: 25mm (short, clears body)
- Femur: 55mm
- Tibia: 75mm
- Total reach: ~130mm from body center

## Resources

- Inverse Kinematics: https://oscarliang.com/inverse-kinematics-implementation-hexapod-robots/
- PCA9685 library: adafruit-circuitpython-pca9685
- Gait patterns: https://www.robotshop.com/community/blog/show/hexapod-robot-gait-simulation

---

*Updated: 2026-01-02*
