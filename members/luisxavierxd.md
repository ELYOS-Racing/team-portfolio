# Luis Xavier García Pimentel Ascencio

| Field | Value |
|---|---|
| GitHub | [luisxavierxd](https://github.com/luisxavierxd) |
| LinkedIn | [luisxaviergpa](https://www.linkedin.com/in/luisxaviergpa/) |
| Seasons on the team | 2026–2027 (joined in August 2026) |
| Area | Motor control, telemetry, Autonomous Driving Challenge |

## Measured results

| Metric | Before | After | Unit |
|---|---|---|---|
| FOC control-loop compute time | 68 | 5.4 | µs |
| FOC control-loop jitter | 27 | 0.6 | µs |
| Team repositories with continuous integration | | 13 | |
| ADC software pipeline (safety, localization, perception, planning, control) running in software-in-the-loop and on both onboard Jetson Orin computers; car hardware tests pending | | Functional | |

## Season 2027 · lead, motor control and Autonomous Driving Challenge

- Lead of the motor driver and of the Autonomous Driving Challenge kit; owner of the team's GitHub organization.
- Implemented PWM-synchronized current sampling in the FOC motor driver (Teensy 4.1): control-loop compute time from ≈ 68 µs to ≈ 5.4 µs and jitter from ≈ 27 µs to ≈ 0.6 µs, measured on the bench.
- Leading the move to sensorless FOC (in progress): selected the rotor-angle observer (Luenberger with PLL, sliding-mode observer as fallback), specified the motor state machine that starts on Hall sensors and hands over to the observer, and added a start-up mode selector with a rollback path to the Hall-only firmware.
- Started and built most of the ADC software stack: ROS 2 nodes for estimation, planning and actuation, software-in-the-loop scenarios in Gazebo, a digital twin of the car and track, and energy-optimal speed profiles (optimal control with CasADi and genetic algorithms with pymoo) on the official track geometry.
- Built an energy-strategy and loss-budget pipeline for the Indianapolis attempt that ranks vehicle improvements (rolling resistance, motor efficiency, aerodynamics, mass, electronics) and sized the 2027 motor.
- Reorganized the team's engineering work on GitHub: 13 repositories with continuous integration (firmware builds, KiCad ERC/DRC, secret scanning), a versioned communication protocol shared by every board, release manifests per competition and project management following PMBOK 8.

## Skills

Embedded C/C++ (Teensy 4.1, ESP32, FreeRTOS, PlatformIO), field-oriented and sensorless motor control (state observers, PLL), ROS 2, Gazebo, Python (NumPy, pandas, CasADi, pymoo), optimal control, KiCad, GitHub Actions, project management (PMBOK 8).
