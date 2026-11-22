# Electronics

The prototype's own circuit boards: the motor driver that turns battery current into torque and the telemetry board that measures the car. Designed in KiCad, checked automatically on every change and reviewed by a second person before anything is manufactured.

| Aspect | Detail |
|---|---|
| Motor driver board | Teensy 4.1 and a three-phase 48 V inverter with six MOSFETs, inline current sensing (INA240 amplifiers on shunt resistors), Hall sensor and throttle inputs, on a 2-layer board |
| Power stage | 48 V, 45 A; the control loop that protects it runs in a hardware interrupt, never behind logging or messages |
| Telemetry board | ESP32 on our own PCB (2026), with an ESP32-S3 cockpit display over CAN; a V2 board in hat format is in design |
| Design flow | KiCad 10; electrical and design-rule checks on every pull request; every part with a manufacturer part number; releases with gerbers, bill of materials and schematic PDF |
| Interfaces | Pinouts and connectors between boards are agreed in interface control documents before routing |
| Migration | The 2026 driver was moved from Altium to KiCad and verified against the original gerbers: zero design-rule errors, schematic and board matching pin for pin (October 2026) |

## Work for 2027

- **Telemetry V2 board** in hat format: a dedicated UART to the motor driver, a 6-pin GPS header and the new sensors (DC-bus energy over CAN, wheel speed, RTK GNSS, air speed).
- **Gateway board** for the autonomy kit: an opto-isolated UART to the motor driver and USB to the onboard computer.
- **Every milliwatt counts.** Shell's joulemeter measures the electronics too, so each board's consumption is measured and justified: in the team's model, 2 W less of fixed electronics is worth about 3 % more km/kWh.

Design files are private.
