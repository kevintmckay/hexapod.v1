# Big Hex Wiring Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BIG HEX SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │   2S LiPo       │                                                       │
│   │   7.4V 3000mAh  │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ▼                                                                │
│   ┌─────────────────┐         ┌─────────────────┐                           │
│   │  Buck Converter │         │   Pi Zero 2W    │◄──── USB (debug)          │
│   │  7.4V → 6V 10A  │────────►│                 │                           │
│   └────────┬────────┘    5V   │   UART TX/RX    │                           │
│            │                  └────────┬────────┘                           │
│            │ 6V                        │                                    │
│            │                           │ TTL Serial (3.3V)                  │
│            │                           │                                    │
│            │              ┌────────────┴────────────┐                       │
│            │              │     Serial Bus Hub      │                       │
│            │              │  (active low for half-  │                       │
│            │              │   duplex if needed)     │                       │
│            │              └────────────┬────────────┘                       │
│            │                           │                                    │
│            │         ┌─────────────────┼─────────────────┐                  │
│            │         │        │        │        │        │                  │
│            ▼         ▼        ▼        ▼        ▼        ▼                  │
│         ┌─────┐   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐               │
│         │ L1  │   │ L2  │  │ L3  │  │ R1  │  │ R2  │  │ R3  │               │
│         │Chain│   │Chain│  │Chain│  │Chain│  │Chain│  │Chain│               │
│         └─────┘   └─────┘  └─────┘  └─────┘  └─────┘  └─────┘               │
│                                                                             │
│   Each chain: 3 servos daisy-chained (coxa → femur → tibia)                 │
│   Total: 18 LX-16A servos                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Leg Daisy-Chain Detail

```
                    From Serial Hub
                          │
                          ▼
              ┌───────────────────────┐
              │     LX-16A #1         │
              │     (COXA)            │
              │   ID: L1=1, L2=4...   │
              │                       │
    6V ──────►│ VIN            VOUT   │──────► to next servo
    GND ─────►│ GND            GND    │──────► to next servo
    SIG ─────►│ SIG            SIG    │──────► to next servo
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     LX-16A #2         │
              │     (FEMUR)           │
              │   ID: L1=2, L2=5...   │
              │                       │
              │ VIN            VOUT   │──────► to next servo
              │ GND            GND    │──────► to next servo
              │ SIG            SIG    │──────► to next servo
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     LX-16A #3         │
              │     (TIBIA)           │
              │   ID: L1=3, L2=6...   │
              │                       │
              │ VIN            VOUT   │ (end of chain)
              │ GND            GND    │
              │ SIG            SIG    │
              └───────────────────────┘
```

## Servo ID Assignment

