# Motor driver

Controller for the prototype's BLDC motor: it turns the pedal into current and the current into torque, with as little loss as possible.

| Aspect | Detail |
|---|---|
| Platform | Teensy 4.1 (NXP i.MX RT1062, ARM Cortex-M7 at 600 MHz) |
| Software | Teensyduino + FreeRTOS + SimpleFOC, with our own hardware abstraction layer |
| Control | FOC (field-oriented control) with Hall sensors; 10 kHz current loop |
| Power | 48 V three-phase inverter |

## History

### 2027 · Synchronized current sampling and a new motor (in progress)

- Current measurement synchronized with the PWM: the loop went from ≈ 68 µs of compute and ≈ 27 µs of jitter to ≈ 5.4 µs and ≈ 0.6 µs (bench measurement, Nov 2026).
- Sensorless start-up and sensorless observer.
- A new ≈ 500 W motor with chain drive and a clutch (2026: a 350 W hub motor, almost always at full power), run at its most efficient operating point.

### 2026 · Hall-sensor FOC at Indianapolis

- Field-oriented control with Hall sensors on a Teensy 4.1 (ARM Cortex-M7 at 600 MHz), with a throttle-to-current curve, driving a 350 W hub motor ([2026 season](../seasons/2026.md)).

The code is private.
