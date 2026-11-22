# Telemetry

Reads the vehicle's sensors, fuses them, logs them and streams them live to the pits; in the cockpit, the driver sees speed, a map and messages from the team.

| Aspect | 2026 |
|---|---|
| Hardware | ESP32 on our own PCB; ESP32-S3 cockpit display over CAN |
| Sensors | GPS, IMU, Pitot tube, plus voltage, current, rpm and throttle from the driver |
| Fusion | Extended Kalman filter with adaptive trust based on signal quality |
| Link | WiFi → cloud backend → WebSockets → dashboard (data delivery from ≈ 535 ms to < 1 ms in a local benchmark) |
| Analysis | Math channels for driver and vehicle efficiency |

## Work for 2027

- Precision energy measurement on the DC bus, speed on all three wheels, RTK GNSS, air and wind.
- A V2 board and a **predictive co-pilot**: a model trained in simulation that tells the driver when to accelerate and when to coast.

The code is private.
