# Telemetry

Reads the vehicle's sensors, fuses them, logs them and streams them live to the pits; in the cockpit, the driver sees speed, a map and messages from the team.

| Aspect | 2026 |
|---|---|
| Hardware | ESP32 on our own PCB; ESP32-S3 cockpit display over CAN |
| Sensors | GPS, IMU, Pitot tube, plus voltage, current, rpm and throttle from the driver |
| Fusion | Extended Kalman filter with adaptive trust based on signal quality |
| Link | WiFi → cloud backend → WebSockets → dashboard (data delivery from ≈ 535 ms to < 1 ms in a local benchmark) |
| Analysis | Math channels for driver and vehicle efficiency |

## History

### 2027 · New sensors, V2 board and a co-pilot (in progress)

- Precision energy measurement on the DC bus, speed on all three wheels, RTK GNSS, air and wind.
- A V2 board and a **predictive co-pilot**: a model trained in simulation that tells the driver when to accelerate and when to coast.

### 2026 · Own ESP32 board and live link to the pits

- ESP32 board of our own design with GPS, IMU, Pitot tube and data from the motor driver; extended Kalman filter with adaptive trust; microSD logging; live link WiFi → backend → WebSockets → dashboard; cockpit display with map, target speed and pit messages ([2026 season](../seasons/2026.md)).
- Post-race analysis: math channels for driver efficiency, vehicle performance and losses.

The code is private.
