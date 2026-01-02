# Hexapod Wiring Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DUAL CONTROLLER ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐    UART    ┌─────────────────────┐               │
│   │    Pi Zero 2W       │◄──────────►│     Pi Pico W       │               │
│   │   (High-Level)      │            │   (Real-Time)       │               │
│   │                     │            │                     │               │
│   │  • WiFi / Web UI    │  Commands  │  • Servo Control    │               │
│   │  • OpenCV / Camera  │  ───────►  │  • Gait Engine      │               │
│   │  • Path Planning    │            │  • IMU Processing   │               │
│   │  • Remote Control   │  Status    │  • I2C Bus Master   │               │
│   │                     │  ◄───────  │                     │               │
│   └─────────────────────┘            └─────────────────────┘               │
│            │                                   │                            │
│        [Camera]                          [I2C Bus]                          │
│                                               │                             │
│                          ┌────────────────────┼────────────────────┐        │
│                          │                    │                    │        │
│                    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐  │
│                    │  MPU6050  │        │ PCA9685x2 │        │  Sensors  │  │
│                    │   (IMU)   │        │  (Servos) │        │ VL53/INA  │  │
│                    └───────────┘        └───────────┘        └───────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Physical Layout (Top View)

```
                          FRONT
                            │
              L1 ─────────────────────── R1
             ╱ ╲           │           ╱ ╲
           Coxa            │         Coxa
            │              │           │
          Femur            │         Femur
            │              │           │
          Tibia            │         Tibia
            │              │           │
          [foot]           │        [foot]
                           │
    L2 ──────────────── [BODY] ──────────────── R2
   ╱ ╲                     │                   ╱ ╲
 Coxa                      │                 Coxa
  │                        │                   │
Femur                      │                 Femur
  │                        │                   │
Tibia                      │                 Tibia
  │                        │                   │
[foot]                     │                [foot]
                           │
              L3 ─────────────────────── R3
             ╱ ╲           │           ╱ ╲
           Coxa            │         Coxa
            │              │           │
          Femur            │         Femur
            │              │           │
          Tibia            │         Tibia
            │              │           │
          [foot]           │        [foot]
                           │
                         REAR
```

## Leg Assembly Detail

```
                BODY PLATE
                    │
    ┌───────────────┴───────────────┐
    │                               │
    │  ┌─────────────────────────┐  │
    │  │      SG90 / HS-82MG     │  │  ← Coxa servo (horizontal rotation)
    │  │      [COXA SERVO]       │  │
    │  └──────────┬──────────────┘  │
    │             │ 25mm             │
    └─────────────┼─────────────────┘
                  │
         ┌────────┴────────┐
         │    HS-82MG      │  ← Femur servo (vertical lift) - use metal gear
         │  [FEMUR SERVO]  │
         └────────┬────────┘
                  │
                  │ 55mm
                  │
         ┌────────┴────────┐
         │      SG90       │  ← Tibia servo (vertical extend)
         │  [TIBIA SERVO]  │
         └────────┬────────┘
                  │
                  │ 75mm
                  │
                  ▼
              [FOOT TIP]
               (TPU)
```

## Power Distribution

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                        3S Li-Ion Battery                        │
    │                     11.1V  3.5Ah  (Titan)                       │
    └───────────────────────────┬─────────────────────────────────────┘
                                │
                          (+)   │   (-)
                           │    │    │
                           ▼    │    ▼
                    ┌──────────────────────┐
                    │  Turnigy PLUSH 60A   │
                    │     ESC (as BEC)     │
                    │    IN: 11.1V         │
                    │    OUT: 5V 3A        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┬────────────────┐
              │                │                │                │
              ▼                ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
    │   PCA9685 #1    │ │  Pi Pico W  │ │ Pi Zero 2W  │ │   PCA9685 #2    │
    │   V+ = 5V       │ │   VSYS=5V   │ │   5V pin    │ │   V+ = 5V       │
    │   (addr 0x40)   │ │             │ │             │ │   (addr 0x41)   │
    └─────────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘
