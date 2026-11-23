# Autonomous Driving Challenge (ADC)

A removable autonomy kit built on the team's newest car, the prototype that raced at Shell Eco-marathon United States 2026, for Shell Eco-marathon's **Autonomous Driving Challenge**.

| Aspect | Detail |
|---|---|
| Goal | Demo in April 2027, **ADC Poland, June 2027**, and formal participation in 2028 |
| Ambition | Become the first team from the Americas to complete ADC attempts (in 2025 all eight competing teams came from Europe, Turkey and Qatar) |
| Software | ROS 2 stack: state estimation, energy-aware planning and actuation |
| Simulation | Software-in-the-loop scenarios in Gazebo, and a digital twin of the track and car in Gazebo and in NVIDIA Isaac Sim (OpenUSD scene of the track, live from the car's telemetry) |
| Planning | Energy-optimal speed profiles (dynamic programming and genetic algorithms over a longitudinal vehicle model) |
| Hardware | Onboard computer, steering and brake actuators, and a gateway board to the team's own FOC motor driver |

## History

### 2027 · Software stack running in simulation (in progress)

- ROS 2 stack (safety, localization, perception, planning, control) running in software-in-the-loop and on both onboard computers; tests on the car's hardware are pending.
- Digital twin in Gazebo and in NVIDIA Isaac Sim, fed live by the car's one-way telemetry.

The code is private.