```
┌─────────────────────────────────────────────────────────────────┐
│                     SERVO ID MAP (Top View)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                           FRONT                                 │
│                             │                                   │
│         L1                  │                  R1               │
│     ┌───────┐               │              ┌───────┐            │
│     │ ID: 1 │ Coxa          │        Coxa │ ID: 10│            │
│     │ ID: 2 │ Femur         │       Femur │ ID: 11│            │
│     │ ID: 3 │ Tibia         │       Tibia │ ID: 12│            │
│     └───────┘               │              └───────┘            │
│                             │                                   │
│         L2                  │                  R2               │
│     ┌───────┐               │              ┌───────┐            │
│     │ ID: 4 │ Coxa     [BODY]        Coxa │ ID: 13│            │
│     │ ID: 5 │ Femur         │       Femur │ ID: 14│            │
│     │ ID: 6 │ Tibia         │       Tibia │ ID: 15│            │
│     └───────┘               │              └───────┘            │
│                             │                                   │
│         L3                  │                  R3               │
│     ┌───────┐               │              ┌───────┐            │
│     │ ID: 7 │ Coxa          │        Coxa │ ID: 16│            │
│     │ ID: 8 │ Femur         │       Femur │ ID: 17│            │
│     │ ID: 9 │ Tibia         │       Tibia │ ID: 18│            │
│     └───────┘               │              └───────┘            │
│                             │                                   │
│                           REAR                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Pi Zero 2W Pinout

```
┌─────────────────────────────────────────┐
│            Pi Zero 2W GPIO              │
├─────────────────────────────────────────┤
│                                         │
│   Pin 1  (3.3V)  ───► Logic level ref   │
│   Pin 2  (5V)    ───► (from BEC)        │
│   Pin 6  (GND)   ───► Common ground     │
│   Pin 8  (TX)    ───► Servo SIG line    │
│   Pin 10 (RX)    ◄─── Servo SIG line    │
│                                         │
│   Note: LX-16A uses half-duplex TTL     │
│   May need TX/RX tied together with     │
│   a resistor or use a buffer IC         │
│                                         │
└─────────────────────────────────────────┘
```

## Half-Duplex Serial Connection

LX-16A uses half-duplex (single wire for TX and RX). Options:

### Option 1: Simple Resistor Method
```
    Pi TX (GPIO 14) ────┬──── 1kΩ ────┬──── Servo SIG
                        │             │
    Pi RX (GPIO 15) ────┘             │
                                      │
                                     ALL SERVOS
                                    (daisy-chained)
```

### Option 2: Tri-State Buffer (74HC126)
```
    Pi TX ────► Buffer ────┐
                          ├──── Servo SIG
    Pi RX ◄─── Buffer ────┘

    Direction pin controlled by GPIO
```

### Option 3: USB-TTL Debug Board
```
    Pi USB ────► LX-16A Debug Board ────► Servo SIG

    Easiest for testing, ~$10
```

## Power Distribution

```
┌─────────────────────────────────────────────────────────────────┐
│                      POWER DISTRIBUTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    2S LiPo (7.4V)                                               │
│         │                                                       │
│         ├────────────► Buck Converter ────► 6V Servo Rail       │
│         │                    │                                  │
│         │                    └────► 5V ────► Pi Zero 2W         │
│         │                                                       │
│         └────────────► Voltage Monitor (optional)               │
│                                                                 │
│    6V Servo Rail                                                │
│         │                                                       │
│         ├──► L1 Chain (3 servos) ──► ~3A peak                   │
│         ├──► L2 Chain (3 servos) ──► ~3A peak                   │
│         ├──► L3 Chain (3 servos) ──► ~3A peak                   │
│         ├──► R1 Chain (3 servos) ──► ~3A peak                   │
│         ├──► R2 Chain (3 servos) ──► ~3A peak                   │
│         └──► R3 Chain (3 servos) ──► ~3A peak                   │
│                                                                 │
│    Total peak: ~18A (all servos stalled - unlikely)             │
│    Typical: ~5A during walking                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Cable Routing

```
                          BODY (Top View)
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │   L1 cable ─┐                         ┌─ R1 cable   │
    │             │    ┌─────────────┐      │             │
    │             │    │   Pi Zero   │      │             │
    │             └───►│             │◄─────┘             │
    │                  │   Battery   │                    │
    │   L2 cable ─────►│     BEC     │◄───── R2 cable    │
    │                  │             │                    │
    │             ┌───►│             │◄─────┐             │
    │             │    └─────────────┘      │             │
    │   L3 cable ─┘                         └─ R3 cable   │
    │                                                     │
    └─────────────────────────────────────────────────────┘

    Each leg cable contains only 3 wires:
    - VIN (6V, 18AWG)
    - GND (18AWG)
    - SIG (22AWG)
```

## Notes

1. **Set servo IDs before assembly** - Use debug board to program each servo with unique ID
2. **Use silicone wire** - More flexible for leg movement
3. **Add ferrite beads** - On signal lines near Pi to reduce noise
4. **Fuse the power** - 20A fuse between battery and system
5. **Voltage monitoring** - LX-16A reports voltage, use for low-battery warning