```

## UART Connection (Pico ↔ Zero)

```
    ┌─────────────────────────────┐      ┌─────────────────────────────┐
    │        Pi Zero 2W           │      │         Pi Pico W           │
    │                             │      │                             │
    │   GPIO 14 (TXD) ────────────┼──────┼──► GPIO 1 (UART0 RX)        │
    │                             │      │                             │
    │   GPIO 15 (RXD) ◄───────────┼──────┼─── GPIO 0 (UART0 TX)        │
    │                             │      │                             │
    │   GND ──────────────────────┼──────┼─── GND                      │
    │                             │      │                             │
    └─────────────────────────────┘      └─────────────────────────────┘

    Protocol: 115200 baud, 8N1

    Commands (Zero → Pico):
      "W:100,0\n"     Walk forward 100mm
      "T:45\n"        Turn 45 degrees
      "S\n"           Stop
      "G:tripod\n"    Set gait to tripod
      "H:50\n"        Set height to 50mm

    Status (Pico → Zero):
      "OK\n"
      "IMU:roll,pitch,yaw\n"
      "ERR:message\n"
```

## I2C Bus (Pico as Master)

```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                           Pi Pico W                                 │
    │                                                                     │
    │   3.3V ─────┬────────────────────────────────────────────────────   │
    │             │                                                       │
    │   GND  ─────┼───┬────────────────────────────────────────────────   │
    │             │   │                                                   │
    │   GP4  ─────┼───┼───┬────────────────────────────────────────────   │ (I2C0 SDA)
    │             │   │   │                                               │
    │   GP5  ─────┼───┼───┼───┬────────────────────────────────────────   │ (I2C0 SCL)
    │             │   │   │   │                                           │
    └─────────────┼───┼───┼───┼───────────────────────────────────────────┘
                  │   │   │   │
    ┌─────────────┴───┴───┴───┴─────────┐
    │           I2C Bus                  │
    │    (directly connect all below)    │
    └──┬──────────┬──────────┬──────────┬──────────┬──────────┬───────────┘
       │          │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼          ▼
   ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐
   │MPU6050│  │PCA9685│  │PCA9685│  │VL53L0X│  │VL53L0X│  │VL53L0X│
   │ 0x68  │  │ 0x40  │  │ 0x41  │  │ 0x29* │  │ 0x30* │  │ 0x31* │
   │ (IMU) │  │ (#1)  │  │ (#2)  │  │(front)│  │(left) │  │(right)│
   └───────┘  └───────┘  └───────┘  └───────┘  └───────┘  └───────┘

   * VL53L0X default address is 0x29. Use XSHUT pins to set unique addresses.
```

## VL53L0X Address Configuration

```
    Pi Pico W
    ┌─────────────────────┐
    │ GP6  ───────────────┼──► VL53L0X #1 XSHUT (front)  → addr 0x29
    │ GP7  ───────────────┼──► VL53L0X #2 XSHUT (left)   → addr 0x30
    │ GP8  ───────────────┼──► VL53L0X #3 XSHUT (right)  → addr 0x31
    └─────────────────────┘

    Boot sequence:
    1. Hold all XSHUT low (sensors off)
    2. Release XSHUT #1, set address to 0x29
    3. Release XSHUT #2, set address to 0x30
    4. Release XSHUT #3, set address to 0x31
```

## INA219 Battery Monitor

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                       INA219 (addr 0x40*)                       │
    │                                                                 │
    │   VIN- ◄─── Battery (-)                                         │
    │   VIN+ ◄─── Battery (+) ───► To ESC/BEC                         │
    │                                                                 │
    │   VCC  ◄─── 3.3V (from Pico)                                    │
    │   GND  ◄─── GND                                                 │
    │   SDA  ◄─── I2C SDA                                             │
    │   SCL  ◄─── I2C SCL                                             │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘

    * Default 0x40 conflicts with PCA9685 #1. Solder A0 jumper → 0x41
      But that conflicts with PCA9685 #2. Use A0+A1 → 0x44 or 0x45
```

## Camera Connection (Zero Only)

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                        Pi Zero 2W                               │
    │                                                                 │
    │   ┌─────────────────┐                                           │
    │   │  CSI Connector  │◄─── Pi Zero Camera Cable (narrow end)     │
    │   │   (22-pin)      │                                           │
    │   └─────────────────┘                                           │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
                                      │
                                      │ (15cm cable)
                                      │
    ┌─────────────────────────────────┴───────────────────────────────┐
    │                     Pi Camera v1.3                              │
    │                   ┌─────────────────┐                           │
    │                   │  CSI Connector  │◄─── Standard end of cable │
    │                   │   (15-pin)      │                           │
    │                   └─────────────────┘                           │
    │                        OV5647                                   │
    │                         5MP                                     │
    └─────────────────────────────────────────────────────────────────┘

    Note: Pi Zero uses narrower 22-pin connector, need special cable!
```

## Servo Channel Mapping

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                        PCA9685 #1 (0x40)                        │
    ├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────┤
    │  CH 0   │  CH 1   │  CH 2   │  CH 3   │  CH 4   │  CH 5   │ ... │
    │ L1 Coxa │L1 Femur │L1 Tibia │ L2 Coxa │L2 Femur │L2 Tibia │     │
    │  SG90   │ HS-82MG │  SG90   │  SG90   │ HS-82MG │  SG90   │     │
    └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴─────┘
         │         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼         ▼
       ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐
       │L1 │     │L1 │     │L1 │     │L2 │     │L2 │     │L2 │
       │hip│     │thigh    │calf│     │hip│     │thigh    │calf│
       └───┘     └───┘     └───┘     └───┘     └───┘     └───┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                   PCA9685 #1 (0x40) continued                   │
    ├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────┤
    │  CH 6   │  CH 7   │  CH 8   │  CH 9   │  CH 10  │  CH 11  │ ... │
    │ L3 Coxa │L3 Femur │L3 Tibia │ R1 Coxa │R1 Femur │R1 Tibia │     │
    │  SG90   │ HS-82MG │  SG90   │  SG90   │ HS-82MG │  SG90   │     │
    └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴─────┘
         │         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼         ▼
       ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐
       │L3 │     │L3 │     │L3 │     │R1 │     │R1 │     │R1 │
       │hip│     │thigh    │calf│     │hip│     │thigh    │calf│
       └───┘     └───┘     └───┘     └───┘     └───┘     └───┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                        PCA9685 #2 (0x41)                        │
    ├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────┤
    │  CH 0   │  CH 1   │  CH 2   │  CH 3   │  CH 4   │  CH 5   │     │
    │ R2 Coxa │R2 Femur │R2 Tibia │ R3 Coxa │R3 Femur │R3 Tibia │     │
    │  SG90   │ HS-82MG │  SG90   │  SG90   │ HS-82MG │  SG90   │     │
    └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬────┴─────┘
         │         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼         ▼
       ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐
       │R2 │     │R2 │     │R2 │     │R3 │     │R3 │     │R3 │
       │hip│     │thigh    │calf│     │hip│     │thigh    │calf│
       └───┘     └───┘     └───┘     └───┘     └───┘     └───┘

    Servo mix: 12x SG90 (coxa, tibia) + 6x HS-82MG (femur - high torque)
```

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HEXAPOD SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                           │
│   │   BATTERY   │                                                           │
│   │  3S 11.1V   │                                                           │
│   │  (Titan)    │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                  │
│          ├────────────────────────────────────────────┐                     │
│          │                                            │                     │
│          ▼                                            ▼                     │
│   ┌─────────────┐                              ┌─────────────┐              │
│   │  INA219     │                              │ PLUSH 60A   │              │
│   │  (monitor)  │                              │  ESC/BEC    │              │
│   └─────────────┘                              └──────┬──────┘              │
│                                                       │ 5V 3A               │
│              ┌────────────────────────────────────────┼──────────┐          │
│              │                    │                   │          │          │
│              ▼                    ▼                   ▼          ▼          │
│       ┌─────────────┐      ┌─────────────┐     ┌──────────┐ ┌──────────┐    │
│       │ Pi Zero 2W  │ UART │  Pi Pico W  │     │ PCA9685  │ │ PCA9685  │    │
│       │             │◄────►│             │     │   #1     │ │   #2     │    │
│       │  • WiFi     │      │  • Servos   │     │  0x40    │ │  0x41    │    │
│       │  • Camera   │      │  • IMU      │     └────┬─────┘ └────┬─────┘    │
│       │  • Planning │      │  • Sensors  │          │            │          │
│       └──────┬──────┘      └──────┬──────┘          │            │          │
│              │                    │                 │            │          │
│         [Camera]            [I2C Bus]               │            │          │
│         Pi v1.3                   │                 │            │          │
│                    ┌──────────────┼─────────┐       │            │          │
│                    │              │         │       │            │          │
│                    ▼              ▼         ▼       │            │          │
│               ┌────────┐    ┌────────┐ ┌────────┐   │            │          │
│               │MPU6050 │    │VL53L0X │ │VL53L0X │   │            │          │
│               │  IMU   │    │  x3    │ │  ...   │   │            │          │
│               └────────┘    └────────┘ └────────┘   │            │          │
│                                                     │            │          │
│    ┌────────────────────────────────────────────────┴────────────┘          │
│    │         │         │         │         │         │                      │
│    ▼         ▼         ▼         ▼         ▼         ▼                      │
│  ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐                    │
│  │L1 │     │L2 │     │L3 │     │R1 │     │R2 │     │R3 │                    │
│  │3x │     │3x │     │3x │     │3x │     │3x │     │3x │                    │
│  └───┘     └───┘     └───┘     └───┘     └───┘     └───┘                    │
│                                                                             │
│  Servos: 12x SG90 + 6x HS-82MG (femur joints)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pin Summary

### Pi Pico W
| GPIO | Function | Connected To |
|------|----------|--------------|
| GP0 | UART0 TX | Zero GPIO 15 (RXD) |
| GP1 | UART0 RX | Zero GPIO 14 (TXD) |
| GP4 | I2C0 SDA | All I2C devices |
| GP5 | I2C0 SCL | All I2C devices |
| GP6 | Digital Out | VL53L0X #1 XSHUT |
| GP7 | Digital Out | VL53L0X #2 XSHUT |
| GP8 | Digital Out | VL53L0X #3 XSHUT |
| VSYS | 5V Power | From BEC |
| GND | Ground | Common |

### Pi Zero 2W
| GPIO | Function | Connected To |
|------|----------|--------------|
| GPIO 14 | UART TXD | Pico GP1 (RX) |
| GPIO 15 | UART RXD | Pico GP0 (TX) |
| CSI | Camera | Pi Camera v1.3 |
| 5V | Power | From BEC |
| GND | Ground | Common |

### I2C Addresses
| Address | Device |
|---------|--------|
| 0x29 | VL53L0X #1 (front) |
| 0x30 | VL53L0X #2 (left) |
| 0x31 | VL53L0X #3 (right) |
| 0x40 | PCA9685 #1 |
| 0x41 | PCA9685 #2 |
| 0x44 | INA219 (A0+A1 soldered) |
| 0x68 | MPU6050 |

## Servo Wire Colors

```
    ┌─────────────────────────────────┐
    │         SERVO CONNECTOR         │
    │                                 │
    │   ┌─────┬─────┬─────┐           │
    │   │ BRN │ RED │ ORG │           │
    │   │ GND │ V+  │ SIG │           │
    │   │     │ 5V  │ PWM │           │
    │   └──┬──┴──┬──┴──┬──┘           │
    │      │     │     │              │
    │      │     │     └───► PCA9685 PWM channel
    │      │     └─────────► PCA9685 V+ (from BEC)
    │      └───────────────► PCA9685 GND
    │                                 │
    └─────────────────────────────────┘
```

## Notes

- Pico handles all real-time control (servos, IMU, sensors)
- Zero handles high-level functions (WiFi, camera, planning)
- UART at 115200 baud for inter-controller communication
- All servos receive 5V power from ESC BEC through PCA9685 V+ terminals
- I2C uses 3.3V logic (Pico GPIO voltage)
- PCA9685 #2 needs A0 address jumper soldered to use 0x41
- INA219 needs A0+A1 jumpers soldered to avoid address conflict (0x44)
- VL53L0X sensors need XSHUT pin sequence to set unique addresses
- Pi Zero camera uses narrower connector - need special cable
- Keep servo wires bundled and routed through body to legs
- Use servo wire extensions (15-20cm) for clean routing
- HS-82MG on femur joints for higher torque under load
