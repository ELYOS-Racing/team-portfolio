# Luis Xavier García Pimentel Ascencio

| Field | Value |
|---|---|
| GitHub | [luisxavierxd](https://github.com/luisxavierxd) |
| Seasons on the team | 2025–2026 and 2026–2027 |
| Area | Motor control, telemetry, Autonomous Driving Challenge |

## Season 2027 · lead, motor control and Autonomous Driving Challenge

- Lead of the motor driver and of the Autonomous Driving Challenge kit; owner of the team's GitHub organization.
- Implemented PWM-synchronized current sampling in the FOC motor driver (Teensy 4.1): control-loop compute time from ≈ 68 µs to ≈ 5.4 µs and jitter from ≈ 27 µs to ≈ 0.6 µs, measured on the bench.
- Started and built most of the ADC software stack: ROS 2 nodes for estimation, planning and actuation, software-in-the-loop scenarios in Gazebo, a digital twin of the car and track, and energy-optimal speed profiles (optimal control with CasADi and genetic algorithms with pymoo) on the official track geometry.
- Built an energy-strategy and loss-budget pipeline for the Indianapolis attempt that ranks vehicle improvements (rolling resistance, motor efficiency, aerodynamics, mass, electronics) and sized the 2027 motor.
- Reorganized the team's engineering work on GitHub: 13 repositories with continuous integration (firmware builds, KiCad ERC/DRC, secret scanning), a versioned communication protocol shared by every board, release manifests per competition and project management following PMBOK 8.

## Season 2026 · firmware and telemetry

- Developed the firmware of the telemetry board (ESP32): GPS, IMU and Pitot fusion with an extended Kalman filter, microSD logging and the live link to the pits.
- Worked on the FOC motor driver that raced at Shell Eco-marathon United States 2026: 6th place in Prototype Battery Electric, 336 km/kWh.

## Skills

Embedded C/C++ (Teensy 4.1, ESP32, FreeRTOS, PlatformIO), field-oriented motor control, ROS 2, Gazebo, Python (NumPy, pandas, CasADi, pymoo), optimal control, KiCad, GitHub Actions, project management (PMBOK 8).
