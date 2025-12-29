# Servo Comparison for Large Hexapods

## Quick Comparison

| Servo | Torque | Control | Feedback | Waterproof | Price | 18x Total |
|-------|--------|---------|----------|------------|-------|-----------|
| SG90 | 1.8 kg-cm | PWM | No | No | $2 | $36 |
| MG996R | 11 kg-cm | PWM | No | No | $6 | $108 |
| DS3218 | 25 kg-cm | PWM | No | IP66 | $12 | $216 |
| **LX-16A** | **17 kg-cm** | **Serial** | **Yes** | No | **$15** | **$270** |
| DS3235 | 35 kg-cm | PWM | No | IP66 | $20 | $360 |
| Dynamixel AX-12A | 15 kg-cm | Serial | Yes | No | $45 | $810 |

## Detailed Specs

### Budget: MG996R
```
Torque:     9.4 kg-cm (4.8V) / 11 kg-cm (6V)
Speed:      0.19s/60° (4.8V) / 0.15s/60° (6V)
Voltage:    4.8-6V
Size:       40.7 x 19.7 x 42.9mm
Weight:     55g
Gears:      Metal
Control:    PWM (standard hobby servo)
Feedback:   None
Price:      ~$5-8
```
**Pros:** Cheap, widely available, metal gears
**Cons:** No feedback, needs PCA9685 for control, lower torque

### Mid-Range PWM: DS3218
```
Torque:     21 kg-cm (5V) / 25 kg-cm (6.8V)
Speed:      0.12s/60° (5V) / 0.09s/60° (6.8V)
Voltage:    4.8-6.8V
Size:       40 x 20 x 40.5mm
Weight:     60g
Gears:      Stainless steel
Control:    PWM
Feedback:   None
Waterproof: IP66
Price:      ~$10-15
```
**Pros:** High torque, fast, waterproof, metal gears
**Cons:** No feedback, still needs PWM channels

### Best Value: LX-16A (Recommended)
```
Torque:     17 kg-cm (6V) / 19.5 kg-cm (7.4V)
Speed:      0.18s/60° (adjustable)
Voltage:    6-7.4V
Angle:      0-240° (configurable)
Resolution: 0.24°
Size:       40 x 20 x 40.5mm
Weight:     57g
Gears:      Full metal
Bearings:   Dual ball bearing
Control:    TTL Serial (115200 baud, half-duplex)
Feedback:   Position, temperature, voltage, load
Price:      ~$12-15
```
**Pros:**
- Serial bus = daisy-chain wiring
- Full feedback (position, temp, voltage, load)
- Programmable speed, limits, ID
- 1/3 the cost of Dynamixel
- Great documentation

**Cons:**
- Half-duplex needs simple circuit
- Custom protocol (libraries available)

### High Torque PWM: DS3235
```
Torque:     35 kg-cm (6.8V)
Speed:      0.11s/60°
Voltage:    6-7.4V
Size:       40 x 20 x 40.5mm
Weight:     79g
Gears:      Full metal
Control:    PWM
Feedback:   None
Waterproof: IP66
Price:      ~$18-25
```
**Pros:** Very high torque, fast, waterproof
**Cons:** Heavy, no feedback, expensive for 18

### Premium: Dynamixel AX-12A
```
Torque:     15.3 kg-cm (12V)
Speed:      0.169s/60°
Voltage:    9-12V
Resolution: 0.29°
Size:       32 x 50 x 40mm
Weight:     54.6g
Gears:      Full metal
Control:    TTL Serial (1Mbps)
Feedback:   Position, speed, load, voltage, temp
Price:      ~$45-50
```
**Pros:** Industry standard, excellent software support, proven reliability
**Cons:** 3x the cost of LX-16A, 12V requirement

## Why LX-16A Wins for Hexapods

### 1. Wiring Simplicity
```
PWM (18 servos):
- 2x PCA9685 boards
- 18 individual 3-wire cables
- Complex cable routing

Serial Bus (18 servos):
- 1 UART from Pi
- 6 daisy-chains (one per leg)
- Simple 3-wire per leg
```

### 2. Feedback Enables
- Closed-loop position control
- Stall/collision detection
- Temperature monitoring (prevent burnout)
- Voltage monitoring (low battery warning)
- Load sensing (terrain adaptation)

### 3. Cost Comparison
```
Dynamixel AX-12A × 18 = $810
LX-16A × 18          = $270
Savings              = $540 (66% less!)
```

### 4. Software Support
- Arduino library: github.com/madhephaestus/lx16a-servo
- Python library: github.com/maximkulkin/lewansoul-lx16a
- ROS driver available
- Well-documented protocol

## Torque Requirements

For a large hexapod (~2kg total weight):

| Joint | Load Case | Required Torque | LX-16A (17kg-cm) |
|-------|-----------|-----------------|------------------|
| Coxa | Rotate leg | ~5 kg-cm | OK |
| Femur | Lift body | ~10-12 kg-cm | OK |
| Tibia | Push off | ~8-10 kg-cm | OK |

**Safety margin:** LX-16A provides ~40-60% margin over requirements.

## Alternatives Considered

### Serial Bus Options
| Servo | Torque | Price | Notes |
|-------|--------|-------|-------|
| LX-16A | 17 kg-cm | $15 | Best value |
| LX-224 | 17 kg-cm | $18 | 360° continuous option |
| LX-15D | 15 kg-cm | $12 | Budget serial option |
| Feetech SCS15 | 15 kg-cm | $14 | Similar to LX-16A |
| Dynamixel XL330 | 1.4 kg-cm | $24 | Too weak |
| Dynamixel XL430 | 3.2 Nm | $50 | Expensive |

### Conclusion

**LX-16A is the sweet spot** for DIY large hexapods:
- Enough torque (17 kg-cm)
- Serial bus simplifies wiring
- Feedback enables advanced control
- ~$270 total vs $800+ for Dynamixel
- Good community support
